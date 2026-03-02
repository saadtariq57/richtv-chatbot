from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # LLM Configuration
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash-lite"
    
    # Data Source API Keys
    mboum_api_key: Optional[str] = None
    fmp_api_key: Optional[str] = None
    fmp_base_url: str = "https://financialmodelingprep.com/api/v3"
    
    # Vector DB (Qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: Optional[str] = None
    
    # In-memory / cache (Redis)
    redis_url: str = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env (prevents errors)

settings = Settings()

