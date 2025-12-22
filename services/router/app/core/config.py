from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Intelligent Burst Router"
    API_V1_STR: str = "/api/v1"
    
    # Lemonade/Local LLM Configuration
    LEMONADE_SERVER_URL: str = "http://localhost:8000"
    LEMONADE_CHECK_INTERVAL: int = 30  # seconds
    
    # Routing Thresholds
    MAX_TTFT_MS: int = 2000
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jarvis_router"
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    # Cloud Providers (for failover)
    GEMINI_API_KEY: Optional[str] = None
    AZURE_OPENAI_KEY: Optional[str] = None
    AZURE_OPENAI_ENDPOINT: Optional[str] = None

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
