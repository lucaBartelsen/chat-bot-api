# File: troubleshoot.py
# Path: fanfix-api/troubleshoot.py

#!/usr/bin/env python3
"""
Troubleshooting script for diagnosing OpenAPI schema issues in the FanFix API.
This script performs various checks on your FastAPI application to identify
potential problems with OpenAPI schema generation.
"""

import os
import sys
import json
import importlib.util
import inspect
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple

def print_header(text: str):
    """Print a section header"""
    print("\n" + "="*80)
    print(f"  {text}")
    print("="*80)

def print_success(text: str):
    """Print a success message"""
    print(f"✅ {text}")

def print_warning(text: str):
    """Print a warning message"""
    print(f"⚠️ {text}")

def print_error(text: str):
    """Print an error message"""
    print(f"❌ {text}")

def print_info(text: str):
    """Print an info message"""
    print(f"ℹ️ {text}")

def load_module_from_path(module_path: str, module_name: Optional[str] = None) -> Any:
    """Load a Python module from a file path"""
    if module_name is None:
        module_name = os.path.basename(module_path).replace(".py", "")
    
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if not spec or not spec.loader:
        print_error(f"Failed to load module spec from {module_path}")
        return None
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def check_pydantic_models(models_dir: str) -> List[str]:
    """Check Pydantic models for potential OpenAPI issues"""
    issues = []
    
    print_info(f"Scanning models in {models_dir}")
    
    # Find all Python files in the models directory
    model_files = list(Path(models_dir).glob("**/*.py"))
    
    for model_file in model_files:
        print_info(f"Checking {model_file}")
        try:
            # Load the module
            module = load_module_from_path(str(model_file))
            if not module:
                issues.append(f"Failed to load module: {model_file}")
                continue
            
            # Find all Pydantic models in the module
            from pydantic import BaseModel
            
            for name, obj in inspect.getmembers(module):
                if not inspect.isclass(obj):
                    continue
                
                # Skip if it's not a Pydantic model
                if not isinstance(obj, type) or not issubclass(obj, BaseModel) or obj == BaseModel:
                    continue
                
                print_info(f"  Checking model: {name}")
                
                try:
                    # Try to generate schema
                    schema = obj.schema()
                    
                    # Check for potential issues
                    for field_name, field in obj.__fields__.items():
                        # Check if field type is unsupported in OpenAPI
                        field_type = field.type_
                        field_type_name = str(field_type)
                        
                        # Check for Any type
                        if field_type_name == 'typing.Any':
                            issues.append(f"Model {name} has field '{field_name}' with type Any which may cause OpenAPI issues")
                        
                        # Check for complex generic types
                        if 'typing.Dict[' in field_type_name and 'Any' in field_type_name:
                            issues.append(f"Model {name} has field '{field_name}' with Dict[Any] which may cause OpenAPI issues")
                        
                        # Check for nested complex types
                        if 'typing.List[typing.Dict' in field_type_name:
                            issues.append(f"Model {name} has field '{field_name}' with nested complex type which may cause OpenAPI issues")
                        
                        # Check for optional field with default None
                        if field.default is None and not field.required:
                            # This is usually fine, but noting it
                            print_info(f"    Field '{field_name}' is optional with default None")
                        
                        # Check for circular dependencies
                        if name.lower() in field_type_name.lower():
                            issues.append(f"Model {name} may have circular dependency in field '{field_name}' with type {field_type_name}")
                    
                except Exception as e:
                    issues.append(f"Error generating schema for model {name}: {str(e)}")
        
        except Exception as e:
            issues.append(f"Error processing file {model_file}: {str(e)}")
    
    return issues

