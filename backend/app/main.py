import gc
import os
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import CHROMA_DB_PATH, UPLOAD_DIR
from app.database import Base, engine, get_db
from app.document_loader import load_and_split_pdf
from app.models import ChatHistory, User, Document
from app.rag import create_vector_store, get_qa_chain, delete_document_vectors


app = FastAPI(title="Enterprise RAG Knowledge Assistant")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://enterprise-rag-knowledge-assistant-seven.vercel.app",
        "https://enterprise-rag-knowledge-assistant-fbxodrthk.vercel.app",
        "https://enterprise-rag-knowledge-assistant-5g5v0lht9.vercel.app",
    ],
    allow_origin_regex=r"https://enterprise-rag-knowledge-assistant.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    db: Session = Depends(get_db),
):
    if len(user.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must be 72 bytes or fewer",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User already exists",
        )

    db_user = User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "User registered successfully"}


@app.post("/login")
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
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
            detail="Invalid email or password",
        )

    if not verify_password(password, existing_user.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        data={"sub": existing_user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "name": existing_user.name,
            "email": existing_user.email,
        },
    }


@app.post("/upload")
async def upload_document(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_upload_dir = os.path.join(
        UPLOAD_DIR,
        f"user_{current_user.id}",
    )

    os.makedirs(user_upload_dir, exist_ok=True)

    all_documents = []

    for file in files:
        file_path = os.path.join(
            user_upload_dir,
            file.filename,
        )

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        docs = load_and_split_pdf(file_path)

        for doc in docs:
            doc.metadata["filename"] = file.filename
            doc.metadata["user_id"] = current_user.id

        all_documents.extend(docs)

        existing_document = (
            db.query(Document)
            .filter(
                Document.user_id == current_user.id,
                Document.filename == file.filename,
            )
            .first()
        )

        if not existing_document:
            new_document = Document(
                user_id=current_user.id,
                filename=file.filename,
            )
            db.add(new_document)

    create_vector_store(
        all_documents,
        current_user.id,
    )

    db.commit()

    return {
        "message": "Documents uploaded successfully",
        "documents": len(files),
        "chunks": len(all_documents),
        "user": current_user.email,
    }


@app.get("/documents")
def get_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "uploaded_at": document.uploaded_at,
        }
        for document in documents
    ]


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id,
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )
    
    deleted_vectors = delete_document_vectors(
        current_user.id,
        document.filename,
    )

    user_upload_dir = os.path.join(
        UPLOAD_DIR,
        f"user_{current_user.id}",
    )

    file_path = os.path.join(
        user_upload_dir,
        document.filename,
    )

    if os.path.exists(file_path):
        os.remove(file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully",
            "deleted_vectors": deleted_vectors,
            }

@app.get("/chat-history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chats = (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.asc())
        .all()
    )

    return [
        {
            "id": chat.id,
            "question": chat.question,
            "answer": chat.answer,
            "created_at": chat.created_at,
            "sources": [],
        }
        for chat in chats
    ]

@app.post("/ask")
def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qa_chain = get_qa_chain(current_user.id)

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

    response = qa_chain.invoke(
        {"query": contextual_question}
    )

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
            sources.append(
                {
                    "source": source,
                    "page": page,
                }
            )

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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gc.collect()

    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id
    ).delete()

    db.query(Document).filter(
        Document.user_id == current_user.id
    ).delete()

    db.commit()

    user_chroma_path = os.path.join(
        CHROMA_DB_PATH,
        f"user_{current_user.id}",
    )

    if os.path.exists(user_chroma_path):
        try:
            shutil.rmtree(user_chroma_path)
        except PermissionError:
            return {
                "message": (
                    "ChromaDB is currently in use. "
                    "Please stop the backend server, manually delete the folder, then restart."
                )
            }

    user_upload_dir = os.path.join(
        UPLOAD_DIR,
        f"user_{current_user.id}",
    )

    if os.path.exists(user_upload_dir):
        shutil.rmtree(user_upload_dir)

    os.makedirs(user_upload_dir, exist_ok=True)

    return {
        "message": "Knowledge base cleared successfully",
        "user": current_user.email,
    }