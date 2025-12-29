"""
Cross-platform path utilities.
"""
from pathlib import Path


def normalize_path(path_str):
    """
    Normalize a path string for cross-platform compatibility.
    Converts backslashes to forward slashes and resolves the path.
    
    Args:
        path_str: Path string or None
        
    Returns:
        Normalized path string or None
    """
    if path_str is None:
        return None
    return str(Path(path_str).resolve())


def get_app_dir():
    """
    Get the application directory.
    Works for both script and frozen executable.
    
    Returns:
        Path to application directory
    """
    import sys
    import os
    
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        # Get directory of the calling script
        import inspect
        frame = inspect.currentframe()
        caller_frame = frame.f_back
        caller_file = caller_frame.f_globals.get('__file__')
        if caller_file:
            return os.path.dirname(os.path.abspath(caller_file))
        return os.getcwd()


def ensure_directory_exists(filepath):
    """
    Ensure the directory for a file path exists.
    
    Args:
        filepath: Path to file
    """
    file_path = Path(filepath)
    if file_path.parent != Path('.'):
        file_path.parent.mkdir(parents=True, exist_ok=True)