def check_router_conflicts(app_dir: str) -> List[str]:
    """Check for potential router conflicts"""
    issues = []
    
    print_info(f"Scanning for router conflicts in {app_dir}")
    
    # Find all router files
    router_files = list(Path(app_dir).glob("**/router.py")) + list(Path(app_dir).glob("**/*router*.py"))
    
    # Keep track of all routes
    all_routes = {}  # path -> [(file, method)]
    
    for router_file in router_files:
        print_info(f"Checking {router_file}")
        try:
            # Load the module
            module = load_module_from_path(str(router_file))
            if not module:
                issues.append(f"Failed to load module: {router_file}")
                continue
            
            # Find all routers
            from fastapi import APIRouter
            
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, APIRouter):
                    print_info(f"  Found router: {name}")
                    
                    # Check router routes
                    for route in getattr(obj, "routes", []):
                        path = getattr(route, "path", None)
                        methods = getattr(route, "methods", set())
                        
                        if path:
                            if path not in all_routes:
                                all_routes[path] = []
                            
                            for method in methods:
                                all_routes[path].append((str(router_file), method))
        
        except Exception as e:
            issues.append(f"Error processing router file {router_file}: {str(e)}")
    
    # Check for conflicts
    for path, routes in all_routes.items():
        methods = {}  # method -> file
        
        for file, method in routes:
            if method in methods:
                issues.append(f"Route conflict: {path} {method} defined in both {methods[method]} and {file}")
            else:
                methods[method] = file
    
    return issues

def check_fastapi_app(main_file: str) -> List[str]:
    """Check FastAPI app configuration"""
    issues = []
    
    print_info(f"Checking FastAPI app in {main_file}")
    
    try:
        # Load the main module
        module = load_module_from_path(main_file)
        if not module:
            issues.append(f"Failed to load main module: {main_file}")
            return issues
        
        # Find the FastAPI app
        from fastapi import FastAPI
        
        app = None
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FastAPI):
                app = obj
                break
        
        if not app:
            issues.append("FastAPI app not found in main module")
            return issues
        
        print_info(f"  Found FastAPI app: {app}")
        
        # Check app configuration
        if not getattr(app, "title", None):
            issues.append("FastAPI app missing title")
        
        if not getattr(app, "version", None):
            issues.append("FastAPI app missing version")
        
        # Check OpenAPI URL
        openapi_url = getattr(app, "openapi_url", None)
        if not openapi_url:
            issues.append("FastAPI app missing openapi_url")
        else:
            print_info(f"  OpenAPI URL: {openapi_url}")
        
        # Check custom OpenAPI function
        openapi_fn = getattr(app, "openapi", None)
        if not callable(openapi_fn):
            issues.append("FastAPI app missing custom openapi function")
        else:
            print_info(f"  Custom OpenAPI function: {openapi_fn.__name__}")
        
        # Check routes
        routes = getattr(app, "routes", [])
        if not routes:
            issues.append("FastAPI app has no routes")
        else:
            print_info(f"  Found {len(routes)} routes")
            
            # Check for duplicates
            paths = {}  # path -> [(method, endpoint)]
            
            for route in routes:
                path = getattr(route, "path", None)
                methods = getattr(route, "methods", set())
                endpoint = getattr(route, "endpoint", None)
                
                if path:
                    if path not in paths:
                        paths[path] = []
                    
                    for method in methods:
                        paths[path].append((method, endpoint))
            
            # Check for conflicts
            for path, route_methods in paths.items():
                methods = {}  # method -> endpoint
                
                for method, endpoint in route_methods:
                    if method in methods:
                        issues.append(f"Route conflict: {path} {method} defined multiple times")
                    else:
                        methods[method] = endpoint
        
    except Exception as e:
        issues.append(f"Error checking FastAPI app: {str(e)}")
    
    return issues

