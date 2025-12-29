"""
Input validation and sanitization following allowlist approach.
Prevents injection attacks and ensures data integrity.
"""
import re
import os
from pathlib import Path
from typing import Union, List, Optional


# Allowlisted file extensions
ALLOWED_3D_FORMATS = {'.obj', '.fbx', '.ply', '.blend', '.gltf', '.glb', '.stl'}
ALLOWED_CONFIG_FORMATS = {'.json', '.yaml', '.yml'}
ALLOWED_LOG_FORMATS = {'.txt', '.log'}

# Maximum path length (prevents buffer overflow attacks)
MAX_PATH_LENGTH = 4096

# Maximum string lengths for various inputs
MAX_OBJECT_NAME_LENGTH = 255
MAX_TYPE_NAME_LENGTH = 100
MAX_LOG_MESSAGE_LENGTH = 10000

# Allowlist patterns
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\.\ ]+$')
SAFE_OBJECT_TYPE_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def validate_file_path(path: Union[str, Path], 
                       purpose: str = "file",
                       must_exist: bool = False,
                       allowed_extensions: Optional[set] = None) -> Path:
    """
    Validate and sanitize file paths using allowlist approach.
    
    Args:
        path: File path to validate
        purpose: Description of file purpose (for error messages)
        must_exist: If True, file must exist
        allowed_extensions: Set of allowed extensions (e.g., {'.obj', '.fbx'})
        
    Returns:
        Validated and resolved Path object
        
    Raises:
        ValidationError: If validation fails
    """
    if not path:
        raise ValidationError(f"Empty {purpose} path provided")
    
    try:
        path_obj = Path(path).resolve()
    except Exception as e:
        raise ValidationError(f"Invalid {purpose} path format: {e}")
    
    # Check path length
    path_str = str(path_obj)
    if len(path_str) > MAX_PATH_LENGTH:
        raise ValidationError(f"{purpose} path exceeds maximum length ({MAX_PATH_LENGTH})")
    
    # Check for path traversal attempts
    try:
        # Ensure resolved path is within expected boundaries
        path_obj.resolve()
    except Exception as e:
        raise ValidationError(f"Invalid {purpose} path: {e}")
    
    # Validate extension if specified
    if allowed_extensions:
        ext = path_obj.suffix.lower()
        if ext not in allowed_extensions:
            raise ValidationError(
                f"Invalid {purpose} file extension: {ext}. "
                f"Allowed: {', '.join(sorted(allowed_extensions))}"
            )
    
    # Check existence if required
    if must_exist and not path_obj.exists():
        raise ValidationError(f"{purpose} file does not exist: {path_obj}")
    
    # Additional check: no null bytes
    if '\x00' in path_str:
        raise ValidationError(f"Null byte detected in {purpose} path")
    
    return path_obj


def validate_3d_file_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate 3D model file path.
    
    Args:
        path: Path to 3D file
        must_exist: If True, file must exist
        
    Returns:
        Validated Path object
    """
    return validate_file_path(
        path,
        purpose="3D model",
        must_exist=must_exist,
        allowed_extensions=ALLOWED_3D_FORMATS
    )


def validate_config_file_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate configuration file path.
    
    Args:
        path: Path to config file
        must_exist: If True, file must exist
        
    Returns:
        Validated Path object
    """
    return validate_file_path(
        path,
        purpose="configuration",
        must_exist=must_exist,
        allowed_extensions=ALLOWED_CONFIG_FORMATS
    )


def validate_log_file_path(path: Union[str, Path]) -> Path:
    """
    Validate log file path (doesn't need to exist).
    
    Args:
        path: Path to log file
        
    Returns:
        Validated Path object
    """
    return validate_file_path(
        path,
        purpose="log",
        must_exist=False,
        allowed_extensions=ALLOWED_LOG_FORMATS
    )


def validate_object_name(name: str) -> str:
    """
    Validate object name using allowlist approach.
    
    Args:
        name: Object name to validate
        
    Returns:
        Validated name
        
    Raises:
        ValidationError: If validation fails
    """
    if not name:
        raise ValidationError("Empty object name provided")
    
    if len(name) > MAX_OBJECT_NAME_LENGTH:
        raise ValidationError(f"Object name exceeds maximum length ({MAX_OBJECT_NAME_LENGTH})")
    
    # Remove any null bytes
    if '\x00' in name:
        raise ValidationError("Null byte detected in object name")
    
    # Sanitize: keep only safe characters
    # Allow alphanumeric, spaces, dots, underscores, hyphens
    sanitized = ''.join(c for c in name if c.isalnum() or c in ' ._-')
    
    if not sanitized:
        raise ValidationError("Object name contains no valid characters")
    
    return sanitized.strip()


