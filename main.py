"""
Voyce Application - Main Entry Point
Configured for local development with localhost settings
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Configuration
HOST = os.getenv('HOST', 'localhost')
PORT = int(os.getenv('PORT', 8000))
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')

# Initialize FastAPI app
app = FastAPI(
    title="Voyce",
    description="Databricks-powered application",
    version="1.0.0",
    debug=DEBUG
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": "voyce",
        "environment": os.getenv('ENVIRONMENT', 'development'),
        "databricks_profile": os.getenv('DATABRICKS_PROFILE', 'DEFAULT')
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "ok",
        "host": HOST,
        "port": PORT,
        "debug": DEBUG
    }

@app.get("/api/v1/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": os.getenv('API_VERSION', 'v1'),
        "status": "operational"
    }

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
