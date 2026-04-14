"""
Security response headers middleware.

Adds defence-in-depth HTTP security headers to every response.
These headers have no equivalent in the COBOL/CICS system; they are
new security controls required for any public-facing web application.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject security headers into every HTTP response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        # Disable legacy browser XSS filter (can cause issues; CSP is the modern control)
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )
        # Note: HSTS is set at the nginx/load-balancer level in production
        return response
