import os

from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_groq import ChatGroq

from app.config import CHROMA_DB_PATH, GROQ_API_KEY

from rank_bm25 import BM25Okapi
from langchain.schema import Document

_embedding_model = None

def get_embedding_model():
    global _embedding_model

    if _embedding_model is None:
        _embedding_model = FastEmbedEmbeddings()

    return _embedding_model


def get_user_chroma_path(user_id: int):
    return os.path.join(CHROMA_DB_PATH, f"user_{user_id}")


def create_vector_store(documents, user_id: int):
    user_chroma_path = get_user_chroma_path(user_id)

    os.makedirs(user_chroma_path, exist_ok=True)

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=get_embedding_model(),
        persist_directory=user_chroma_path,
    )

    return vector_store


def get_qa_chain(user_id: int):
    user_chroma_path = get_user_chroma_path(user_id)

    vector_store = Chroma(
        persist_directory=user_chroma_path,
        embedding_function=get_embedding_model(),
    )

    retriever = vector_store.as_retriever(
        search_kwargs={"k": 5}
    )

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        temperature=0,
    )

    prompt_template = """
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
{question}

Answer:
"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"],
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt},
    )

    return qa_chain

def delete_document_vectors(user_id: int, filename: str):
    user_chroma_path = get_user_chroma_path(user_id)

    vector_store = Chroma(
        persist_directory=user_chroma_path,
        embedding_function=get_embedding_model(),
    )

    collection = vector_store._collection

    results = collection.get()

    ids_to_delete = []

    for doc_id, metadata in zip(
        results.get("ids", []),
        results.get("metadatas", []),
    ):
        source = metadata.get("source","")
        stored_filename = metadata.get("filename", "")

        if stored_filename == filename or source.endswith(filename):
            ids_to_delete.append(doc_id)

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    return len(ids_to_delete)

def hybrid_retrieve(user_id: int, query: str, k: int = 5):
    user_chroma_path = get_user_chroma_path(user_id)

    vector_store = Chroma(
        persist_directory=user_chroma_path,
        embedding_function=get_embedding_model(),
    )

    vector_docs = vector_store.similarity_search(
        query,
        k=k,
    )

    all_data = vector_store.get()
    documents = all_data.get("documents", [])
    metadatas = all_data.get("metadatas", [])

    if not documents:
        return vector_docs

    tokenized_docs = [
        doc.lower().split()
        for doc in documents
    ]

    bm25 = BM25Okapi(tokenized_docs)

    tokenized_query = query.lower().split()

    bm25_scores = bm25.get_scores(tokenized_query)

    top_indexes = sorted(
        range(len(bm25_scores)),
        key=lambda i: bm25_scores[i],
        reverse=True,
    )[:k]

    bm25_docs = [
        Document(
            page_content=documents[index],
            metadata=metadatas[index] or {},
        )
        for index in top_indexes
    ]

    combined_docs = []
    seen = set()

    for doc in vector_docs + bm25_docs:
        key = (
            doc.page_content[:120],
            doc.metadata.get("source", ""),
            doc.metadata.get("page", ""),
            doc.metadata.get("filename", ""),
        )

        if key not in seen:
            seen.add(key)
            combined_docs.append(doc)

    return combined_docs[:k]