# Enterprise RAG Knowledge Assistant

A production-ready Retrieval-Augmented Generation (RAG) platform that enables users to securely upload PDF documents, perform hybrid document retrieval, and interact with enterprise knowledge through conversational AI.

The application combines vector search, keyword-based retrieval, cloud storage, persistent chat history, AI-generated conversation titles, and streaming LLM responses to deliver grounded answers with source citations.

---

## Features

### Authentication & User Management

* User Registration and Login
* JWT-based Authentication
* Protected API Endpoints
* User-specific Knowledge Bases
* Multi-user Isolation

### Document Management

* Multi-PDF Upload and Indexing
* Cloud Storage using Supabase Storage
* Secure PDF Preview with Signed URLs
* Document Deletion
* Automatic Embedding Cleanup
* Knowledge Base Reset

### Retrieval-Augmented Generation

* Hybrid Search (BM25 + Vector Search)
* ChromaDB Vector Store
* FastEmbed Embeddings
* Source-grounded Responses
* Page-level Citations
* Conversational Context Awareness
* Multi-turn Question Answering

### Conversation Management

* Multiple Conversations
* Persistent Chat History
* AI-generated Conversation Titles
* Conversation Deletion
* Context-aware Follow-up Questions

### User Experience

* Real-time Streaming Responses
* Modern React Interface
* Document Dashboard
* Responsive Layout
* Source Citation Display

### Infrastructure

* Docker & Docker Compose
* GitHub Actions CI/CD
* Supabase PostgreSQL
* Supabase Storage
* Render Backend Deployment
* Vercel Frontend Deployment

---

## Tech Stack

### Frontend

* React
* Axios
* CSS

### Backend

* FastAPI
* Python
* SQLAlchemy
* JWT Authentication

### AI & Retrieval

* LangChain
* ChromaDB
* FastEmbed Embeddings
* Groq LLM (Llama 3.1)
* BM25 Retrieval

### Database & Storage

* Supabase PostgreSQL
* Supabase Storage

### DevOps

* Docker
* Docker Compose
* GitHub Actions
* Render
* Vercel

---

## System Architecture

```text
User
 │
 ▼
React Frontend (Vercel)
 │
 ▼
FastAPI Backend (Render)
 │
 ├── JWT Authentication
 │
 ├── Conversation Management
 │
 ├── Hybrid Retrieval Engine
 │      ├── BM25 Search
 │      └── Vector Search
 │
 ├── Groq LLM Streaming
 │
 ├── ChromaDB
 │
 ├── Supabase PostgreSQL
 │
 └── Supabase Storage
```

---

## Retrieval Pipeline

```text
Question
   │
   ▼
Hybrid Retrieval
 ├── Vector Search
 └── BM25 Search
   │
   ▼
Merge & Deduplicate Results
   │
   ▼
Groq LLM
   │
   ▼
Grounded Answer + Citations
```

---

## Local Setup

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

### Docker

```bash
docker compose up --build
```

---

## Environment Variables

### Backend `.env`

```env
GROQ_API_KEY=

SECRET_KEY=

DATABASE_URL=

SUPABASE_URL=

SUPABASE_SERVICE_ROLE_KEY=

SUPABASE_BUCKET=rag-documents

CHROMA_DB_PATH=chroma_db

UPLOAD_DIR=uploads
```

---

## Key Implemented Features

* JWT Authentication
* Supabase PostgreSQL Integration
* Supabase Storage Integration
* Multi-PDF Upload
* Hybrid Search (BM25 + Vector Search)
* ChromaDB Vector Storage
* Streaming Responses
* AI-generated Conversation Titles
* Multi-Conversation Support
* Persistent Chat History
* Conversational Memory
* Source Citations
* Document Preview
* Document Deletion with Embedding Cleanup
* Dockerized Deployment
* CI/CD Pipeline

---

## Example Workflow

```text
Upload PDFs
      │
      ▼
Generate Embeddings
      │
      ▼
Store in ChromaDB
      │
      ▼
Ask Question
      │
      ▼
Hybrid Retrieval
      │
      ▼
Groq LLM
      │
      ▼
Stream Response
      │
      ▼
Display Sources
```

---

## Example Conversation

**User:** What is this document about?

**Assistant:** The document provides a project status update and outlines the next phase plan.

**User:** What are the next steps?

**Assistant:** Based on the project update, the next steps include final testing, scalability validation, and a review meeting with stakeholders.

**User:** What are the project risks?

**Assistant:** The document highlights deployment monitoring, validation activities, and stakeholder approvals as key risk areas requiring attention.

---

## Deployment

### Frontend

* Vercel

### Backend

* Render

### Database

* Supabase PostgreSQL

### Storage

* Supabase Storage

---

## Future Enhancements

* Cross-Encoder Reranking
* Retrieval Analytics Dashboard
* Chat Export to PDF
* Admin Dashboard
* Role-Based Access Control (RBAC)
* Multi-Modal Document Support
* Advanced Evaluation Metrics
* Enterprise Monitoring & Observability

---

## Screenshots (will add soon)

### Login Page


### Dashboard


### Multi-Conversation Interface


### Document Management


### Streaming Responses


---

## Author

Developed as a full-stack GenAI project demonstrating Retrieval-Augmented Generation, hybrid retrieval systems, cloud-native architecture, secure document management, and production-grade AI application development.
