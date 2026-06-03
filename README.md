# Enterprise RAG Knowledge Assistant

A full-stack Retrieval-Augmented Generation (RAG) application that enables users to upload multiple PDF documents and ask grounded questions using semantic search, conversational memory, and LLM-powered responses with source citations.

## Features

* Multi-document PDF upload and indexing
* Semantic search using vector embeddings
* Retrieval-Augmented Generation (RAG) based question answering
* Source citations with page references
* Conversational memory for multi-turn document interactions
* Chat history with timestamps
* Knowledge base management (clear and re-index documents)
* Upload statistics and document tracking
* Custom enterprise prompt for grounded responses
* React frontend and FastAPI backend architecture
* User registration and login
* JWT-based authentication
* Protected document upload, question answering and knowledge base clearing

## Tech Stack

### Frontend

* React
* Axios
* CSS

### Backend

* FastAPI
* LangChain
* ChromaDB
* Groq LLM
* Python

## Architecture

```text
User
  ↓
React Frontend
  ↓
FastAPI Backend
  ↓
LangChain Retrieval Pipeline
  ↓
ChromaDB Vector Store
  ↓
Groq LLM
```

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

### Run with Docker

```bash
docker compose up --build

## Implemented Features

* Multi-PDF Upload
* Semantic Document Retrieval
* Source Citations
* Chat History
* Conversational Memory
* Knowledge Base Management
* Enterprise Prompting
* Multi-turn Question Answering
* Dockerized frontend/backend

## Example Conversation

**User:** What is this document about?

**Assistant:** The document provides a project status update and outlines the next phase plan.

**User:** What are the next steps?

**Assistant:** Based on the project update, the next steps include final testing, scalability validation, and a review meeting with stakeholders.

**User:** Who is responsible?

**Assistant:** The project team is responsible for mitigating risks and completing validation activities.

## Future Enhancements

* JWT Authentication
* PostgreSQL Chat Persistence
* Docker Support
* Cloud Deployment (Vercel + Render)
* User-Specific Knowledge Bases
* Advanced LangChain Memory

## Screenshots

Screenshots and deployment links will be added soon.
