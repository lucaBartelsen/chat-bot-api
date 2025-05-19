# File: app/middlewares.py
# Path: fanfix-api/app/middlewares.py

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
from typing import Callable
import json

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request information and timing
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get request details
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request details
            logger.info(
                f"{client_host} - {method} {path} {response.status_code} - "
                f"{process_time:.4f}s"
            )
            
            # Add process time header
            response.headers["X-Process-Time"] = f"{process_time:.4f}"
            
            return response
        except Exception as e:
            # Log error
            logger.error(
                f"{client_host} - {method} {path} - Error: {str(e)}"
            )
            raise

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    For production, consider using Redis for distributed rate limiting
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # client_ip -> [(timestamp, count), ...]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Clean old records
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                record for record in self.requests[client_ip]
                if current_time - record[0] < self.window_seconds
            ]
        
        # Check if rate limit exceeded
        requests_count = sum(record[1] for record in self.requests.get(client_ip, []))
        
        if requests_count >= self.max_requests:
            # Rate limit exceeded
            return Response(
                content=json.dumps({
                    "detail": "Rate limit exceeded",
                    "status_code": 429
                }),
                status_code=429,
                media_type="application/json"
            )
        
        # Update request count
        if client_ip not in self.requests:
            self.requests[client_ip] = [(current_time, 1)]
        else:
            self.requests[client_ip].append((current_time, 1))
        
        return await call_next(request)

def setup_middlewares(app):
    """
    Configure and add middlewares to the FastAPI app
    """
    # Add CORS middleware first (already added in main.py)
    
    # Add logging middleware
    app.add_middleware(LoggingMiddleware)
    
    # Add rate limiting middleware
    # Commented out because we're using FastAPI's built-in rate limiting
    # app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)