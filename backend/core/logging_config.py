"""
Logging configuration for UACC Portal.

Sets up structured logging with appropriate levels and formats.
"""
import logging
import sys
from pathlib import Path
from backend.core.config import settings


def setup_logging():
    """
    Configure application-wide logging.
    
    Sets up:
    - Console handler with INFO level
    - File handler (if log directory exists) with DEBUG level
    - Appropriate formatters
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler - INFO level for general output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler - DEBUG level for detailed logs
    # Check if log directory exists (from server structure: ~/data/logs/portal)
    log_dir = Path.home() / "data" / "logs" / "portal"
    if log_dir.exists() or settings.APP_ENV != "development":
        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / "uacc_portal.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Reduce SQL query noise
    
    logging.info("Logging configured successfully")


# Initialize logging when module is imported
setup_logging()

