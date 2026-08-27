from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pathlib import Path

from app.config import settings
from app.db.database import init_db, AsyncSessionLocal
from app.api.router import api_router
from app.api.v1.stats import seed_sample_emails

# Rate Limiter configuration (100 requests per minute burst capacity)
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])

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

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 1. Security Headers & Request Guard Middleware
@app.middleware("http")
async def security_headers_and_limits_middleware(request: Request, call_next):
    # Max Request Size Guard (25 MB)
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 26_214_400:
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"detail": "Payload exceeds maximum allowed size of 25MB."}
        )

    response: Response = await call_next(request)

    # Enterprise Security Headers (OWASP Top 10 recommendations)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' ws: wss: http: https:;"
    )

    return response

# 2. CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
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
