# File: main.py (updated with diagnostics)
# Path: fanfix-api/main.py

import os
import sys
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prisma import Prisma
from fastapi.openapi.utils import get_openapi
import logging

from app.core.config import settings
from app.auth.router import router as auth_router
from app.api.creators import router as creators_router
from app.api.suggestions import router as suggestions_router
from app.middlewares import setup_middlewares
from app.diagnostics import router as diagnostics_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Prisma client
prisma = Prisma()

# Create lifespan context manager instead of using on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database on startup
    try:
        logger.info("Connecting to database...")
        await prisma.connect()
        logger.info("Database connection established successfully")
        
        # Initialize database if tables don't exist
        try:
            from app.core.database import init_db_pool
            db_pool = await init_db_pool()
            await db_pool.close()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        # Don't exit here, continue to allow the app to start
        # This helps when deploying to environments where the DB might be temporarily unavailable
    
    yield
    
    # Disconnect from database on shutdown
    try:
        await prisma.disconnect()
        logger.info("Database connection closed successfully")
    except Exception as e:
        logger.error(f"Error disconnecting from database: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="ChatAssist API",
    description="AI-powered chat suggestions for creators",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up custom middlewares
setup_middlewares(app)

# Add exception handler for OpenAPI rendering errors
@app.exception_handler(Exception)
async def openapi_exception_handler(request: Request, exc: Exception):
    # Check if this is a request for OpenAPI schema
    if request.url.path in ["/openapi.json", "/docs", "/redoc"]:
        logger.error(f"Error generating OpenAPI schema: {exc}")
        
        # For OpenAPI JSON requests, return a minimal valid schema
        if request.url.path == "/openapi.json":
            return JSONResponse(
                status_code=200,
                content={
                    "openapi": "3.0.2",
                    "info": {
                        "title": "ChatAssist API (Minimal Schema)",
                        "description": "Error generating full schema, displaying minimal version.",
                        "version": "1.0.0"
                    },
                    "paths": {}
                }
            )
    
    # For other exceptions, let FastAPI handle it
    raise exc

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(creators_router, prefix=settings.API_V1_STR)
app.include_router(suggestions_router, prefix=settings.API_V1_STR)

# Include diagnostics router (no API prefix to make it easier to access)
app.include_router(diagnostics_router)

# Custom simplified OpenAPI schema generator for stability
def simplified_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    try:
        # Try to generate the full schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    except Exception as e:
        logger.error(f"Error generating full OpenAPI schema: {e}")
        
        # Fall back to a minimal schema
        minimal_schema = {
            "openapi": "3.0.2",
            "info": {
                "title": f"{app.title} (Simplified Schema)",
                "description": f"{app.description}\n\nNote: This is a simplified schema due to generation issues.",
                "version": app.version
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add basic paths for main endpoints
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                path = route.path
                methods = route.methods
                
                if path not in minimal_schema["paths"]:
                    minimal_schema["paths"][path] = {}
                
                for method in methods:
                    method_lower = method.lower()
                    minimal_schema["paths"][path][method_lower] = {
                        "summary": getattr(route, "name", "Endpoint"),
                        "responses": {
                            "200": {
                                "description": "Successful response"
                            }
                        }
                    }
        
        app.openapi_schema = minimal_schema
        return app.openapi_schema

# Set simplified OpenAPI schema generator
app.openapi = simplified_openapi

# Add redirect from root to docs
@app.get("/", include_in_schema=False)
async def redirect_to_docs():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

# Add a route to force reload OpenAPI schema
@app.get("/reload-openapi", include_in_schema=False)
async def reload_openapi():
    app.openapi_schema = None
    return {"status": "OpenAPI schema reloaded"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)