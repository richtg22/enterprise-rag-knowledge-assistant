# Enterprise RAG Knowledge Assistant

A full-stack Retrieval-Augmented Generation (RAG) application that enables users to upload multiple PDF documents and ask grounded questions using semantic search and LLM-powered responses with source citations.

## Features

* Multi-document PDF upload and indexing
* Semantic search using vector embeddings
* RAG-based question answering
* Source citations with page references
* Conversational chat history
* Knowledge base management (clear and re-index documents)
* Upload statistics and document tracking
* Custom enterprise prompt for grounded responses
* React frontend and FastAPI backend architecture

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

User → React Frontend → FastAPI Backend → LangChain → ChromaDB → Groq LLM

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

## Current Features

* Multi-PDF Upload
* Semantic Document Retrieval
* Source Citations
* Chat History
* Knowledge Base Management
* Enterprise Prompting

## Future Enhancements

* Conversational Memory
* JWT Authentication
* PostgreSQL Integration
* Docker Support
* Cloud Deployment
* User-Specific Knowledge Bases

