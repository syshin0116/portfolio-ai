"""Logging configuration for the application."""

import json
import logging
import logging.config
from pathlib import Path
from typing import Any, Dict

import yaml


# Configure logging format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(level: str = "INFO", config_file: str = "logging.yaml") -> None:
    """Set up logging configuration from YAML file or fallback to basic config.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) - used if config_file not found
        config_file: Path to YAML logging configuration file
    """
    config_path = Path(config_file)

    if config_path.exists():
        try:
            # Create logs directory if it doesn't exist
            Path("logs").mkdir(exist_ok=True)

            with open(config_path) as f:
                config = yaml.safe_load(f)
                logging.config.dictConfig(config)
            return
        except Exception as e:
            # Use sys.stderr for early logging before config is set up
            import sys

            print(
                f"Warning: Failed to load logging config from {config_file}: {e}",
                file=sys.stderr,
            )
            print("Falling back to basic logging configuration", file=sys.stderr)

    # Fallback to basic configuration
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_request(logger: logging.Logger, endpoint: str, data: Dict[str, Any]) -> None:
    """Log incoming request with pretty formatting.

    Args:
        logger: Logger instance
        endpoint: Endpoint name
        data: Request data
    """
    logger.info(f"Request to {endpoint}")
    logger.debug(
        f"Request data: {json.dumps(data, indent=2, ensure_ascii=False, default=str)}"
    )


def log_response(logger: logging.Logger, endpoint: str, success: bool = True) -> None:
    """Log response status.

    Args:
        logger: Logger instance
        endpoint: Endpoint name
        success: Whether the request was successful
    """
    emoji = "✅" if success else "❌"
    level = logging.INFO if success else logging.ERROR
    logger.log(level, f"{emoji} Response from {endpoint}")


def log_step(logger: logging.Logger, step: str, details: str = "") -> None:
    """Log execution step.

    Args:
        logger: Logger instance
        step: Step name
        details: Additional details
    """
    logger.info(f"{step}" + (f" - {details}" if details else ""))


def log_error(logger: logging.Logger, error: Exception, context: str = "") -> None:
    """Log error with context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context
    """
    logger.error(
        f"Error{' in ' + context if context else ''}: {type(error).__name__}: {str(error)}"
    )
    logger.debug("Stack trace:", exc_info=True)
