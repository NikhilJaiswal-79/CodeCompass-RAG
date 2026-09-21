# CodeCompass Cloud Architecture: A Journey to Serverless AWS

Building a highly complex Tri-Modal RAG engine is difficult. Deploying it to the public internet while dealing with timeouts, serverless constraints, and asynchronous processing is an entirely different beast.   

This article details the step-by-step AWS Cloud architecture of CodeCompass, how data flows through the system, and a transparent look at the critical architectural mistakes I made (and fixed) along the way.

---

## Core AWS Services Used

Before tracking a request, here are the core AWS services that make up the architecture. Notably, the system is split across **4 distinct Lambda functions** to safely handle asynchronous workloads and bypass strict API timeouts.

*   **Amazon Route 53 & CloudFront:** The DNS and CDN edge layer. Route 53 manages the custom domain (`code-compass.app`) and SSL certificates, while CloudFront securely hosts and globally distributes the static frontend (HTML/CSS/JS) to users at edge locations.
*   **AWS API Gateway:** The backend front door. Routes HTTP requests from the frontend to the correct Lambda function.
*   **Amazon DynamoDB:** A lightning-fast NoSQL database used purely as a cache and state-tracker (e.g., storing whether a repo is `processing` or `completed`).
*   **Amazon S3 (Simple Storage Service):** The massive storage bucket where the generated `faiss.bin`, `bm25.pkl`, and `graph.db` databases are saved for long-term retrieval.
*   **AWS Lambda (The 4 Compute Engines):**
    1.  **RAG-Dispatcher Lambda:** A lightning-fast orchestrator. It instantly checks the DynamoDB cache, triggers the background worker, and returns a 202 Accepted response to the user in under 1 second.
    2.  **RAG-Ingestion-Worker Lambda:** The heavy lifter. It runs completely in the background (allowed up to 15 minutes). It downloads the codebase, runs the Tree-sitter AST, calls the Gemini embedding API, calculates PageRank, compiles BM25, and uploads the final databases to S3.
    3.  **RAG-Status Lambda:** A lightweight polling endpoint. The frontend continuously calls this Lambda, which reads the DynamoDB state and reports whether the background worker is finished.
    4.  **RAG-Chat Lambda:** The conversational engine. It pulls the databases from S3, executes the Tri-Modal RAG search, runs the LangGraph state machine with Claude 3.5 Haiku, and streams the answer back to the user.

---

## The AWS Serverless Flow

The entire backend is 100% serverless, eliminating the need to manage EC2 instances or long-running servers. Here is exactly how a request travels through the system from the moment you click "Index Repo" on the frontend.

### 1. The Entry Point: API Gateway & The Dispatcher
When a user submits a GitHub repository, the frontend sends a `POST` request to `/ingest`. 
This request is intercepted by the **AWS API Gateway** and routed to the **RAG-Dispatcher Lambda**.

The Dispatcher has one job: **Act fast.** 
1. It checks the **DynamoDB** cache. If the repo is already indexed, it stops and tells the user. 
2. It writes an initial "processing" state to DynamoDB.
3. It asynchronously invokes the Heavy Worker Lambda using `InvocationType='Event'`.
4. It instantly returns an HTTP 202 (Accepted) response to the frontend, closing the connection cleanly.

### 2. The Heavy Lifting: The Ingestion Worker
Because the Dispatcher triggered it asynchronously, the **RAG-Ingestion-Worker Lambda** spins up in the background. AWS allows this Lambda to run for up to 15 minutes. 

It clones the repository, runs the Tree-sitter AST parser, generates vectors using the Gemini API, calculates PageRank, and compiles the BM25 dictionary. 
Once finished, it uploads the massive `faiss.bin`, `bm25.pkl`, and `graph.db` databases directly into an **Amazon S3 Bucket**. It then updates DynamoDB to say "Completed".

### 3. The Polling Mechanism: The Status Lambda
While the Worker is churning in the background, the frontend UI is showing a loading spinner. The frontend continuously sends `GET` requests to the `/status` endpoint.
These requests hit the **RAG-Status Lambda**, which simply peeks at the DynamoDB table and reports back to the frontend whether the worker is still "processing" or has "completed".

### 4. The Conversation: The Chat Lambda
Once ingestion is complete, the user asks a question. The request goes to `/chat`, hitting the **RAG-Chat Lambda**.
This Lambda retrieves the databases from S3, fires up the LangGraph Agentic state machine, executes the Tri-Modal search, and streams the reasoning and final answer (using Claude 3.5 Haiku) back through the API Gateway to the user's screen.

