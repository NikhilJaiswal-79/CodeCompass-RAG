# The Anatomy of a Codebase RAG: How CodeCompass Thinks

## What is a RAG and Why Do We Need It?

Large Language Models (LLMs) like ChatGPT or Claude are incredibly smart, but they suffer from two major limitations when dealing with enterprise code:
1. **Lack of Knowledge:** They don't know anything about your private, proprietary codebase.
2. **Context Limits:** You cannot simply copy and paste an entire 100000-line repository into the AI's chat window. It will crash or aggressively forget information because it exceeds the model's memory (context window).

Because of this, if you ask a standard AI, *"How does my custom authentication system work?"*, it will either guess (hallucinate) or simply tell you it doesn't know.

**Retrieval-Augmented Generation (RAG)** solves this. It acts as a highly intelligent search engine for the AI. When you ask a question, the RAG system *Retrieves* the exact, relevant files from your private codebase, hands those files to the AI, and asks the AI to *Generate* an answer based purely on that retrieved code. It gives the AI a perfect, instantaneous memory of your entire project.

### The Problem with Traditional Codebase RAGs
Traditional RAG systems try to build this "search engine" by blindly chopping text files into 500-word chunks and using basic vector similarity to find the right code. But code isn't a novel—it's a highly structured, interconnected web of logic. If you feed an entire repository into a standard RAG, it will likely get confused by chopped-in-half functions and missing context.

To truly understand an unfamiliar codebase, you need an architecture that understands concepts, precise variable names, and architectural dependencies simultaneously. Here is an in-depth breakdown of how the **CodeCompass Tri-Modal RAG Engine** processes and comprehends code behind the scenes to solve this massive problem.

### The Tech Stack & Python Libraries
Before diving into the architecture, here is the exact technology stack that powers CodeCompass:

**Core RAG Engine (Python):**
*   **`langgraph`:** Manages the agentic state machine and autonomous reasoning loops.
*   **`anthropic` (Claude 3.5 Haiku):** The core LLM powering the reasoning engine.
*   **`faiss-cpu`:** Handles the high-dimensional vector similarity search.
*   **`networkx`:** Constructs the dependency graph and executes the PageRank algorithm.
*   **`google-genai` (Gemini):** Generates the 768-dimensional text embeddings.
*   **`tree-sitter` & `tree_sitter_languages`:** Provides the Abstract Syntax Tree (AST) parsing for over 15 languages.
*   **`rank_bm25`:** Powers the TF-IDF exact keyword matching engine.

**Cloud Infrastructure & Frontend:**
*   **AWS:** 100% Serverless backend using Lambda, API Gateway, DynamoDB, and S3.
*   **Frontend:** Vanilla HTML/CSS/JS with `marked.js`, hosted on Amazon CloudFront (CDN) & Route 53 (DNS).

---

### The Evolution: From Vector-Only to Tri-Modal Hybrid
When building CodeCompass, I didn't start with this complex Tri-Modal architecture. Initially, I built a standard **Vector-Only** system (using just FAISS embeddings). It seemed to work fine for basic questions, but when I evaluated it using LangSmith to test its performance on complex codebase queries, the metrics were disappointing. It struggled to find exact variable names and often returned irrelevant helper scripts instead of core architectural files.

Realizing that Vector-Only was fundamentally flawed for codebases, I completely tore down the engine and rebuilt it as a **Hybrid Tri-Modal** system (combining Vectors, BM25 Keyword Search, and PageRank Graph Centrality). 

### How I Evaluated: LLM-as-a-Judge using LangSmith
To prove this scientifically, I used **LangSmith's Evaluation framework** leveraging an **"AI-as-a-Judge"** methodology. I constructed a rigorous dataset of **50 complex questions** based specifically on the open-source `corsair` repository. 

For every single question, I fed the LangSmith AI Judge four specific inputs:
1.  **The User Question** (e.g., *"How does the cache invalidation work?"*)
2.  **The Ground Truth Answer & Documents** (The manually verified correct answer, AND the exact file paths that *should* have been retrieved to answer it)
3.  **The Retrieved Context** (The raw code chunks the database actually found and retrieved)
4.  **The Generated Answer** (The final answer the AI produced based on that retrieved context)

