import os

from dotenv import load_dotenv


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")

CHROMA_DB_PATH = os.getenv(
    "CHROMA_DB_PATH",
    "chroma_db"
)

UPLOAD_DIR = os.getenv(
    "UPLOAD_DIR",
    "uploads"
)