import logging
import sys
from app.core.config import settings

def setup_logging():
    """Configure logging for the application"""
    # Map string log level to logging constants
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    log_level = log_levels.get(settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create a logger
    logger = logging.getLogger(__name__)
    return logger

# Create a logger instance
logger = setup_logging()