The AI Judge then rigorously graded the system across 6 distinct metrics. Here is exactly what those metrics evaluated:

*   **Accuracy:** Did the final generated answer correctly and fully address the user's question?
*   **Faithfulness:** Was the answer based *strictly* on the retrieved code (proving zero hallucinations)?
*   **MRR@10 (Mean Reciprocal Rank):** How close to the absolute #1 spot was the correct file?
*   **Precision@5:** Out of the top 5 files retrieved, what percentage were actually useful?
*   **Recall@10:** Out of all the files needed to answer the question, did the system find them all?
*   **Relevance:** Was the retrieved code genuinely relevant to the original user intent?

Here is the direct head-to-head comparison proving why the Hybrid approach is mandatory for code:

| Evaluation Metric | Exp #1 (Vector-Only) | Exp #2 (Tri-Modal) | Improvement |
| :--- | :--- | :--- | :--- |
| **Accuracy** | 74% (0.74) | **91% (0.91)** | +17% |
| **Faithfulness** | 76% (0.76) | **94% (0.94)** | +18% |
| **MRR@10** | 81% (0.81) | **97% (0.97)** | +16% |
| **Precision@5** | 62% (0.62) | **71% (0.71)** | +9% |
| **Recall@10** | 74% (0.74) | **95% (0.95)** | +21% |
| **Relevance** | 77% (0.77) | **97% (0.97)** | +20% |

As the metrics prove, the addition of BM25 completely fixed the exact-keyword precision issues, and PageRank solved the relevance issues by boosting core architectural files to the top. Let's look at exactly how this new brain is built.

---

## Phase 1: Ingestion (Building the Brain)

When you ask the system to index a repository, it doesn't just read the text. It surgically dissects it into four distinct "cheat sheets" so the AI can look up information in three entirely different ways.

### 1. The Master List & AST Parsing
Before building any databases, the system uses **Abstract Syntax Trees (AST)** via Tree-sitter. Instead of arbitrarily chopping code every few paragraphs, Tree-sitter parses the actual logic of the language (supporting Python, JS, Go, Rust, Java, etc.). It surgically extracts every single function and class individually. 

The rule is: **1 Chunk = 1 Function/Class.**

The system creates a "Master List" (saved as `chunks.pkl`), assigning an ID to each function. For example:
* **Chunk 0:** `def login_user(request): ...`
* **Chunk 1:** `class DatabaseConnection: ...`

This Master List is the *only* place where the raw, human-readable code is actually stored. The following three databases only store math and pointers pointing back to this list.

### 2. FAISS (The "Vibes" Searcher)
**Goal: Semantic Concept Matching**

FAISS takes the entire body of a function (the signature, the comments, the internal math) and crushes it into a **Vector Embedding**—a mathematical coordinate in a 768-dimensional space. 

If you ask the AI to "find where passwords are saved safely," it doesn't look for those exact English words. It translates that concept into a mathematical coordinate. It then looks at the FAISS grid and finds that a function named `hash_credential_to_db()` is sitting at the exact same mathematical coordinate. FAISS allows the system to understand what a function *does*, even if the developer gave it a terrible, completely unrelated name.

### 3. BM25 (The "Ctrl+F" on Steroids)
**Goal: Exact Keyword Matching**

If you search for the exact variable `retry_timeout_v2`, FAISS might get confused and return `retry_timeout_v1` because their "vibes" are mathematically similar. 

BM25 solves this. It acts as an ultra-powerful dictionary index using an algorithm based on **TF-IDF (Term Frequency - Inverse Document Frequency)**.
* **IDF (Rarity Score):** The system calculates how rare a word is across the entire project. Common words like `def`, `class`, or `return` are given a score of 0. Highly unique words like `stripe_payment_v2` are given massive rarity scores.
* **TF (Term Frequency):** The system counts how many times the rare word appears in a specific file.

By multiplying these together, BM25 instantly zeroes in on the exact file containing specific variables, ignoring all the "useless" common words in your query. BM25 also includes mathematical guardrails (like length normalization) so massive 10,000-line files don't unfairly beat small, highly targeted files.

