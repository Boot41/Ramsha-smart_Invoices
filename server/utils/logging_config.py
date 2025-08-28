import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    # Color codes for different log levels
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Get the original formatted message
        message = super().format(record)
        
        # Add color based on log level
        level_color = self.COLORS.get(record.levelname, '')
        if level_color:
            # Color the level name and message
            message = f"{level_color}{message}{self.RESET}"
        
        return message


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "smart_invoice_scheduler.log",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Setup logging configuration for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from environment or parameter
    level = getattr(logging, os.getenv("LOG_LEVEL", log_level).upper(), logging.INFO)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    colored_formatter = ColoredFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(colored_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        log_dir / log_file,
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler (only errors and critical)
    error_file_handler = RotatingFileHandler(
        log_dir / f"error_{log_file}",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_file_handler)
    
    # Set specific logger levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("google.cloud").setLevel(logging.WARNING)
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("🚀 Smart Invoice Scheduler - Logging System Initialized")
    logger.info(f"📊 Log Level: {logging.getLevelName(level)}")
    logger.info(f"📁 Log Directory: {log_dir.absolute()}")
    logger.info(f"📄 Log File: {log_file}")
    logger.info("=" * 60)


def get_request_logger(module_name: str) -> logging.Logger:
    """
    Get a logger for request handling with consistent formatting
    
    Args:
        module_name: Name of the module (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(module_name)
    
    # Add request context if available (for future FastAPI request ID tracking)
    class RequestContextFilter(logging.Filter):
        def filter(self, record):
            # Add request ID if available in context
            # This can be enhanced with FastAPI middleware to track request IDs
            record.request_id = getattr(record, 'request_id', 'N/A')
            return True
    
    logger.addFilter(RequestContextFilter())
    return logger


def log_request_start(logger: logging.Logger, method: str, endpoint: str, user_email: str = "anonymous"):
    """Log the start of a request"""
    logger.info(f"🔄 {method} {endpoint} - User: {user_email}")


def log_request_success(logger: logging.Logger, method: str, endpoint: str, duration_ms: int = 0):
    """Log successful request completion"""
    logger.info(f"✅ {method} {endpoint} - Completed ({duration_ms}ms)")


def log_request_error(logger: logging.Logger, method: str, endpoint: str, error: str, duration_ms: int = 0):
    """Log request error"""
    logger.error(f"❌ {method} {endpoint} - Error: {error} ({duration_ms}ms)")


# Example usage and test function
def test_logging():
    """Test logging configuration"""
    setup_logging(log_level="DEBUG")
    
    logger = logging.getLogger(__name__)
    
    logger.debug("🔍 This is a debug message")
    logger.info("ℹ️ This is an info message")
    logger.warning("⚠️ This is a warning message")
    logger.error("❌ This is an error message")
    logger.critical("🚨 This is a critical message")
    
    # Test request logging
    request_logger = get_request_logger("test_module")
    log_request_start(request_logger, "POST", "/documents/upload", "test@example.com")
    log_request_success(request_logger, "POST", "/documents/upload", 250)


if __name__ == "__main__":
    test_logging()