---

## Lessons Learned: Critical Mistakes and Architectural Blunders

No system is designed perfectly on the first try. Here are the major architectural mistakes made during development and how we solved them.

### Mistake 1: The 29-Second API Gateway Guillotine
**The Flaw:** Initially, my plan was to use a single Lambda function for `/ingest`. Knowing that the vector generation process was slow, I assumed I could just configure the API Gateway route as "async". My goal was to have this single Lambda "reply early" to the frontend (to beat the Gateway's hard 29-second timeout limit), while it quietly finished cloning the repo and parsing the code in the background.

**The Reality:** This assumption was completely wrong on two fundamental levels:
1.  **API Gateway HTTP APIs cannot do this:** The modern, cheaper "HTTP API" version of API Gateway literally does not have an asynchronous invocation setting. That capability only exists on the older, more expensive "REST API" type.
2.  **Lambdas cannot "reply early":** Even if the Gateway allowed it, a single Lambda function fundamentally cannot reply to a user and then keep working. A Lambda function only returns an HTTP response at the *very end* of its execution, right before it shuts down. It is physically impossible for a single Lambda to send an HTTP response and then continue processing code in the background.

**The Fix (The Asynchronous Rewrite):** I had to completely tear down the architecture and rebuild it using an Asynchronous Dispatcher/Worker pattern. I split the single slow operation into two distinct Lambda functions:
1.  **The Dispatcher (Lightweight):** When `/ingest` is called, the Dispatcher wakes up. Instead of processing the code, it uses the AWS SDK (`boto3`) to trigger the Worker Lambda with the crucial flag `InvocationType='Event'`. This magical flag tells AWS to fire the Worker in the background and immediately release the Dispatcher.
2.  **The Worker:** The Worker spins up independently with a 15-minute timeout allowance, doing the heavy lifting without the API Gateway watching it.
3.  **The Handshake:** Because the Dispatcher is instantly released, it replies to the frontend in under 1 second with an **HTTP 202 (Accepted)**. The frontend then starts a polling loop (`setInterval`), asking a new `/status` endpoint every 3 seconds if the background worker has finished updating the DynamoDB table.

### Mistake 2: Synchronous Chat Timeouts
**The Flaw:** Similar to the ingestion issue, I initially used slower LLMs for the LangGraph Agent. Because the agent dynamically plans, loops, and self-corrects, it often took 40+ seconds to finalize an answer. This hit the same 29-second API Gateway timeout.
**The Fix:** I aggressively optimized the reasoning engine by switching the Agent to **Claude 3.5 Haiku**. Haiku is so blazingly fast that the entire state machine completes its complex loops in under 12 seconds, safely dodging the AWS timeout.

### Mistake 3: The DynamoDB Caching Trap
**The Flaw:** To save compute costs, I implemented a DynamoDB cache. If a `repo_id` was marked "completed", I skipped ingestion. However, when users pushed new commits to their GitHub repos, CodeCompass refused to re-index the fresh code because it assumed the old cache was still valid.
**The Fix:** I had to patch the system by building a explicit **Force Re-Index** checkbox into the UI, wiring it through the frontend `fetch` request, and modifying the Dispatcher to explicitly bypass the DynamoDB cache when flagged.

### Mistake 4: Git History Bloat via PowerShell Encoding
**The Flaw:** During deployment, I created massive `deployment_package.zip` files (60MB+) containing all the Python dependencies. I added `*.zip` to my `.gitignore` file using a PowerShell script. However, PowerShell defaulted to UTF-16 encoding, which Git cannot read. Git ignored the `.gitignore` file and accidentally committed 100MB of useless AWS deployment zip files directly into the GitHub repository, bloating the git history.
**The Fix:** I had to rewrite the `.gitignore` in UTF-8 and execute complex Git commands (`git commit --amend`) to manually strip the bloat out of the repository's history.

### Mistake 5: Naive LLM JSON Parsing
**The Flaw:** I originally asked the Agent to return JSON and used Python's strict `json.loads()` on the output. However, LLMs (even Claude) occasionally wrap their JSON in markdown code blocks (e.g., ` ```json { ... } ``` `) or append conversational text like *"Here is your JSON:"*. This caused the entire pipeline to crash violently.
**The Fix:** I had to build a bulletproof parsing engine that uses regular expressions to hunt for the outermost `{` and `}` brackets, mathematically extracting and repairing malformed JSON from the LLM's raw markdown output before it crashes the app.
