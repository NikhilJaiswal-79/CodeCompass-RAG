# 🔍 ContribLens: Cloud-Native Codebase RAG Engine

ContribLens is a state-of-the-art **Tri-Modal Retrieval-Augmented Generation (RAG) Engine** designed to instantly index, comprehend, and navigate massive, unfamiliar codebases. 

Unlike traditional RAG systems that blindly chop text into chunks, ContribLens uses Abstract Syntax Trees (AST) and Graph Mathematics to truly understand the structural logic of code, acting as an AI Senior Developer that can answer complex architectural questions. It is fully modernized and deployed as a highly scalable **Serverless AWS Cloud Architecture**.

## 🌟 Key Innovations

### 1. Tri-Modal Search (Vector + Keyword + PageRank)
ContribLens abandons standard vector-only search for a hyper-accurate Tri-Modal approach:
* **Dense Vectors (FAISS):** Semantic conceptual matching.
* **Sparse Keywords (BM25):** Ensures exact variable and function names are never lost.
* **Graph Centrality (PageRank):** Calculates the PageRank of the SQLite dependency graph to artificially boost structurally critical "God classes" in the search results.
* All three signals are fused together mathematically using **Reciprocal Rank Fusion (RRF)**.

### 2. AST-Aware Ingestion (Tree-sitter)
Instead of arbitrary character-count chunking, it uses Tree-sitter bindings across 15+ languages to surgically extract perfect, logical functions and classes. 

### 3. Agentic State Machine (LangGraph)
Powered by **Google Gemini 3.1 Flash Lite**, the reasoning engine is a true Agent. When asked a complex question, the Agent:
1. Plans multiple sub-queries.
2. Generates Hypothetical Code (HyDE) to improve vector matching.
3. Automatically compresses noisy context.
4. **Self-Corrects:** If the retrieved code is insufficient, the Agent loops back and executes new searches autonomously.

### 4. 100% Serverless AWS Architecture
The backend is completely decoupled into a highly scalable cloud pipeline:
- **AWS API Gateway:** Securely routes all incoming traffic.
- **Amazon DynamoDB:** Manages the state and progress of the repository ingestion, featuring **Instant Cache Checks** to prevent redundant indexing.
- **AWS Lambda (Dispatcher):** Instantly acknowledges requests and asynchronously triggers background tasks.
- **AWS Lambda (Heavy Worker):** Dynamically allocates up to 15 minutes of compute to clone, chunk, and index massive repositories in the background.
- **AWS Lambda (Chat):** Streams the LangGraph reasoning engine responses back to the frontend.
- **Amazon S3:** Persistently stores the massive FAISS, BM25, and Graph SQLite databases for instantaneous retrieval.

### 5. Beautiful Frontend
Features a gorgeous, glassmorphic UI built in vanilla HTML/CSS/JS that communicates directly with the cloud APIs.

---

## 🚀 Quick Start

### 1. Local Frontend
You can simply double-click `frontend/index.html` to open the web app in your browser locally!

### 2. AWS Cloud Deployment
All backend logic is fully deployed on AWS. 
If you wish to deploy the frontend to the public internet as well:
1. Create an S3 Bucket and enable **Static Website Hosting**.
2. Upload the `index.html`, `app.js`, and `style.css` files.
3. Deploy an **Amazon CloudFront** distribution in front of the bucket.
4. Link it to your custom domain via **Route 53**.

*Built with LangGraph, FAISS, Google Gemini, and AWS Lambda.*
