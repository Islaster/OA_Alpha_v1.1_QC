"""
Secure error handling to prevent information leakage.
Provides user-friendly messages while logging detailed errors securely.
"""
import sys
import traceback
import logging
from typing import Optional, Callable
from functools import wraps

from .validators import sanitize_log_message


logger = logging.getLogger(__name__)


# Generic user-friendly error messages
GENERIC_ERRORS = {
    'file_not_found': "The requested file could not be found.",
    'file_read_error': "Unable to read the file. Please check file permissions.",
    'file_write_error': "Unable to write to the file. Please check file permissions.",
    'invalid_input': "Invalid input provided. Please check your input and try again.",
    'processing_error': "An error occurred during processing. Please try again.",
    'configuration_error': "Configuration error. Please check your settings.",
    'network_error': "Network error. Please check your connection.",
    'permission_error': "Permission denied. Please check file and directory permissions.",
    'timeout_error': "Operation timed out. Please try again.",
    'unknown_error': "An unexpected error occurred. Please contact support if the problem persists."
}


class SecureError(Exception):
    """
    Base exception for secure errors.
    Includes both user message and detailed internal message.
    """
    
    def __init__(self, user_message: str, internal_message: Optional[str] = None,
                 error_code: Optional[str] = None):
        """
        Initialize secure error.
        
        Args:
            user_message: User-friendly message (shown to user)
            internal_message: Detailed internal message (logged only)
            error_code: Optional error code for categorization
        """
        self.user_message = user_message
        self.internal_message = internal_message or user_message
        self.error_code = error_code or 'unknown_error'
        super().__init__(self.user_message)


class SecureErrorHandler:
    """
    Handles errors securely, preventing information leakage.
    """
    
    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize error handler.
        
        Args:
            log_file: Optional log file for detailed errors
        """
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup secure logging configuration."""
        # Create logger with secure format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (INFO and above, generic messages)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # File handler (DEBUG and above, detailed messages)
        if self.log_file:
            try:
                file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
                file_handler.setLevel(logging.DEBUG)
                file_handler.setFormatter(formatter)
                
                # Add handlers
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"Warning: Could not setup file logging: {e}")
        
        logger.addHandler(console_handler)
        logger.setLevel(logging.DEBUG)
    
    def handle_error(self, error: Exception, context: Optional[str] = None) -> str:
        """
        Handle an error securely.
        
        Args:
            error: Exception to handle
            context: Optional context description
            
        Returns:
            User-friendly error message
        """
        # Determine error type
        if isinstance(error, SecureError):
            user_msg = error.user_message
            internal_msg = error.internal_message
            error_code = error.error_code
        elif isinstance(error, FileNotFoundError):
            user_msg = GENERIC_ERRORS['file_not_found']
            internal_msg = str(error)
            error_code = 'file_not_found'
        elif isinstance(error, PermissionError):
            user_msg = GENERIC_ERRORS['permission_error']
            internal_msg = str(error)
            error_code = 'permission_error'
        elif isinstance(error, TimeoutError):
            user_msg = GENERIC_ERRORS['timeout_error']
            internal_msg = str(error)
            error_code = 'timeout_error'
        elif isinstance(error, (ValueError, TypeError)):
            user_msg = GENERIC_ERRORS['invalid_input']
            internal_msg = str(error)
            error_code = 'invalid_input'
        else:
            user_msg = GENERIC_ERRORS['unknown_error']
            internal_msg = str(error)
            error_code = 'unknown_error'
        
        # Build context string
        context_str = f" (Context: {context})" if context else ""
        
        # Log detailed error (sanitized)
        sanitized_internal = sanitize_log_message(internal_msg)
        logger.error(
            f"[{error_code}]{context_str} {sanitized_internal}",
            exc_info=True
        )
        
        # Return user-friendly message
        return user_msg
    
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
        
        # Log full traceback securely
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        tb_str = ''.join(tb_lines)
        sanitized_tb = sanitize_log_message(tb_str)
        
        logger.critical(f"Unhandled exception:\n{sanitized_tb}")
        
        # Show generic message to user
        print("\n" + "="*60)
        print("ERROR: An unexpected error occurred")
        print("="*60)
        print(GENERIC_ERRORS['unknown_error'])
        if self.log_file:
            print(f"\nDetails have been logged to: {self.log_file}")
        print("="*60)


def secure_function(error_code: str = 'unknown_error', 
                    user_message: Optional[str] = None,
                    log_errors: bool = True):
    """
    Decorator to handle errors securely in functions.
    
    Args:
        error_code: Error code for this function
        user_message: Custom user message (default: generic)
        log_errors: Whether to log errors
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SecureError:
                # Re-raise SecureError as-is
                raise
            except Exception as e:
                # Wrap in SecureError
                msg = user_message or GENERIC_ERRORS.get(error_code, GENERIC_ERRORS['unknown_error'])
                internal = f"Error in {func.__name__}: {str(e)}"
                
                if log_errors:
                    logger.error(sanitize_log_message(internal), exc_info=True)
                
                raise SecureError(msg, internal, error_code) from e
        
        return wrapper
    return decorator


def log_sensitive_operation(operation: str):
    """
    Log a sensitive operation for audit trail.
    
    Args:
        operation: Description of operation
    """
    sanitized = sanitize_log_message(operation)
    logger.info(f"[AUDIT] {sanitized}")


def setup_global_error_handler(log_file: Optional[str] = None):
    """
    Setup global error handler for unhandled exceptions.
    
    Args:
        log_file: Optional log file path
    """
    handler = SecureErrorHandler(log_file)
    sys.excepthook = handler.handle_exception
    logger.info("Global secure error handler installed")


# Create global error handler instance
_global_handler: Optional[SecureErrorHandler] = None


def get_error_handler(log_file: Optional[str] = None) -> SecureErrorHandler:
    """
    Get global error handler instance.
    
    Args:
        log_file: Optional log file path
        
    Returns:
        SecureErrorHandler instance
    """
    global _global_handler
    
    if _global_handler is None:
        _global_handler = SecureErrorHandler(log_file)
    
    return _global_handler

