import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SENTRY - Forensic Email Threat Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "demo"
    DEBUG: bool = True

    # Databases: SQLite (aiosqlite) anchored to backend/sentry.db; Postgres in Production Cloud Mode
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR.as_posix()}/sentry.db"
    SYNC_DATABASE_URL: str = f"sqlite:///{BASE_DIR.as_posix()}/sentry.db"
    
    # Message Queue & Cache (Optional distributed workers)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Graph Intelligence (Optional enterprise graph cluster)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = ""

    # Security & Evidence
    SECRET_KEY: str = "sentry_demo_secret_key_2025_evidentiary_standard"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    EVIDENCE_VAULT_DIR: str = str(BASE_DIR.parent / "evidence_vault")

    # Threat Intel Feeds (Optional with simulated offline fallbacks)
    VIRUSTOTAL_API_KEY: str = ""
    URLHAUS_API_KEY: str = ""
    THREATFOX_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

# Fail-safe security validator: Production mode requires explicitly injected entropy
if settings.ENVIRONMENT.lower() == "production":
    if "demo" in settings.SECRET_KEY.lower() or "secret" in settings.SECRET_KEY.lower():
        raise RuntimeError(
            "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a secure, "
            "cryptographically random SECRET_KEY injected via environment variable."
        )

# Ensure evidence vault directory exists
Path(settings.EVIDENCE_VAULT_DIR).mkdir(parents=True, exist_ok=True)
