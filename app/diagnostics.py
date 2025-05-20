import os
import sys
import time
import platform
import psutil
from typing import Dict, Any
from importlib.metadata import distributions

def get_system_info() -> Dict[str, Any]:
    """
    Get system information for diagnostics
    """
    return {
        "os": {
            "name": os.name,
            "platform": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
        },
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler(),
        },
        "cpu": {
            "count": psutil.cpu_count(logical=False),
            "logical_count": psutil.cpu_count(logical=True),
            "usage": psutil.cpu_percent(interval=1),
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "used": psutil.virtual_memory().used,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {
            "total": psutil.disk_usage('/').total,
            "used": psutil.disk_usage('/').used,
            "free": psutil.disk_usage('/').free,
            "percent": psutil.disk_usage('/').percent,
        },
        "process": {
            "pid": os.getpid(),
            "memory_info": dict(psutil.Process(os.getpid()).memory_info()._asdict()),
            "cpu_percent": psutil.Process(os.getpid()).cpu_percent(interval=1),
            "threads": psutil.Process(os.getpid()).num_threads(),
        },
        "timestamp": time.time(),
    }

def get_dependencies_info() -> Dict[str, str]:
    """
    Get information about installed dependencies using importlib.metadata
    """
    dependencies = {}
    for dist in distributions():
        dependencies[dist.metadata["Name"]] = dist.version
    
    return dependencies

def get_diagnostics_info() -> Dict[str, Any]:
    """
    Get complete diagnostics information
    """
    return {
        "system": get_system_info(),
        "dependencies": get_dependencies_info(),
    }