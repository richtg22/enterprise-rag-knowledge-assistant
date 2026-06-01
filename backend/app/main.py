import os
import shutil
import gc

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import UPLOAD_DIR, CHROMA_DB_PATH
from app.document_loader import load_and_split_pdf
from app.rag import create_vector_store, get_qa_chain

app = FastAPI(title="Enterprise RAG Knowledge Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

chat_history = []
MAX_HISTORY = 5


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {"message": "Enterprise RAG Assistant API is running"}


@app.post("/upload")
async def upload_document(files: list[UploadFile] = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    all_documents = []

    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        docs = load_and_split_pdf(file_path)
        all_documents.extend(docs)

    create_vector_store(all_documents)

    return {
        "message": "Documents uploaded successfully",
        "documents": len(files),
        "chunks": len(all_documents),
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    qa_chain = get_qa_chain()

    contextual_question = request.question

    if chat_history:
        recent_history = chat_history[-MAX_HISTORY:]

        history_text = ""

        for interaction in recent_history:
            history_text += f"""
Previous Question:
{interaction["question"]}

Previous Answer:
{interaction["answer"]}

"""

        contextual_question = f"""
Conversation History:
{history_text}

Current Question:
{request.question}
"""

    response = qa_chain.invoke({"query": contextual_question})

    sources = []
    seen = set()

    for doc in response["source_documents"]:
        source = os.path.basename(doc.metadata.get("source", ""))
        page = doc.metadata.get("page", 0) + 1

        key = (source, page)

        if key not in seen:
            seen.add(key)

            sources.append(
                {
                    "source": source,
                    "page": page,
                }
            )

    chat_history.append(
        {
            "question": request.question,
            "answer": response["result"],
        }
    )

    if len(chat_history) > MAX_HISTORY:
        chat_history.pop(0)

    return {
        "answer": response["result"],
        "sources": sources,
    }


@app.delete("/clear")
def clear_knowledge_base():
    gc.collect()

    chat_history.clear()

    if os.path.exists(CHROMA_DB_PATH):
        try:
            shutil.rmtree(CHROMA_DB_PATH)
        except PermissionError:
            return {
                "message": "ChromaDB is currently in use. Please stop the backend server, manually delete chroma_db folder, then restart."
            }

    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    return {"message": "Knowledge base cleared successfully"}