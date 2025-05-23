import time
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlmodel import Session

from app.core.database import init_db, get_session
from app.core.config import settings
from app.api import auth, creators, suggestions, examples
from app.middlewares import add_middlewares
from app.diagnostics import get_diagnostics_info

# Initialize the FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for storing creator writing styles and generating AI-powered chat suggestions",
    version="0.1.1",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "clientId": "",
        "clientSecret": "",
    }
)

# Add CORS middleware - SEHR PERMISSIV für Development
# Lass FastAPI alle CORS-Headers handhaben
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Alle Origins erlauben
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # Alle Headers (inkl. Authorization)
    expose_headers=["*"], # Alle Response-Headers freigeben
)

# Debug: Print CORS settings
print(f"🌐 CORS configured to allow all origins")
print(f"🌐 Original CORS setting from config: {settings.CORS_ORIGINS}")

# Add custom middlewares
add_middlewares(app)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    init_db()

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(creators.router, prefix=f"{settings.API_V1_STR}/creators", tags=["Creators"])
app.include_router(suggestions.router, prefix=f"{settings.API_V1_STR}/suggestions", tags=["Suggestions"])
app.include_router(examples.router, prefix=f"{settings.API_V1_STR}/creators", tags=["Examples"])

# Health check endpoint
@app.get("/health", tags=["Diagnostics"])
async def health_check():
    return {
        "status": "ok",
        "timestamp": time.time(),
        "version": app.version,
        "cors_enabled": "All origins allowed",
    }

# Diagnostics endpoints
@app.get("/diagnostics/info", tags=["Diagnostics"])
async def diagnostics_info():
    return get_diagnostics_info()

# API routes information
@app.get("/diagnostics/routes", tags=["Diagnostics"])
async def list_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else [],
        })
    return routes

# OpenAPI schema
@app.get("/diagnostics/openapi", tags=["Diagnostics"])
async def get_openapi():
    return app.openapi()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)