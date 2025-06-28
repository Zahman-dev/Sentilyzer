"""Centralized logging configuration for all services.

Implements structured JSON logging with proper formatting and log levels.
"""

import logging
import logging.config
import sys


def configure_logging(service_name: str, log_level: str | None = None) -> None:
    """Configure logging for a service with structured JSON output and proper log levels.

    Args:
        service_name: Name of the service (e.g., 'data_ingestor', 'sentiment_processor')
        log_level: Optional override for log level (e.g., 'DEBUG', 'INFO')
    """
    # Default to INFO if no level specified
    level = getattr(logging, log_level.upper()) if log_level else logging.INFO

    # Define logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": '{"timestamp": "%(asctime)s", "service": "'
                + service_name
                + '", '
                '"level": "%(levelname)s", "name": "%(name)s", '
                '"function": "%(funcName)s", "line": %(lineno)d, '
                '"message": "%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%dT%H:%M:%S%z",
            },
        },
        "handlers": {
            "console_json": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "stream": sys.stdout,
            },
            "console_simple": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console_json"]
                if not sys.stderr.isatty()
                else ["console_simple"],
                "level": level,
                "propagate": True,
            }
        },
    }

    # Apply configuration
    logging.config.dictConfig(config)

    # Get logger for the service
    logger = logging.getLogger(service_name)
    logger.info(f"Logging configured for service: {service_name}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name.

    Args:
        name: Name for the logger, typically __name__ or service component name

    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)
