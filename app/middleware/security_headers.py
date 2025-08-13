"""Security headers middleware for FastAPI."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(request, response)

        return response

    def _add_security_headers(self, request: Request, response: Response) -> None:
        """Add essential security headers to the response."""
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Enable XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy - different policies for docs vs API
        if settings.CSP_ENABLED:
            if self._is_docs_endpoint(request):
                # Relaxed CSP for FastAPI documentation (Swagger UI)
                csp_policy = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                    "font-src 'self' https://fonts.gstatic.com; "
                    "img-src 'self' data: https:; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none';"
                )
            else:
                # Strict CSP for API endpoints
                csp_policy = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data: https:; "
                    "font-src 'self'; "
                    "connect-src 'self'; "
                    "frame-ancestors 'none';"
                )

            # Use report-only mode if configured
            header_name = "Content-Security-Policy-Report-Only" if settings.CSP_REPORT_ONLY else "Content-Security-Policy"
            response.headers[header_name] = csp_policy
        
        # Permissions Policy (formerly Feature Policy)
        permissions_policy = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "speaker=()"
        )
        response.headers["Permissions-Policy"] = permissions_policy
        
        # HSTS (HTTP Strict Transport Security) - only in production with HTTPS
        if settings.is_production and settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
        
        # Prevent caching of sensitive content
        if request.url.path.startswith("/api/v1/auth") or request.url.path.startswith("/api/v1/users"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

    def _is_docs_endpoint(self, request: Request) -> bool:
        """Check if the request is for API documentation endpoints."""
        docs_paths = ["/docs", "/redoc", "/openapi.json"]
        return any(request.url.path.startswith(path) for path in docs_paths)