### 4. SQLite (The Detective's String Board)
**Goal: Architectural Dependency Mapping**

If you ask, *"If I delete the Database class, what breaks?"*, FAISS and BM25 are useless. They only read text *inside* files; they don't know how files interact.

CodeCompass turns the codebase into a mathematical network (a Graph). Using a SQLite database, it explicitly maps out every relationship in two tables:
* **Nodes:** Every function and class.
* **Edges:** Every connection (e.g., "Chunk 0 *calls* Chunk 1").

With this map built, it runs **Google's PageRank algorithm**. The importance of this algorithm cannot be overstated: in traditional RAG, a tiny, unimportant helper script that happens to mention a keyword might unfairly beat out the main architectural file. PageRank fixes this. If a specific class (like `DatabaseManager`) is called by 50 other files, the algorithm proves it is a highly critical architectural pillar. By assigning it a massive PageRank score, the system mathematically guarantees that the most heavily-relied-upon code always rises to the top of the search results, completely filtering out irrelevant noise.

---

## A Look Inside the Databases

To truly understand how this works, imagine what these four files actually look like when the system ingests a function like `def check_auth(user_token):`.

### 1. The Master List (`chunks.pkl`)
This file assigns an ID to the chunk and saves the raw text.
* **[Chunk 5]:** `def check_auth(user_token): ...`

### 2. FAISS (`faiss.bin`)
A grid of raw math (768 numbers per row). Line 5 belongs to Chunk 5. It holds the mathematical "meaning" of the function.
```text
Row 0: [0.11, 0.45, -0.99, ... ]
...
Row 5: [0.88, 0.12, -0.45, ... ] 
```

### 3. BM25 (`bm25.pkl`)
A dictionary mapping every word to chunks with BM25 scores.
```json
{
    "check_auth": { "chunk_5": 14.5 },
    "user_token": { "chunk_5": 8.2, "chunk_10": 4.1 }
}
```

### 4. SQLite (`graph.db`)
A relational database mapping connections and storing the **PageRank score** directly in the `nodes` table.

**`nodes` table:**
| id  | type     | name         | pagerank_score | chunk_id |
|-----|----------|--------------|----------------|----------|
| 5   | function | `check_auth` | **2.45**       | 5        |

**`edges` table:**
| source_id | target_id   | relationship |
|-----------|-------------|--------------|
| 5         | 10          | `calls`      |

When a query is made, FAISS votes based on math, BM25 votes based on the full **TF-IDF score** (combining word rarity and term frequency), and SQLite votes based on the **PageRank score**. The system aggregates these votes to find the ultimate winner.

---

## Phase 2: Querying (The Chat)

When you finally type a question into the chat, an autonomous **Agentic State Machine** takes over to orchestrate the search.

### 1. Agentic Planning
Powered by a fast LLM reasoning engine, the Agent doesn't just blindly search your exact prompt. It plans out multiple sub-queries. It also uses **HyDE (Hypothetical Document Embeddings)**, where it writes fake, hypothetical code answering your question, and uses that fake code to search FAISS for real code that looks mathematically similar.

### 2. Tri-Modal Search Execution
The system takes the planned queries and searches all three databases simultaneously:
1. **FAISS** finds the concepts.
2. **BM25** finds the exact words.
3. **SQLite** finds the architectural importance.

### 3. Reciprocal Rank Fusion (RRF)
The system now has three completely different lists of winning code chunks. It cannot simply add their scores together because the scoring systems are completely incompatible (FAISS scores are between 0-1, while BM25 scores can be 105).

To solve this, it uses **Reciprocal Rank Fusion (RRF)**. RRF ignores the raw math scores entirely and only looks at the **Rank Position** (1st place, 2nd place, 3rd place). 

It gives points based on a simple fraction: `1 / (60 + rank position)`.
This mathematically guarantees that a code snippet which placed **#3 in Vector**, **#2 in Keyword**, and **#5 in PageRank** will beat a snippet that placed #1 in Vector but didn't even show up on the other two lists. RRF rewards code that is consistently relevant across multiple different types of search.

