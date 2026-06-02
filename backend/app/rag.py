from langchain_chroma import Chroma
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_groq import ChatGroq
from langchain.chains import RetrievalQA
from app.config import CHROMA_DB_PATH, GROQ_API_KEY
from langchain.prompts import PromptTemplate

embedding_model = FastEmbedEmbeddings()


def create_vector_store(documents):
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embedding_model,
        persist_directory=CHROMA_DB_PATH
    )
    return vector_store


def get_qa_chain():
    vector_store = Chroma(
        persist_directory=CHROMA_DB_PATH,
        embedding_function=embedding_model
    )

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    llm = ChatGroq(
        groq_api_key=GROQ_API_KEY,
        model_name="llama-3.1-8b-instant",
        temperature=0
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
        input_variables=["context", "question"]
        )
        
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": prompt}
        )

    return qa_chain