#!/bin/bash
# Local development script for Voyce application

set -e

echo "Starting Voyce Local Development Server"
echo "========================================"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Check if .env exists, if not copy from .env.example
if [ ! -f ".env" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if port is available
PORT=${PORT:-8000}
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "Warning: Port $PORT is already in use"
    echo "Please stop the service or change PORT in .env"
    exit 1
fi

echo ""
echo "Configuration:"
echo "  Host: ${HOST:-localhost}"
echo "  Port: $PORT"
echo "  Debug: ${DEBUG:-True}"
echo "  Databricks Profile: ${DATABRICKS_PROFILE:-DEFAULT}"
echo ""

# Run the application
echo "Starting server..."
echo "Access the application at: http://${HOST:-localhost}:$PORT"
echo "API docs at: http://${HOST:-localhost}:$PORT/docs"
echo ""

python main.py
