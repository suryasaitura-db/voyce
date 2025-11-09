"""
Local development configuration
Localhost settings and port configurations
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Server configuration
SERVER_CONFIG = {
    'host': os.getenv('HOST', 'localhost'),
    'port': int(os.getenv('PORT', 8000)),
    'debug': os.getenv('DEBUG', 'True').lower() == 'true',
    'reload': True,
}

# Available ports for local services
PORTS = {
    'api': 8000,
    'frontend': 3000,
    'docs': 8001,
    'metrics': 9090,
}

# Databricks configuration
DATABRICKS_CONFIG = {
    'profile': os.getenv('DATABRICKS_PROFILE', 'DEFAULT'),
    'use_serverless': True,
    'sql_serverless': True,
    'runtime_version': '15.4.x-scala2.12',
}

# CORS settings for local development
CORS_CONFIG = {
    'allow_origins': [
        'http://localhost:3000',
        'http://localhost:8000',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8000',
    ],
    'allow_credentials': True,
    'allow_methods': ['*'],
    'allow_headers': ['*'],
}

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
}
