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
        # For compiled executables (Nuitka, PyInstaller, etc.)
        # Nuitka with --onefile places data files next to the executable
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


def find_data_file(filename):
    """
    Find a data file that was included with --include-data-files.
    Searches multiple locations for compiled executables.
    
    For Nuitka with --onefile, data files are placed in the same directory
    as the executable (or extracted temp directory).
    
    Args:
        filename: Name of the file to find (e.g., "bounding_box_minimizer.py")
        
    Returns:
        Path to the file if found, None otherwise
    """
    import sys
    import os
    from pathlib import Path
    
    # List of directories to search
    search_dirs = []
    
    if getattr(sys, 'frozen', False):
        # For compiled executables (Nuitka, PyInstaller, etc.)
        exe_path = sys.executable
        exe_dir = os.path.dirname(os.path.abspath(exe_path))
        
        # Primary location: same directory as executable
        search_dirs.append(exe_dir)
        
        # For Nuitka --onefile, files are in the same directory as the .exe
        # Also check the actual executable location (not symlink)
        if os.path.islink(exe_path):
            real_exe = os.path.realpath(exe_path)
            search_dirs.append(os.path.dirname(real_exe))
        
        # Check parent directory (in case exe is in a subdirectory)
        parent_dir = os.path.dirname(exe_dir)
        if parent_dir != exe_dir:  # Avoid infinite loops
            search_dirs.append(parent_dir)
        
        # PyInstaller uses _MEIPASS for temp extraction
        if hasattr(sys, '_MEIPASS'):
            search_dirs.append(sys._MEIPASS)
        
        # Nuitka may use different temp locations, check common ones
        # For --onefile, Nuitka extracts to a temp dir, but data files
        # should be accessible via the executable's directory
        temp_base = os.path.join(os.path.expanduser("~"), ".cache")
        if os.path.exists(temp_base):
            search_dirs.append(temp_base)
    else:
        # For development/script mode
        app_dir = get_app_dir()
        search_dirs.append(app_dir)
        search_dirs.append(os.getcwd())
        
        # Also check the root project directory
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        search_dirs.append(str(project_root))
    
    # Search all directories (remove duplicates while preserving order)
    seen = set()
    for search_dir in search_dirs:
        if search_dir and search_dir not in seen:
            seen.add(search_dir)
            file_path = Path(search_dir) / filename
            if file_path.exists() and file_path.is_file():
                return str(file_path.resolve())
    
    # If not found, return None
    return None


def ensure_directory_exists(filepath):
    """
    Ensure the directory for a file path exists.
    
    Args:
        filepath: Path to file
    """
    file_path = Path(filepath)
    if file_path.parent != Path('.'):
        file_path.parent.mkdir(parents=True, exist_ok=True)

