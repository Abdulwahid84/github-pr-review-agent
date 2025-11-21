import logging
import sys
from app.config import settings

def setup_logger():
    """Setup application logger."""
    logger = logging.getLogger("github_pr_agent")
    
    # Set log level
    log_level = getattr(logging, settings.log_level, logging.INFO)
    logger.setLevel(log_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    if not logger.handlers:
        logger.addHandler(handler)
    
    return logger