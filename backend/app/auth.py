import hmac
from typing import Optional
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

# OpenAPI Bearer Security Scheme (D2)
bearer_scheme = HTTPBearer(
    auto_error=False,
    description="Enter the SENTRY DFIR Operator Bearer Token (configured via SENTRY_API_TOKEN)."
)

async def require_api_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> str:
    """
    Enforces Bearer authentication on all writable forensic endpoints (GAP-006 / D2).
    Requires a valid token matching SENTRY_API_TOKEN in the Authorization header.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "UNAUTHORIZED",
                "message": "Missing required Bearer authentication token. Provide 'Authorization: Bearer <SENTRY_API_TOKEN>' header."
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials.strip()
    expected_token = settings.SENTRY_API_TOKEN.strip()

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "INVALID_TOKEN",
                "message": "Invalid Bearer authentication token. Access denied to forensic write operations."
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token
