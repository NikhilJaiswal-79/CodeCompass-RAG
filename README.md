# 🔍 CodeCompass (ContribLens): Cloud-Native Codebase RAG Engine

**Live Application:** [https://code-compass.app](https://code-compass.app)

CodeCompass is a state-of-the-art **Tri-Modal Retrieval-Augmented Generation (RAG) Engine** designed to instantly index, comprehend, and navigate massive, unfamiliar codebases. 

Unlike traditional RAG systems that blindly chop text into chunks, CodeCompass uses Abstract Syntax Trees (AST) and Graph Mathematics to truly understand the structural logic of code, acting as an AI Senior Developer that can answer complex architectural questions. It is fully modernized and deployed as a highly scalable **Serverless AWS Cloud Architecture**.

---

## 🌟 Key Innovations

### 1. Tri-Modal Search (Vector + Keyword + PageRank)
CodeCompass abandons standard vector-only search for a hyper-accurate Tri-Modal approach:
* **Dense Vectors (FAISS):** Semantic conceptual matching.
* **Sparse Keywords (BM25):** Ensures exact variable and function names are never lost.
* **Graph Centrality (PageRank):** Maps out function calls and imports to find the most heavily relied-upon code in the repository. It uses Google's PageRank algorithm to guarantee that core architectural files are boosted to the top of your search results, rather than unimportant helper scripts.
* All three signals are fused together mathematically using **Reciprocal Rank Fusion (RRF)**.

### 2. AST-Aware Ingestion (Tree-sitter)
Instead of arbitrary character-count chunking, it uses Tree-sitter bindings across 15+ languages to surgically extract perfect, logical functions and classes. 

### 3. Agentic State Machine (LangGraph)
Powered by **Claude 3.5 Haiku**, the reasoning engine is a true autonomous Agent. When asked a complex question, the Agent:
1. Plans multiple sub-queries.
2. Generates Hypothetical Code (HyDE) to improve vector matching.
3. Automatically compresses noisy context.
4. **Self-Corrects:** If the retrieved code is insufficient, the Agent loops back and executes new searches autonomously.
5. **Robust Parsing:** Features a bulletproof fallback engine that mathematically intercepts and repairs malformed markdown responses from the LLM.

### 4. 100% Serverless AWS Architecture
The backend is completely decoupled into a highly scalable cloud pipeline:
- **AWS API Gateway:** Securely routes all incoming traffic.
- **Amazon DynamoDB:** Manages the state and progress of the repository ingestion, featuring **Smart Cache Checks** to prevent redundant indexing.
- **AWS Lambda (Dispatcher):** Instantly acknowledges requests and asynchronously triggers background tasks (Supports Force Re-Indexing).
- **AWS Lambda (Heavy Worker):** Dynamically allocates up to 15 minutes of compute to clone, chunk, and index massive repositories in the background.
- **AWS Lambda (Chat):** Streams the LangGraph reasoning engine responses back to the frontend.
- **Amazon S3:** Persistently stores the massive FAISS, BM25, and Graph SQLite databases for instantaneous retrieval.

### 5. Premium Glassmorphic UI
Features a gorgeous, responsive UI built in vanilla HTML/CSS/JS that communicates directly with the cloud APIs, offering real-time streaming, smart caching, and force re-indexing controls.

---

## 🚀 Quick Start

### 1. Local Frontend
You can simply double-click `frontend/index.html` to open the web app in your browser locally!

### 2. AWS Cloud Deployment
This application is fully deployed and hosted in the AWS Cloud:
1. **Backend:** All RAG pipeline microservices and conversational agents are running on highly scalable **AWS Lambda** functions behind an **API Gateway**.
2. **Frontend:** The web application is hosted via an **S3 Bucket** with Static Website Hosting enabled.
3. **CDN & DNS:** The frontend is globally accelerated by an **Amazon CloudFront** distribution and routed through **Route 53** to the custom domain (code-compass.app).

*Built with LangGraph, FAISS, Google Gemini, Anthropic Claude, and AWS Lambda.*
