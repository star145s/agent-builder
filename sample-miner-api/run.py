#!/usr/bin/env python3
"""
Main entry point for the Sample Miner API.
This script ensures proper module imports from the src/ directory.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Now import and run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    from src.core.config import settings
    
    # Import the app from the new location
    from src.api.main import app
    
    print(f"Starting Sample Miner API on {settings.host}:{settings.miner_port}")
    print(f"Docs available at: http://{settings.host}:{settings.miner_port}/docs")
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.miner_port,
        log_level=settings.log_level.lower()
    )
