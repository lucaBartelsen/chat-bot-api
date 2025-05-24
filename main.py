# main.py - Updated with user management router

import time
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session, create_db_and_tables, check_database_health
from app.core.config import settings
from app.api import auth, creators, suggestions, examples, users  # Added users import
from app.middlewares import add_middlewares
from app.diagnostics import get_diagnostics_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    # Startup
    print("🚀 Starting up ChatsAssistant API...")
    
    try:
        # Initialize database tables
        print("🗄️ Initializing database...")
        await create_db_and_tables()
        print("✅ Database tables created/verified")
        
        # Check database health
        health_ok = await check_database_health()
        if health_ok:
            print("✅ Database connection healthy")
        else:
            print("⚠️ Database connection issues detected")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise
    
    print("✅ Application startup complete")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down ChatsAssistant API...")
    print("✅ Application shutdown complete")


# Initialize the FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for storing creator writing styles and generating AI-powered chat suggestions with comprehensive user management",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "clientId": "",
        "clientSecret": "",
    },
    redirect_slashes=False,
    lifespan=lifespan
)

# CORS origins - allow both local development and production
cors_origins = ["*"]

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

# Debug: Print CORS settings
print(f"🌐 CORS configured for origins: {cors_origins}")
print(f"🚫 Redirect slashes disabled")

# Add custom middlewares
add_middlewares(app)

# Include routers - Added users router
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(creators.router, prefix=f"{settings.API_V1_STR}/creators", tags=["Creators"])
app.include_router(suggestions.router, prefix=f"{settings.API_V1_STR}/suggestions", tags=["Suggestions"])
app.include_router(examples.router, prefix=f"{settings.API_V1_STR}/creators", tags=["Examples"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["User Management"])  # New users router

# Health check endpoint
@app.get("/health", tags=["Diagnostics"])
async def health_check():
    """Health check endpoint"""
    db_health = await check_database_health()
    
    return {
        "status": "ok" if db_health else "degraded",
        "timestamp": time.time(),
        "version": settings.VERSION,
        "database": "healthy" if db_health else "unhealthy",
        "environment": settings.ENVIRONMENT,
        "cors_origins": cors_origins,
        "redirect_slashes": False,
        "features": [
            "user_management",
            "creator_management", 
            "ai_suggestions",
            "style_examples",
            "response_examples",
            "vector_search",
            "admin_panel"
        ]
    }

# Diagnostics endpoints
@app.get("/diagnostics/info", tags=["Diagnostics"])
async def diagnostics_info():
    """Get system diagnostics information"""
    return get_diagnostics_info()

# Database diagnostics
@app.get("/diagnostics/database", tags=["Diagnostics"])
async def database_diagnostics(session: AsyncSession = Depends(get_session)):
    """Test database connectivity and operations"""
    try:
        # Test basic query
        result = await session.execute("SELECT 1 as test")
        test_result = result.scalar()
        
        # Test database-specific functions
        result = await session.execute("SELECT version()")
        db_version = result.scalar()
        
        # Test pgvector extension
        try:
            result = await session.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            vector_installed = result.scalar() is not None
        except:
            vector_installed = False
        
        # Test user management tables
        try:
            from app.models.user import User, UserPreference
            user_count_result = await session.execute("SELECT COUNT(*) FROM users")
            user_count = user_count_result.scalar()
            
            pref_count_result = await session.execute("SELECT COUNT(*) FROM user_preferences")
            pref_count = pref_count_result.scalar()
            
            user_tables_status = "healthy"
        except Exception as e:
            user_count = 0
            pref_count = 0
            user_tables_status = f"error: {str(e)}"
        
        return {
            "status": "healthy",
            "test_query": test_result,
            "database_version": db_version,
            "pgvector_installed": vector_installed,
            "user_management": {
                "status": user_tables_status,
                "users_count": user_count,
                "preferences_count": pref_count
            },
            "database_url": settings.DATABASE_URL.split("@")[1] if "@" in settings.DATABASE_URL else "configured",
            "timestamp": time.time()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }

# API routes information
@app.get("/diagnostics/routes", tags=["Diagnostics"])
async def list_routes():
    """List all available API routes"""
    routes = []
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", ""),
            "name": getattr(route, "name", ""),
            "methods": list(getattr(route, "methods", [])),
        }
        routes.append(route_info)
    
    # Group routes by category
    route_categories = {
        "authentication": [r for r in routes if "/auth" in r["path"]],
        "user_management": [r for r in routes if "/users" in r["path"]],
        "creators": [r for r in routes if "/creators" in r["path"]],
        "suggestions": [r for r in routes if "/suggestions" in r["path"]],
        "diagnostics": [r for r in routes if "/diagnostics" in r["path"] or "/health" in r["path"]],
        "other": [r for r in routes if not any(x in r["path"] for x in ["/auth", "/users", "/creators", "/suggestions", "/diagnostics", "/health"])]
    }
    
    return {
        "routes_by_category": route_categories,
        "total_routes": len(routes),
        "timestamp": time.time()
    }

# OpenAPI schema
@app.get("/diagnostics/openapi", tags=["Diagnostics"])
async def get_openapi_schema():
    """Get the OpenAPI schema"""
    return app.openapi()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )