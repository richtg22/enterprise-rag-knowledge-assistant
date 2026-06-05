import gc
import os
import shutil

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.utils.title_generator import generate_chat_title

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.config import CHROMA_DB_PATH, UPLOAD_DIR, GROQ_API_KEY
from app.database import Base, engine, get_db
from app.document_loader import load_and_split_pdf
from app.models import ChatHistory, User, Document, Conversation
from app.rag import ( 
    create_vector_store, get_qa_chain, delete_document_vectors, hybrid_retrieve,
)

from app.storage import upload_file_to_supabase, delete_file_from_supabase, get_signed_url

from langchain_groq import ChatGroq

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
    conversation_id: int | None = None


class ConversationRequest(BaseModel):
    title: str = "New Conversation"


class UserRegister(BaseModel):
    name: str
    email: str
    password: str


@app.get("/")
def health_check():
    return {"message": "Enterprise RAG Assistant API is running"}


@app.post("/register")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

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

    existing_user = db.query(User).filter(User.email == email).first()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(password, existing_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(data={"sub": existing_user.email})

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

        storage_path = upload_file_to_supabase(
            current_user.id,
            file.filename,
            file_path,
        )

        docs = load_and_split_pdf(file_path)

        for doc in docs:
            doc.metadata["filename"] = file.filename
            doc.metadata["user_id"] = current_user.id
            doc.metadata["storage_path"] = storage_path

        all_documents.extend(docs)

        existing_document = (
            db.query(Document)
            .filter(
                Document.user_id == current_user.id,
                Document.filename == file.filename,
            )
            .first()
        )

        if existing_document:
            existing_document.storage_path = storage_path
        else:
            db.add(
                Document(
                    user_id=current_user.id,
                    filename=file.filename,
                    storage_path=storage_path,
                )
            )

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
            "storage_path": document.storage_path,
            "uploaded_at": document.uploaded_at,
        }
        for document in documents
    ]

@app.get("/documents/{document_id}/view")
def view_document(
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

    if not document.storage_path:
        raise HTTPException(
            status_code=404,
            detail="Storage path missing",
        )

    signed_url = get_signed_url(
        document.storage_path
    )

    return {
        "url": signed_url
    }

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

    delete_file_from_supabase(
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

    return {
        "message": "Document deleted successfully",
        "deleted_vectors": deleted_vectors,
    }

@app.post("/conversations")
def create_conversation(
    request: ConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


@app.get("/conversations")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )

    return [
        {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at,
        }
        for conversation in conversations
    ]

@app.put("/conversations/{conversation_id}")
def update_conversation_title(
    conversation_id: int,
    request: ConversationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation.title = request.title[:50] or "New Conversation"

    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }

@app.get("/conversations/{conversation_id}/chats")
def get_conversation_chats(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    chats = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == current_user.id,
            ChatHistory.conversation_id == conversation_id,
        )
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


@app.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.query(ChatHistory).filter(
        ChatHistory.user_id == current_user.id,
        ChatHistory.conversation_id == conversation_id,
    ).delete()

    db.delete(conversation)
    db.commit()

    return {"message": "Conversation deleted successfully"}


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
            "conversation_id": chat.conversation_id,
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

    conversation_id = request.conversation_id

    if conversation_id is None:
        generated_title = generate_chat_title(request.question)

        conversation = Conversation(
            user_id=current_user.id,
            title=generated_title or request.question[:50] or "New Conversation",
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        conversation_id = conversation.id
    else:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail="Conversation not found",
            )

        if conversation.title == "New Conversation":
            generated_title = generate_chat_title(request.question)
            conversation.title = (
                generated_title
                or request.question[:50]
                or "New Conversation"
            )
            db.commit()
            db.refresh(conversation)

    recent_chats = (
        db.query(ChatHistory)
        .filter(
            ChatHistory.user_id == current_user.id,
            ChatHistory.conversation_id == conversation_id,
        )
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

    retrieved_docs = hybrid_retrieve(
        current_user.id,
        contextual_question,
        k=5,
    )

    if not retrieved_docs:
        answer = "I could not find that information in the uploaded documents."
        sources = []
    else:
        context = "\n\n".join(
            [
                f"Source: {os.path.basename(doc.metadata.get('source', ''))}, "
                f"Page: {doc.metadata.get('page', 0) + 1}\n"
                f"{doc.page_content}"
                for doc in retrieved_docs
            ]
        )

        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.1-8b-instant",
            temperature=0,
        )

        prompt = f"""
You are an enterprise knowledge assistant.

Use ONLY the information provided in the context.

When the user asks for:
- a summary
- what the document is about
- what the document says

provide a concise but complete summary of the retrieved content.

Do not say "the context appears to be".

Answer confidently using the retrieved information.

If the answer is not contained in the context, respond:

"I could not find that information in the uploaded documents."

Context:
{context}

Question:
{contextual_question}

Answer:
"""

        response = llm.invoke(prompt)
        answer = response.content

        sources = []
        seen = set()

        for doc in retrieved_docs:
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

    new_chat = ChatHistory(
        user_id=current_user.id,
        conversation_id=conversation_id,
        question=request.question,
        answer=answer,
    )

    db.add(new_chat)
    db.commit()

    return {
        "answer": answer,
        "sources": sources,
        "user": current_user.email,
        "conversation_id": conversation_id,
        "conversation_title": conversation.title,
    }

@app.delete("/clear")
def clear_knowledge_base(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    gc.collect()

    db.query(ChatHistory).filter(ChatHistory.user_id == current_user.id).delete()
    db.query(Conversation).filter(Conversation.user_id == current_user.id).delete()
    db.query(Document).filter(Document.user_id == current_user.id).delete()

    db.commit()

    user_chroma_path = os.path.join(CHROMA_DB_PATH, f"user_{current_user.id}")

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

    user_upload_dir = os.path.join(UPLOAD_DIR, f"user_{current_user.id}")

    if os.path.exists(user_upload_dir):
        shutil.rmtree(user_upload_dir)

    os.makedirs(user_upload_dir, exist_ok=True)

    return {
        "message": "Knowledge base cleared successfully",
        "user": current_user.email,
    }