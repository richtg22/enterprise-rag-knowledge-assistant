import os
import shutil
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from app.config import UPLOAD_DIR, CHROMA_DB_PATH
from app.document_loader import load_and_split_pdf
from app.rag import create_vector_store, get_qa_chain

from fastapi.middleware.cors import CORSMiddleware
import shutil
import os

app = FastAPI(title="Enterprise RAG Knowledge Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def health_check():
    return {"message": "Enterprise RAG Assistant API is running"}


@app.post("/upload")
async def upload_document(files: list[UploadFile] = File(...)):

    all_documents=[]

    for file in files:
        file_path=os.path.join(
            UPLOAD_DIR,
            file.filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )
        docs=load_and_split_pdf(file_path)
        all_documents.extend(docs)

    create_vector_store(all_documents)

    return {
        "message": "Documents uploaded successfully",
        "documents": len(files),
        "chunks": len(all_documents)
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    qa_chain = get_qa_chain()
    response = qa_chain.invoke({"query": request.question})

    sources = []
    seen = set()
    
    for doc in response["source_documents"]:
        source = os.path.basename(
            doc.metadata.get("source", "")
        )
        
        page = doc.metadata.get("page", 0) + 1
        
        key = (source, page)
        
        if key not in seen:
            seen.add(key)
            
            sources.append({
                "source": source,
                "page": page
            })

    return {
        "answer": response["result"],
        "sources": sources
    }

@app.delete("/clear")
def clear_knowledge_base():
    import gc

    gc.collect()

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
