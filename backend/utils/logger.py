"""
JSON logger setup for structured logging.
"""
import logging
import sys
from datetime import datetime
import json
from typing import Any, Dict

from app.config import settings


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add standard fields
        log_data.update({
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })

        # Add process and thread info
        log_data.update({
            "process": record.process,
            "thread": record.thread,
        })

        return json.dumps(log_data, default=str)


class ContextFilter(logging.Filter):
    """Filter to add contextual information to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Add contextual information to log record.

        Args:
            record: Log record to filter

        Returns:
            True to include the record
        """
        # Add environment
        record.environment = settings.ENVIRONMENT

        # You can add more context here, such as:
        # - Request ID from context
        # - User ID from context
        # - Correlation ID
        # These would typically come from contextvars

        return True


def setup_logger(name: str = None) -> logging.Logger:
    """
    Setup and configure a logger with JSON formatting.

    Args:
        name: Logger name (defaults to root logger if None)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Set log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Remove existing handlers
    logger.handlers = []

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use JSON formatter in production, simple formatter in development
    if settings.ENVIRONMENT == "production":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)

    # Add context filter
    console_handler.addFilter(ContextFilter())

    # Add handler to logger
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter to add extra context to all log messages.
    """

    def __init__(self, logger: logging.Logger, extra: Dict[str, Any] = None):
        """
        Initialize logger adapter.

        Args:
            logger: Logger instance
            extra: Extra context to add to all log messages
        """
        super().__init__(logger, extra or {})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the logging message and keyword arguments.

        Args:
            msg: Log message
            kwargs: Keyword arguments

        Returns:
            Tuple of (message, kwargs)
        """
        # Merge extra context
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        kwargs["extra"].update(self.extra)

        return msg, kwargs


# Performance logging decorator
def log_performance(logger: logging.Logger):
    """
    Decorator to log function execution time.

    Args:
        logger: Logger instance to use

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Function {func.__name__} completed",
                    extra={
                        "function": func.__name__,
                        "duration": f"{duration:.3f}s",
                        "status": "success"
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"Function {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "duration": f"{duration:.3f}s",
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )

                raise

        return wrapper
    return decorator


# Async performance logging decorator
def log_async_performance(logger: logging.Logger):
    """
    Decorator to log async function execution time.

    Args:
        logger: Logger instance to use

    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            import time
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                logger.info(
                    f"Async function {func.__name__} completed",
                    extra={
                        "function": func.__name__,
                        "duration": f"{duration:.3f}s",
                        "status": "success"
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time

                logger.error(
                    f"Async function {func.__name__} failed",
                    extra={
                        "function": func.__name__,
                        "duration": f"{duration:.3f}s",
                        "status": "error",
                        "error": str(e)
                    },
                    exc_info=True
                )

                raise

        return wrapper
    return decorator
