"""
Blender installation finder and path management.
"""
import sys
import os
from src.utils.paths import get_app_dir


def find_blender():
    """
    Find Blender installation automatically.
    
    Returns:
        Path to Blender executable or empty string if not found
    """
    # First check saved path
    saved = load_saved_blender_path()
    if saved:
        return saved
    
    # Then check environment variable
    env_blender = os.environ.get('BLENDER')
    if env_blender and os.path.exists(env_blender):
        return env_blender
    
    # Platform-specific paths
    if sys.platform == 'darwin':  # macOS
        paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            os.path.expanduser("~/Applications/Blender.app/Contents/MacOS/Blender"),
            "/opt/homebrew/bin/blender",
            "/usr/local/bin/blender",
        ]
    elif sys.platform == 'win32':  # Windows
        paths = []
        # Check all versions 4.5 down to 3.0
        for major in [4, 3]:
            for minor in range(9, -1, -1):
                version = f"{major}.{minor}"
                paths.append(rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe")
        
        # Generic paths
        paths.extend([
            r"C:\Program Files\Blender Foundation\Blender\blender.exe",
            r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe",
            os.path.expanduser(r"~\Blender\blender.exe"),
        ])
    else:  # Linux
        paths = [
            "/usr/bin/blender",
            "/snap/bin/blender",
            "/usr/local/bin/blender",
        ]
        # Home directory versions
        for major in [4, 3]:
            for minor in range(9, -1, -1):
                version = f"{major}.{minor}"
                paths.append(os.path.expanduser(f"~/blender-{version}/blender"))
        paths.append(os.path.expanduser("~/blender/blender"))
        # Steam
        paths.append(os.path.expanduser("~/.steam/steam/steamapps/common/Blender/blender"))
    
    for p in paths:
        if os.path.exists(p):
            return p
    return ""


def load_saved_blender_path():
    """
    Load Blender path from saved file if it exists.
    
    Returns:
        Saved Blender path or None
    """
    app_dir = get_app_dir()
    path_file = os.path.join(app_dir, "blender_path.txt")
    if os.path.exists(path_file):
        try:
            with open(path_file, 'r') as f:
                saved_path = f.read().strip()
                if os.path.exists(saved_path):
                    return saved_path
        except:
            pass
    return None


def save_blender_path(blender_path):
    """
    Save Blender path for future use.
    
    Args:
        blender_path: Path to Blender executable
    """
    app_dir = get_app_dir()
    path_file = os.path.join(app_dir, "blender_path.txt")
    try:
        with open(path_file, 'w') as f:
            f.write(blender_path)
    except:
        pass