def check_openapi_schema(app_dir: str, main_file: str) -> List[str]:
    """Try to generate the OpenAPI schema and check for issues"""
    issues = []
    
    print_info("Attempting to generate OpenAPI schema")
    
    try:
        # Add app directory to path
        sys.path.insert(0, app_dir)
        
        # Load the main module
        module = load_module_from_path(main_file)
        if not module:
            issues.append(f"Failed to load main module: {main_file}")
            return issues
        
        # Find the FastAPI app
        from fastapi import FastAPI
        
        app = None
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FastAPI):
                app = obj
                break
        
        if not app:
            issues.append("FastAPI app not found in main module")
            return issues
        
        # Try to generate the OpenAPI schema
        try:
            from fastapi.openapi.utils import get_openapi
            
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            
            print_success("Successfully generated OpenAPI schema")
            print_info(f"  Schema version: {openapi_schema.get('openapi', 'unknown')}")
            print_info(f"  Paths: {len(openapi_schema.get('paths', {}))}")
            print_info(f"  Schemas: {len(openapi_schema.get('components', {}).get('schemas', {}))}")
            
            # Check for common issues
            if not openapi_schema.get("openapi"):
                issues.append("OpenAPI schema missing 'openapi' version")
            
            if not openapi_schema.get("info", {}).get("title"):
                issues.append("OpenAPI schema missing info.title")
            
            if not openapi_schema.get("info", {}).get("version"):
                issues.append("OpenAPI schema missing info.version")
            
            if not openapi_schema.get("paths"):
                issues.append("OpenAPI schema has no paths")
            
            # Save the schema to a file for inspection
            with open("openapi_schema.json", "w") as f:
                json.dump(openapi_schema, f, indent=2)
            print_info(f"  Schema saved to openapi_schema.json")
            
        except Exception as e:
            issues.append(f"Error generating OpenAPI schema: {str(e)}")
            import traceback
            issues.append(traceback.format_exc())
    
    except Exception as e:
        issues.append(f"Error checking OpenAPI schema: {str(e)}")
    
    finally:
        # Remove app directory from path
        if app_dir in sys.path:
            sys.path.remove(app_dir)
    
    return issues

def main():
    parser = argparse.ArgumentParser(description="Troubleshoot FastAPI OpenAPI schema issues")
    parser.add_argument("--app-dir", default="./app", help="Path to the app directory")
    parser.add_argument("--main-file", default="./main.py", help="Path to the main FastAPI file")
    parser.add_argument("--models-dir", default="./app", help="Path to the models directory")
    
    args = parser.parse_args()
    
    print_header("FanFix API OpenAPI Schema Troubleshooter")
    
    all_issues = []
    
    # Check Pydantic models
    print_header("Checking Pydantic Models")
    model_issues = check_pydantic_models(args.models_dir)
    all_issues.extend(model_issues)
    
    if model_issues:
        print_warning(f"Found {len(model_issues)} issues in Pydantic models")
        for issue in model_issues:
            print_error(f"  {issue}")
    else:
        print_success("No issues found in Pydantic models")
    
    # Check router conflicts
    print_header("Checking Router Conflicts")
    router_issues = check_router_conflicts(args.app_dir)
    all_issues.extend(router_issues)
    
    if router_issues:
        print_warning(f"Found {len(router_issues)} router conflicts")
        for issue in router_issues:
            print_error(f"  {issue}")
    else:
        print_success("No router conflicts found")
    
    # Check FastAPI app
    print_header("Checking FastAPI App")
    app_issues = check_fastapi_app(args.main_file)
    all_issues.extend(app_issues)
    
    if app_issues:
        print_warning(f"Found {len(app_issues)} issues in FastAPI app")
        for issue in app_issues:
            print_error(f"  {issue}")
    else:
        print_success("No issues found in FastAPI app")
    
    # Check OpenAPI schema
    print_header("Checking OpenAPI Schema")
    schema_issues = check_openapi_schema(args.app_dir, args.main_file)
    all_issues.extend(schema_issues)
    
    if schema_issues:
        print_warning(f"Found {len(schema_issues)} issues in OpenAPI schema")
        for issue in schema_issues:
            print_error(f"  {issue}")
    else:
        print_success("Successfully generated OpenAPI schema")
    
    # Summary
    print_header("Summary")
    
    if all_issues:
        print_warning(f"Found {len(all_issues)} total issues")
        
        # Suggest fixes
        print_header("Suggested Fixes")
        
        print_info("1. Check for circular dependencies in Pydantic models")
        print_info("2. Make sure all models use proper types (avoid Any types)")
        print_info("3. Ensure your FastAPI app has title, version, and description")
        print_info("4. Check for route conflicts")
        print_info("5. Try using a custom OpenAPI schema function")
        print_info("6. Consider using a minimal OpenAPI schema as fallback")
    else:
        print_success("No issues found! Your FastAPI app should generate a valid OpenAPI schema.")

if __name__ == "__main__":
    main()