def validate_object_type(type_name: str) -> str:
    """
    Validate object type using allowlist approach.
    
    Args:
        type_name: Object type to validate
        
    Returns:
        Validated type
        
    Raises:
        ValidationError: If validation fails
    """
    if not type_name:
        return "unknown"  # Default fallback
    
    if len(type_name) > MAX_TYPE_NAME_LENGTH:
        raise ValidationError(f"Object type exceeds maximum length ({MAX_TYPE_NAME_LENGTH})")
    
    # Remove null bytes
    if '\x00' in type_name:
        raise ValidationError("Null byte detected in object type")
    
    # Strict allowlist: only alphanumeric, underscores, hyphens
    if not SAFE_OBJECT_TYPE_PATTERN.match(type_name):
        raise ValidationError(
            "Object type contains invalid characters. "
            "Allowed: letters, numbers, underscores, hyphens"
        )
    
    return type_name.lower().strip()


def validate_rotation_tuple(rotation: tuple) -> tuple:
    """
    Validate rotation tuple.
    
    Args:
        rotation: Tuple of (x, y, z) rotation values
        
    Returns:
        Validated rotation tuple
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(rotation, (tuple, list)):
        raise ValidationError("Rotation must be a tuple or list")
    
    if len(rotation) != 3:
        raise ValidationError("Rotation must have exactly 3 values (x, y, z)")
    
    try:
        validated = tuple(float(v) for v in rotation)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid rotation values: {e}")
    
    # Check for reasonable bounds (degrees: -360 to 360, radians: -2π to 2π)
    for i, val in enumerate(validated):
        if abs(val) > 720:  # Covers both degree and radian ranges with margin
            raise ValidationError(f"Rotation value out of reasonable bounds: {val}")
    
    return validated


def validate_percentage(value: Union[int, float], name: str = "value") -> float:
    """
    Validate percentage value.
    
    Args:
        value: Percentage value
        name: Name of value (for error messages)
        
    Returns:
        Validated float
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        val = float(value)
    except (TypeError, ValueError) as e:
        raise ValidationError(f"Invalid {name}: must be a number")
    
    if not 0 <= val <= 100:
        raise ValidationError(f"{name} must be between 0 and 100")
    
    return val


def validate_command_args(args: List[str], purpose: str = "command") -> List[str]:
    """
    Validate command-line arguments to prevent injection.
    
    Args:
        args: List of command arguments
        purpose: Description of command (for error messages)
        
    Returns:
        Validated arguments list
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(args, list):
        raise ValidationError(f"{purpose} arguments must be a list")
    
    validated = []
    for arg in args:
        if not isinstance(arg, str):
            raise ValidationError(f"All {purpose} arguments must be strings")
        
        # Check for null bytes
        if '\x00' in arg:
            raise ValidationError(f"Null byte detected in {purpose} argument")
        
        # Check for suspicious patterns that might indicate injection
        suspicious_patterns = [';', '&&', '||', '`', '$(', '${']
        if any(pattern in arg for pattern in suspicious_patterns):
            raise ValidationError(
                f"Suspicious pattern detected in {purpose} argument. "
                "Possible command injection attempt."
            )
        
        validated.append(arg)
    
    return validated


def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message to prevent log injection.
    
    Args:
        message: Log message
        
    Returns:
        Sanitized message
    """
    if not message:
        return ""
    
    # Truncate if too long
    if len(message) > MAX_LOG_MESSAGE_LENGTH:
        message = message[:MAX_LOG_MESSAGE_LENGTH] + "... (truncated)"
    
    # Remove null bytes
    message = message.replace('\x00', '')
    
    # Replace newlines with spaces to prevent log injection
    message = message.replace('\n', ' ').replace('\r', ' ')
    
    # Remove any ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    message = ansi_escape.sub('', message)
    
    return message.strip()


def validate_port(port: Union[int, str]) -> int:
    """
    Validate network port number.
    
    Args:
        port: Port number
        
    Returns:
        Validated port number
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        port_int = int(port)
    except (TypeError, ValueError):
        raise ValidationError("Port must be an integer")
    
    if not 1 <= port_int <= 65535:
        raise ValidationError("Port must be between 1 and 65535")
    
    return port_int


def validate_timeout(timeout: Union[int, float]) -> float:
    """
    Validate timeout value.
    
    Args:
        timeout: Timeout in seconds
        
    Returns:
        Validated timeout
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        timeout_float = float(timeout)
    except (TypeError, ValueError):
        raise ValidationError("Timeout must be a number")
    
    if timeout_float < 0:
        raise ValidationError("Timeout cannot be negative")
    
    if timeout_float > 86400:  # 24 hours max
        raise ValidationError("Timeout exceeds maximum (24 hours)")
    
    return timeout_float

