#!/usr/bin/env python3
"""
Sample Miner API - Server Launcher

Quick start script to launch the FastAPI server with uvicorn.

Usage:
    python run.py                    # Development mode
    python run.py --production       # Production mode with multiple workers
    python run.py --port 8080        # Custom port
    python run.py --help             # Show all options

Requirements:
    - Python 3.10+
    - Install dependencies: pip install -r requirements-minimal.txt
    - Configure .env file with your API keys
    - Database is created automatically on first run
"""

import argparse
import os
import sys
from pathlib import Path

def main():
    """Launch the FastAPI server with uvicorn."""
    
    # Load environment variables from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Get defaults from environment variables
    default_host = os.getenv("HOST", "0.0.0.0")
    default_port = int(os.getenv("PORT", "8001"))
    
    parser = argparse.ArgumentParser(
        description="Sample Miner API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py                    # Development mode (auto-reload)
  python run.py --production       # Production mode (4 workers)
  python run.py --port 8080        # Custom port
  python run.py --host 0.0.0.0     # Listen on all interfaces
  python run.py --workers 8        # Custom worker count
        """
    )
    
    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Host to bind (default from .env: {default_host})"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=default_port,
        help=f"Port to bind (default from .env: {default_port})"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of worker processes (default: 1 for dev, 4 for production)"
    )
    
    parser.add_argument(
        "--production",
        action="store_true",
        help="Run in production mode (multiple workers, no auto-reload)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development only)"
    )
    
    args = parser.parse_args()
    
    # Check if database exists (it will be created automatically if missing)
    db_path = Path("./data/miner_api.db")
    if not db_path.exists():
        print("ℹ️  Database not found - will be created automatically on first request")
        print()
    
    # Check if .env file exists
    env_path = Path(".env")
    if not env_path.exists():
        print("⚠️  WARNING: .env file not found!")
        print("   Please copy .env.example to .env and configure your API keys")
        print()
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Startup cancelled. Please create .env file first.")
            sys.exit(1)
    
    # Set production defaults
    if args.production:
        if args.workers == 1:  # User didn't specify workers
            args.workers = 4
        reload = False
    else:
        reload = args.reload
    
    # Build uvicorn command
    try:
        import uvicorn
    except ImportError:
        print("❌ ERROR: uvicorn not found!")
        print("   Please install dependencies:")
        print("   pip install -r requirements-minimal.txt")
        sys.exit(1)
    
    # Display startup info
    print("=" * 60)
    print("🚀 Sample Miner API Server")
    print("=" * 60)
    print(f"Host:        {args.host}{' (from .env)' if args.host == default_host else ' (from --host)'}")
    print(f"Port:        {args.port}{' (from .env)' if args.port == default_port else ' (from --port)'}")
    print(f"Workers:     {args.workers}")
    print(f"Mode:        {'Production' if args.production else 'Development'}")
    print(f"Auto-reload: {'Yes' if reload else 'No'}")
    print(f"Database:    {db_path.absolute()}")
    print("=" * 60)
    print()
    print(f"📡 API will be available at: http://{args.host}:{args.port}")
    print(f"📚 API docs at: http://{args.host}:{args.port}/docs")
    print(f"🔧 Health check: http://{args.host}:{args.port}/health")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Launch uvicorn
    try:
        uvicorn.run(
            "src.api.main:app",
            host=args.host,
            port=args.port,
            workers=args.workers if args.production else 1,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
