"""
FastAPI main application for voice feedback platform.
Includes CORS, middleware, routes, health checks, and metrics.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import time
import logging

from app.config import settings
from app.database import init_db, close_db
from routers import auth, submissions, analytics
from utils.logger import setup_logger

# Setup logger
logger = setup_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("Starting voice feedback platform backend")
    logger.info(f"Database backend: {settings.DB_BACKEND}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    await init_db()

    yield

    # Shutdown
    logger.info("Shutting down voice feedback platform backend")
    await close_db()


app = FastAPI(
    title="Voice Feedback Platform API",
    description="Backend API for voice feedback collection, transcription, and analysis",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)


# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "chrome-extension://*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Request logging and metrics middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests and track metrics."""
    start_time = time.time()

    # Log request
    logger.info(
        f"Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
        }
    )

    # Process request
    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        logger.error(f"Request failed: {str(e)}", exc_info=True)
        status_code = 500
        response = JSONResponse(
            status_code=status_code,
            content={"detail": "Internal server error"}
        )

    # Calculate duration
    duration = time.time() - start_time

    # Update metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=status_code
    ).inc()

    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    # Log response
    logger.info(
        f"Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": status_code,
            "duration": f"{duration:.3f}s",
        }
    )

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(
        f"Validation error",
        extra={
            "url": str(request.url),
            "errors": exc.errors()
        }
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(submissions.router, prefix="/api/submissions", tags=["Submissions"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": settings.DB_BACKEND,
        "version": "1.0.0"
    }


# Metrics endpoint
@app.get("/metrics", tags=["System"])
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint."""
    return {
        "message": "Voice Feedback Platform API",
        "version": "1.0.0",
        "docs": "/api/docs" if settings.ENVIRONMENT != "production" else None
    }
