# File: main.py (updated)
# Path: fanfix-api/main.py

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma

from app.core.config import settings
from app.auth.router import router as auth_router
from app.api.creators import router as creators_router
from app.api.suggestions import router as suggestions_router
from app.middlewares import setup_middlewares

# Initialize Prisma client
prisma = Prisma()

# Create lifespan context manager instead of using on_event
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database on startup
    try:
        print("Connecting to database...")
        await prisma.connect()
        print("Database connection established successfully")
        
        # Initialize database if tables don't exist
        try:
            from app.core.database import init_db_pool
            db_pool = await init_db_pool()
            await db_pool.close()
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        # Don't exit here, continue to allow the app to start
        # This helps when deploying to environments where the DB might be temporarily unavailable
    
    yield
    
    # Disconnect from database on shutdown
    try:
        await prisma.disconnect()
        print("Database connection closed successfully")
    except Exception as e:
        print(f"Error disconnecting from database: {e}")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="ChatAssist API",
    description="AI-powered chat suggestions for creators",
    version="1.0.0",
    lifespan=lifespan
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include API routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(creators_router, prefix=settings.API_V1_STR)
app.include_router(suggestions_router, prefix=settings.API_V1_STR)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)