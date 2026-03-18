"""
Application configuration module.
Loads environment variables using python-dotenv and provides
a centralized Settings class for all configuration values.
"""

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Groq API
    GROQ_API_KEY: str = ""

    # PostgreSQL
    POSTGRES_DB_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_chatbot"

    # ChromaDB
    CHROMA_DB_PATH: str = "./chroma_db"

    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Embedding Model
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # LLM
    LLM_MODEL_NAME: str = "openai/gpt-oss-120b"

    # Chunk Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Top K results for similarity search
    TOP_K_RESULTS: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Returns a cached singleton instance of Settings."""
    return Settings()
