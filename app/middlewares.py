import time
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = request.headers.get("X-Request-ID", str(time.time()))
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Start timer
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"Response {request_id}: {response.status_code} (took {process_time:.4f}s)")
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(f"Error {request_id}: {str(e)} (took {process_time:.4f}s)")
            raise

def add_middlewares(app: FastAPI) -> None:
    """
    Add middleware to the FastAPI application
    """
    app.add_middleware(LoggingMiddleware)