### 4. The Final Synthesis
RRF crowns the ultimate winning chunk IDs. The system takes these winning IDs, goes back to the **Master List (`chunks.pkl`)**, rips out the raw human-readable code for those specific functions, and hands them to the AI. 

The AI reads this highly-targeted, perfectly verified code and synthesizes a flawlessly accurate response to your original question.

---

## Key Learnings

Building a production-grade, AI-powered codebase search engine yielded several critical insights:

1. **Pure Vector Search Fails for Code:** Standard vector embeddings (FAISS) are excellent at capturing semantic meaning, but they fail catastrophically at exact matches (like specific variable names or obscure function parameters). Code requires a hybrid approach.
2. **PageRank Translates to Code Importance:** Applying Google's PageRank algorithm to a codebase's Abstract Syntax Tree (AST) brilliantly solved the "noisy retrieval" problem. It ensures that widely used utility functions naturally surface higher than isolated, one-off scripts.
3. **RRF is the Great Equalizer:** When combining three entirely different retrieval systems, the mathematical scores are fundamentally incompatible (e.g., FAISS cosine similarity vs. BM25 TF-IDF scoring vs. PageRank centrality). Reciprocal Rank Fusion (RRF) proved absolutely vital for normalizing these lists into a single, highly accurate ranking purely based on position.
4. **Empirical Evaluation Over "Vibes":** Implementing the LangSmith "LLM-as-a-Judge" pipeline was a game-changer. It transformed our evaluation process from subjective "vibes" into hard data, proving across 6 concrete metrics that the Tri-Modal approach vastly outperformed standard Vector search.

---

## Mistakes & Pitfalls (What Went Wrong)

The evolution of Code Compass was not without its architectural hurdles. Here are the biggest mistakes made and how they were overcome:

### 1. The 29-Second Timeout Trap
Initially, we attempted to execute the heavy indexing pipeline (cloning, chunking, embedding, graphing) inside a single AWS Lambda function triggered directly by API Gateway. 
* **The Mistake:** API Gateway enforces a strict, unchangeable 29-second timeout on all HTTP requests. Processing a mid-sized repository took several minutes, causing immediate 504 Gateway Timeouts.
* **The Fix:** We decoupled the architecture into two distinct Lambdas. A lightning-fast **Dispatcher** immediately returns a `202 Accepted` to bypass the gateway timeout, and simultaneously triggers a heavy **Worker** Lambda asynchronously in the background.

### 2. The Heavy Deployment Bottleneck
When attempting to deploy the `RAG-Ingestion-Worker` Lambda, the deployment package ballooned to 68MB because it contained heavy ML libraries (FAISS, NetworkX).
* **The Mistake:** Trying to deploy this massive `.zip` file directly via the AWS CLI (`update-function-code`) resulted in severe network timeouts and dropped connections.
* **The Fix:** We implemented a two-step deployment pipeline. First, we push the 68MB package to an Amazon S3 bucket via a robust multipart upload. Second, we command Lambda to pull the code internally directly from S3 on the AWS backbone.

### 3. The "Manual Cache" Anti-Pattern
Early in development, caching was handled by a manual "Force Re-Index" button on the frontend. If a user pushed new code to GitHub, they had to remember to explicitly check the force box.
* **The Mistake:** Relying on the user to manually manage cache invalidation is terrible UX and leads to the AI answering questions based on stale, outdated code.
* **The Fix:** We implemented **Autonomous Smart Caching**. The Dispatcher now instantly hits the GitHub API (`/commits/HEAD`) to fetch the live commit SHA. It compares this against the SHA stored in DynamoDB. If they mismatch, it autonomously invalidates the cache and re-indexes the fresh code entirely behind the scenes.

---

## Conclusion

Code Compass represents a paradigm shift in how developers interact with complex, undocumented repositories. By combining the semantic understanding of Large Language Models, the exact precision of Lexical Search, and the structural awareness of Graph Theory into a unified **Tri-Modal RAG Engine**, it bridges the gap between human language and machine logic. 

Furthermore, by grounding this intelligence in a fully serverless, highly decoupled AWS architecture, the system is exceptionally resilient, infinitely scalable, and capable of indexing and comprehending entire codebases autonomously.
