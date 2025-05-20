# File: app/diagnostics.py
# Path: fanfix-api/app/diagnostics.py

import json
import logging
import traceback
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create diagnostics router
router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

class DiagnosticInfo(BaseModel):
    """Model for diagnostic information"""
    app_version: str
    python_version: str
    fastapi_version: str
    prisma_version: str
    environment: str
    database_connected: bool
    routes_count: int
    openapi_schema_size: int
    openapi_errors: Optional[List[str]] = None

@router.get("/info", response_model=DiagnosticInfo)
async def get_diagnostic_info(request: Request) -> DiagnosticInfo:
    """
    Get diagnostic information about the API
    """
    import sys
    import os
    import fastapi
    import prisma

    app = request.app
    
    # Check database connection
    from prisma import Prisma
    prisma_client = Prisma()
    db_connected = False
    try:
        await prisma_client.connect()
        db_connected = True
        await prisma_client.disconnect()
    except Exception as e:
        logger.error(f"Database connection error: {e}")
    
    # Get OpenAPI schema size and check for errors
    openapi_schema_size = 0
    openapi_errors = []
    try:
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        openapi_schema_size = len(json.dumps(schema))
    except Exception as e:
        logger.error(f"OpenAPI schema error: {e}")
        openapi_errors.append(str(e))
        openapi_errors.append(traceback.format_exc())
    
    return DiagnosticInfo(
        app_version=app.version,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        fastapi_version=fastapi.__version__,
        prisma_version=getattr(prisma, "__version__", "unknown"),
        environment=os.environ.get("ENVIRONMENT", "production"),
        database_connected=db_connected,
        routes_count=len(app.routes),
        openapi_schema_size=openapi_schema_size,
        openapi_errors=openapi_errors if openapi_errors else None
    )

@router.get("/openapi", response_class=JSONResponse)
async def get_raw_openapi(request: Request) -> JSONResponse:
    """
    Get the raw OpenAPI schema for debugging
    """
    app = request.app
    try:
        # Try to generate the schema directly
        schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        return JSONResponse(schema)
    except Exception as e:
        logger.error(f"Error generating OpenAPI schema: {e}")
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

@router.get("/routes", response_class=JSONResponse)
async def get_routes(request: Request) -> JSONResponse:
    """
    Get a list of all routes registered in the app
    """
    app = request.app
    routes = []
    
    for route in app.routes:
        route_info = {
            "path": getattr(route, "path", str(route)),
            "name": getattr(route, "name", None),
            "methods": getattr(route, "methods", None),
            "endpoint": str(getattr(route, "endpoint", None)),
            "response_model": str(getattr(route, "response_model", None)),
        }
        routes.append(route_info)
    
    return JSONResponse({"routes": routes})

