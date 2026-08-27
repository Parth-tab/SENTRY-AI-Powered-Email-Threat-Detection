from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.db.database import init_db, AsyncSessionLocal
from app.api.router import api_router
from app.api.v1.stats import seed_sample_emails

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schemas on startup
    await init_db()
    
    # Auto-seed sample scenarios into local DB
    async with AsyncSessionLocal() as session:
        try:
            await seed_sample_emails(session)
        except Exception as e:
            print(f"Startup seeding notice: {e}")
            
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Evidentiary-Grade Email Threat Detection, GeoLocation & Forensic Intelligence Platform (SIH 2025 PS ID 26106)",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "SENTRY Forensic Backend",
        "version": settings.VERSION,
        "rfc_compliance": ["RFC 5321", "RFC 5322", "RFC 7208 (SPF)", "RFC 6376 (DKIM)", "RFC 7489 (DMARC)", "RFC 3227 (Evidence)"]
    }

@app.get("/", tags=["Root"])
async def root():
    return {
        "platform": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
        "status": "OPERATIONAL"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
