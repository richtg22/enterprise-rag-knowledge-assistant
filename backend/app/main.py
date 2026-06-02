import gc
import os
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import CHROMA_DB_PATH, UPLOAD_DIR
from app.document_loader import load_and_split_pdf
from app.rag import create_vector_store, get_qa_chain
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import User, ChatHistory

app = FastAPI(title="Enterprise RAG Knowledge Assistant")
Base.metadata.create_all(bind=engine)

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

chat_histories = {}
MAX_HISTORY = 5


class QuestionRequest(BaseModel):
    question: str


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


@app.get("/")
def health_check():
    return {"message": "Enterprise RAG Assistant API is running"}

@app.post("/register")
def register_user(
    user: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    db_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {
        "message": "User registered successfully"
    }

@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    email = form_data.username
    password = form_data.password

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        password,
        existing_user.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        data={"sub": existing_user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": existing_user.name,
            "email": existing_user.email
        }
    }

@app.post("/upload")
async def upload_document(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    all_documents = []

    for file in files:
        file_path = os.path.join(
            UPLOAD_DIR,
            file.filename
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        docs = load_and_split_pdf(file_path)
        all_documents.extend(docs)

    create_vector_store(all_documents)

    return {
        "message": "Documents uploaded successfully",
        "documents": len(files),
        "chunks": len(all_documents),
        "user": current_user.email,
    }


@app.post("/ask")
def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qa_chain = get_qa_chain()

    recent_chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(MAX_HISTORY)
        .all()
    )

    history_text = ""

    for chat in reversed(recent_chats):
        history_text += f"""
Previous Question:
{chat.question}

Previous Answer:
{chat.answer}

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
            sources.append({
                "source": source,
                "page": page,
            })

    new_chat = ChatHistory(
        user_id=current_user.id,
        question=request.question,
        answer=response["result"],
    )

    db.add(new_chat)
    db.commit()

    return {
        "answer": response["result"],
        "sources": sources,
        "user": current_user.email,
    }


@app.delete("/clear")
def clear_knowledge_base(
    current_user: dict = Depends(get_current_user),
):
    import gc

    gc.collect()

    user_email = current_user.email

    # Clear only this user's conversation memory
    if user_email in chat_histories:
        chat_histories[user_email].clear()

    if os.path.exists(CHROMA_DB_PATH):
        try:
            shutil.rmtree(CHROMA_DB_PATH)
        except PermissionError:
            return {
                "message": (
                    "ChromaDB is currently in use. "
                    "Please stop the backend server, "
                    "manually delete chroma_db folder, "
                    "then restart."
                )
            }

    if os.path.exists(UPLOAD_DIR):
        shutil.rmtree(UPLOAD_DIR)

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    return {
        "message": "Knowledge base cleared successfully",
        "user": user_email,
    }