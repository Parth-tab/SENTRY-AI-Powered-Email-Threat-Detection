import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SENTRY - Forensic Email Threat Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Databases
    DATABASE_URL: str = "sqlite+aiosqlite:///./sentry.db"
    SYNC_DATABASE_URL: str = "sqlite:///./sentry.db"
    
    # Message Queue & Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Graph Intelligence
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "sentry_graph_2025"

    # Security & Evidence
    SECRET_KEY: str = "sentry_super_secret_jwt_key_hackathon_2025_entropy_high"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    EVIDENCE_VAULT_DIR: str = str(BASE_DIR.parent / "evidence_vault")

    # Threat Intel Feeds (Optional with live fallbacks)
    VIRUSTOTAL_API_KEY: str = ""
    URLHAUS_API_KEY: str = ""
    THREATFOX_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Ensure evidence vault directory exists
Path(settings.EVIDENCE_VAULT_DIR).mkdir(parents=True, exist_ok=True)
