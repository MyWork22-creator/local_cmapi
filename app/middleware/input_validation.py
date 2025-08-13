"""Input validation middleware for FastAPI."""
import json
from typing import Any, Dict
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.input_validation import SecurityValidator, InputValidationError


class InputValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate all incoming request data for security threats."""
    
    def __init__(self, app, enable_strict_validation: bool = True):
        super().__init__(app)
        self.enable_strict_validation = enable_strict_validation
        
        # Endpoints that should skip validation (e.g., file uploads, webhooks)
        self.skip_validation_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/favicon.ico",
            "/health",
            "/"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain paths
        if request.url.path in self.skip_validation_paths:
            return await call_next(request)
        
        # Skip validation for GET requests (query params are handled separately)
        if request.method == "GET":
            await self._validate_query_params(request)
            return await call_next(request)
        
        # Validate request body for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            await self._validate_request_body(request)
        
        response = await call_next(request)
        return response
    
    async def _validate_query_params(self, request: Request) -> None:
        """Validate query parameters."""
        try:
            for key, value in request.query_params.items():
                if isinstance(value, str):
                    # Apply basic security validations
                    SecurityValidator.validate_against_sql_injection(value)
                    SecurityValidator.validate_against_xss(value)
                    SecurityValidator.validate_against_path_traversal(value)
                    
                    # Validate search queries more strictly
                    if key.lower() in ['search', 'query', 'q', 'filter']:
                        SecurityValidator.validate_search_query(value)
        
        except InputValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid query parameter '{key}': {str(e)}"
            )
    
    async def _validate_request_body(self, request: Request) -> None:
        """Validate request body content."""
        try:
            # Skip validation for certain endpoints that might need reserved usernames
            skip_validation_endpoints = {
                "/api/v1/login",  # Allow login with any username
                "/api/v1/refresh",  # Token refresh
                "/docs",
                "/redoc",
                "/openapi.json"
            }

            if any(request.url.path.startswith(endpoint) for endpoint in skip_validation_endpoints):
                return

            # Get the request body
            body = await request.body()
            if not body:
                return

            # Try to parse as JSON
            try:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = json.loads(body)
                    self._validate_json_data(data, request.url.path)
                elif "application/x-www-form-urlencoded" in content_type:
                    # For form data, we'll let FastAPI handle parsing
                    # and validate in the endpoint
                    pass
            except json.JSONDecodeError:
                # If it's not valid JSON, skip validation
                pass

        except InputValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid request data: {str(e)}"
            )
    
    def _validate_json_data(self, data: Any, request_path: str = "") -> None:
        """Recursively validate JSON data."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    self._validate_string_value(key, value, request_path)
                elif isinstance(value, (dict, list)):
                    self._validate_json_data(value, request_path)
        elif isinstance(data, list):
            for item in data:
                self._validate_json_data(item, request_path)
    
    def _validate_string_value(self, key: str, value: str, request_path: str = "") -> None:
        """Validate individual string values."""
        # Skip validation for certain fields that might contain special characters
        skip_fields = {'password', 'token', 'refresh_token', 'access_token'}
        if key.lower() in skip_fields:
            return

        # Apply security validations based on field type
        if key.lower() in ['username', 'user_name']:
            # For login requests, use less restrictive validation
            if "/login" in request_path:
                SecurityValidator.validate_username_for_login(value)
            else:
                # For user creation/update, apply full validation
                SecurityValidator.validate_username(value)
        elif key.lower() in ['email']:
            SecurityValidator.validate_email(value)
        elif key.lower() in ['name', 'role_name']:
            SecurityValidator.validate_role_name(value)
        elif key.lower() in ['description']:
            SecurityValidator.validate_description(value)
        elif key.lower() in ['search', 'query', 'filter']:
            SecurityValidator.validate_search_query(value)
        else:
            # Apply basic security checks for all other string fields
            SecurityValidator.validate_against_sql_injection(value)
            SecurityValidator.validate_against_xss(value)
            SecurityValidator.validate_against_path_traversal(value)

            # Check for excessively long strings
            if len(value) > 1000:
                raise InputValidationError(f"Field '{key}' exceeds maximum length")


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request size and prevent DoS attacks."""
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_request_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Request size {content_length} exceeds maximum allowed size {self.max_request_size}"
                    )
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Content-Length header"
                )
        
        response = await call_next(request)
        return response


class SecurityHeadersValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate security-related headers."""
    
    async def dispatch(self, request: Request, call_next):
        # Validate User-Agent header
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 500:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User-Agent header too long"
            )
        
        # Check for suspicious patterns in headers
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
        ]
        
        for header_name, header_value in request.headers.items():
            if isinstance(header_value, str):
                for pattern in suspicious_patterns:
                    if pattern.lower() in header_value.lower():
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Suspicious content detected in header '{header_name}'"
                        )
        
        response = await call_next(request)
        return response
