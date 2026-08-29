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

    # Production Serving & Frontend Static Mount (D1)
    SERVE_STATIC: bool = False
    BUILD_MODE: str = "demo"
    FRONTEND_DIST_DIR: str = str(BASE_DIR.parent / "frontend" / "dist")
    CORS_ORIGINS: str = ""
    SENTRY_API_TOKEN: str = "sentry_operator_token_2025"

    # Security & Evidence
    SECRET_KEY: str = "sentry_demo_secret_key_2025_evidentiary_standard"
    ADMIN_TOKEN: str = "sentry_admin_demo_secret_2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    EVIDENCE_VAULT_DIR: str = str(BASE_DIR.parent / "evidence_vault")
    LOGS_DIR: str = str(BASE_DIR.parent / "logs")

    # Threat Intel Feeds (Optional with simulated offline fallbacks)
    VIRUSTOTAL_API_KEY: str = ""
    URLHAUS_API_KEY: str = ""
    THREATFOX_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

def validate_security_posture(s: Settings):
    """Fail-safe security validator: Enforces credential entropy on production and unrecognized environments while allowing demo defaults in demo/development/testing/local."""
    env = s.ENVIRONMENT.lower()
    if env == "production" or env not in ("demo", "development", "testing", "local"):
        if "demo" in s.SECRET_KEY.lower() or "secret" in s.SECRET_KEY.lower():
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Production deployment requires a secure, "
                "cryptographically random SECRET_KEY injected via environment variable."
            )
        if "demo" in s.ADMIN_TOKEN.lower() or "secret" in s.ADMIN_TOKEN.lower() or s.ADMIN_TOKEN == "sentry_admin_demo_secret_2025":
            raise RuntimeError(
                "CRITICAL SECURITY CONFIGURATION ERROR: Production/non-demo deployment requires a secure, "
                "cryptographically random ADMIN_TOKEN injected via environment variable."
            )

# Execute security validation on module load
validate_security_posture(settings)

# Ensure evidence vault directory exists
Path(settings.EVIDENCE_VAULT_DIR).mkdir(parents=True, exist_ok=True)
