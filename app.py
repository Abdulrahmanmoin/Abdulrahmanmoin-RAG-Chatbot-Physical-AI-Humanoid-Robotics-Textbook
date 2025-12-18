#!/usr/bin/env python3
"""
Start script for the RAG Chatbot API
This script starts the FastAPI application using uvicorn
"""
import uvicorn
import os
import sys
from pathlib import Path


def main():
    # Add the backend/src directory to the Python path so imports work correctly
    src_path = Path(__file__).parent / "src"
    sys.path.insert(0, str(src_path))

    # Import settings to get configuration
    try:
        from src.config.settings import settings
    except ImportError:
        print("Error: Could not import settings. Make sure all dependencies are installed.")
        print("Run 'pip install -r requirements.txt' first.")
        sys.exit(1)

    # Determine host and port
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    print(f"Starting RAG Chatbot API server...")
    print(f"Environment: {settings.app_env}")
    print(f"Debug mode: {settings.debug}")
    print(f"Server will run on {host}:{port}")

    # Run the server
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=settings.app_env == "development",  # Enable auto-reload in development
        log_level=settings.log_level.lower(),
        reload_dirs=["src"] if settings.app_env == "development" else None,
    )


if __name__ == "__main__":
    main()