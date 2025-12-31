"""
Simple error handling with logging.
"""
import sys
import traceback
import logging
from typing import Optional

from .validators import sanitize_log_message


logger = logging.getLogger(__name__)


class ErrorHandler:
    """
    Simple error handler with logging.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize error handler.
        
        Args:
            log_file: Optional log file for detailed errors
        """
        self.log_file = log_file
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception handler for unhandled exceptions.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't handle keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Log full traceback
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)
        sanitized_tb = sanitize_log_message(tb_str)
        
        logger.critical(f"Unhandled exception:\n{sanitized_tb}")
        
        # Show message to user
        print("\n" + "="*60)
        print("ERROR: An unexpected error occurred")
        print("="*60)
        print("An unexpected error occurred. Please contact support if the problem persists.")
        if self.log_file:
            print(f"\nDetails have been logged to: {self.log_file}")
        print("="*60)


def setup_global_error_handler(log_file: Optional[str] = None) -> None:
    """
    Setup global error handler for unhandled exceptions.
    
    Args:
        log_file: Optional log file path
    """
    handler = ErrorHandler(log_file)
    sys.excepthook = handler.handle_exception
    logger.info("Global error handler installed")