@router.get("/docs-fallback", response_class=HTMLResponse)
async def get_docs_fallback() -> HTMLResponse:
    """
    A fallback documentation page when OpenAPI docs fail
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ChatAssist API - Fallback Documentation</title>
        <style>
            body {
                font-family: sans-serif;
                margin: 0;
                padding: 0;
                color: #333;
                line-height: 1.6;
            }
            .container {
                width: 80%;
                margin: 0 auto;
                padding: 2rem;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 2rem;
            }
            h2 {
                color: #3498db;
                margin-top: 2rem;
                border-bottom: 1px solid #eee;
                padding-bottom: 0.5rem;
            }
            pre {
                background: #f8f8f8;
                padding: 1rem;
                border-radius: 5px;
                overflow-x: auto;
            }
            .endpoint {
                background: #f8f8f8;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 5px;
                border-left: 4px solid #3498db;
            }
            .method {
                display: inline-block;
                padding: 0.25rem 0.5rem;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 0.5rem;
            }
            .get { background: #61affe; color: white; }
            .post { background: #49cc90; color: white; }
            .put { background: #fca130; color: white; }
            .delete { background: #f93e3e; color: white; }
            .patch { background: #50e3c2; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>ChatAssist API - Fallback Documentation</h1>
            <p>This is a fallback documentation page for the ChatAssist API. The OpenAPI documentation is currently unavailable.</p>
            
            <h2>Authentication</h2>
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/auth/jwt/login</code>
                <p>Login and get an access token</p>
                <pre>
{
  "username": "user@example.com",
  "password": "password"
}
                </pre>
            </div>
            
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/auth/register</code>
                <p>Register a new user</p>
                <pre>
{
  "email": "user@example.com",
  "password": "password"
}
                </pre>
            </div>
            
            <h2>Creators</h2>
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/creators</code>
                <p>Get all creators</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/creators/{creator_id}</code>
                <p>Get a specific creator</p>
            </div>
            
            <h2>Suggestions</h2>
            <div class="endpoint">
                <span class="method post">POST</span> <code>/api/suggestions</code>
                <p>Get suggestions for a fan message</p>
                <pre>
{
  "message": "Hello, how are you?",
  "chat_history": [],
  "regenerate": false
}
                </pre>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/api/suggestions/stats</code>
                <p>Get statistics about stored conversations</p>
            </div>
            
            <h2>Diagnostics</h2>
            <div class="endpoint">
                <span class="method get">GET</span> <code>/diagnostics/info</code>
                <p>Get diagnostic information about the API</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/diagnostics/openapi</code>
                <p>Get the raw OpenAPI schema for debugging</p>
            </div>
            
            <div class="endpoint">
                <span class="method get">GET</span> <code>/diagnostics/routes</code>
                <p>Get a list of all routes registered in the app</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.get("/fix-openapi")
async def fix_openapi(request: Request) -> JSONResponse:
    """
    Attempt to fix OpenAPI schema issues
    """
    app = request.app
    
    # Save the original schema
    original_schema = app.openapi_schema
    
    # Create a minimal schema to ensure documentation works
    minimal_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": app.title,
            "version": app.version,
            "description": app.description
        },
        "paths": {},
        "components": {
            "schemas": {}
        }
    }
    
    # Try to build up the schema progressively, adding only working routes
    for route in app.routes:
        try:
            # Skip built-in routes that might cause issues
            if route.path.startswith(("/docs", "/redoc", "/openapi.json")):
                continue
                
            partial_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=[route],
            )
            
            # If we got this far, the route is valid
            for path, path_item in partial_schema.get("paths", {}).items():
                minimal_schema["paths"][path] = path_item
                
            # Add any schemas
            for name, schema in partial_schema.get("components", {}).get("schemas", {}).items():
                minimal_schema["components"]["schemas"][name] = schema
                
        except Exception as e:
            logger.error(f"Error adding route {route.path} to schema: {e}")
    
    # Set the minimal schema
    app.openapi_schema = minimal_schema
    
    return JSONResponse({
        "status": "success",
        "message": "Applied minimal OpenAPI schema",
        "route_count": len(minimal_schema["paths"]),
        "schema_count": len(minimal_schema["components"]["schemas"])
    })

@router.get("/check-models")
async def check_models() -> JSONResponse:
    """
    Check all models for OpenAPI compatibility issues
    """
    import inspect
    import sys
    from app.auth import models as auth_models
    from app.models import creator as creator_models
    from app.models import suggestion as suggestion_models
    from pydantic import BaseModel
    
    model_modules = [auth_models, creator_models, suggestion_models]
    model_issues = []
    
    # Check all models in all modules
    for module in model_modules:
        for name, obj in inspect.getmembers(module):
            # Only check classes that are Pydantic models
            if inspect.isclass(obj) and issubclass(obj, BaseModel) and obj != BaseModel:
                try:
                    # Check if schema can be generated
                    schema = obj.schema()
                    
                    # Check for known problematic fields
                    for field_name, field in obj.__fields__.items():
                        # Check if field type is valid for OpenAPI
                        field_type = field.type_
                        if field_type is Any:
                            model_issues.append(f"Model {name} has field {field_name} with type Any")
                except Exception as e:
                    model_issues.append(f"Model {name} has schema error: {str(e)}")
    
    return JSONResponse({
        "status": "success" if not model_issues else "issues_found",
        "model_issues": model_issues
    })