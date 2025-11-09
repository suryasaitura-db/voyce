"""
Voyce - Voice Feedback Platform
Main application entry point for local development
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import uvicorn

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Import the FastAPI app from backend
from backend.app.main import app

# Configuration
HOST = os.getenv('HOST', 'localhost')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

def main():
    """Run the application locally"""
    print(f"Starting Voyce application on http://{HOST}:{PORT}")
    print(f"Debug mode: {DEBUG}")
    print(f"Databricks profile: {os.getenv('DATABRICKS_PROFILE', 'DEFAULT')}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info" if DEBUG else "warning"
    )

if __name__ == "__main__":
    main()
