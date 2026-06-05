from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from app.config import GROQ_API_KEY


llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama-3.1-8b-instant",
    temperature=0,
)


def generate_chat_title(question: str):
    prompt = PromptTemplate.from_template(
        """
Generate a short chat title (3-5 words max).

Question:
{question}

Title:
"""
    )

    chain = prompt | llm

    response = chain.invoke(
        {"question": question}
    )

    title = response.content.strip()
    
    return title[:50]