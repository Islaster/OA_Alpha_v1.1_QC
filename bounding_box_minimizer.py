"""
Blender script for bounding box minimization.
This script is executed by Blender via: blender --background --python bounding_box_minimizer.py -- [args]

This version is hardened for compiled app bundles (e.g., Nuitka) by:
- Avoiding adding app bundle directories that may contain compiled Python runtime/extension modules
  (which can corrupt Blender's embedded Python and cause ABI crashes like _struct slot errors).
- Adding ONLY an isolated import root that exposes the `src` package to Blender safely.
- Loading main_processor.py via importlib from an explicit file path (no sys.path injection needed).
"""
import sys
import os
import tempfile
import importlib.util
from pathlib import Path


# Use resolve() to handle symlinks (important for macOS AppTranslocation)
script_dir = Path(__file__).resolve().parent

# Add src directory to path (for compiled apps, build process copies src to Contents/Resources/src)
# Check standard locations where the build process places src
possible_src_paths = [
    (script_dir.parent / "Resources" / "src"),          # Contents/Resources/src (macOS app bundle)
    (script_dir / "src"),                               # Same directory as script (Windows/Linux)
    (script_dir.parent.parent / "Resources" / "src"),   # App bundle root/Resources/src (alternative)
    (Path.cwd() / "src"),                               # Current working directory (development)
    (script_dir.parent / "src"),                        # Contents/src (alternative)
]

# Remove duplicates while preserving order
seen = set()
unique_paths = []
for p in possible_src_paths:
    try:
        p_str = str(p)
    except Exception:
        p_str = repr(p)
    if p_str not in seen:
        seen.add(p_str)
        unique_paths.append(p)
possible_src_paths = unique_paths

debug_enabled = os.getenv("BLENDER_DEBUG") is not None

src_found = False
src_path_used = None
isolated_root = None

for src_path in possible_src_paths:
    try:
        resolved_path = src_path.resolve()
        if resolved_path.exists() and resolved_path.is_dir():
            # Verify it actually contains Python modules (has __init__.py or subdirectories)
            has_init = (resolved_path / "__init__.py").exists()
            has_subdirs = any(
                item.is_dir() for item in resolved_path.iterdir()
                if item.name not in ("__pycache__", ".DS_Store")
            )

            if has_init or has_subdirs:
                # IMPORTANT:
                # Do NOT add Contents/Resources or other app bundle dirs to sys.path in compiled builds,
                # because they may contain compiled Python runtime bits that can corrupt Blender's Python.
                #
                # Instead, create an isolated import root and expose ONLY the `src` package there.
                isolated_root = Path(tempfile.mkdtemp(prefix="oa_blender_py_"))
                isolated_src = isolated_root / "src"

                try:
                    # Symlink the real src directory into the isolated root
                    isolated_src.symlink_to(resolved_path, target_is_directory=True)
                except Exception:
                    # Fallback if symlinks are restricted
                    import shutil
                    shutil.copytree(resolved_path, isolated_src)

                iso_str = str(isolated_root)
                if iso_str not in sys.path:
                    sys.path.insert(0, iso_str)

                src_found = True
                src_path_used = resolved_path
                print(f"✓ Found src directory at: {resolved_path}", file=sys.stderr)
                print(f"✓ Added isolated import root to sys.path: {isolated_root}", file=sys.stderr)
                break

    except Exception as e:
        if debug_enabled:
            print(f"DEBUG: Error checking {src_path}: {e}", file=sys.stderr)
        continue

if not src_found:
    print(f"ERROR: Could not find 'src' directory. Searched:", file=sys.stderr)
    print(f"Script file: {__file__}", file=sys.stderr)
    print(f"Script directory (resolved): {script_dir}", file=sys.stderr)
    print(f"Script parent: {script_dir.parent}", file=sys.stderr)
    print("", file=sys.stderr)
    print("Searched paths:", file=sys.stderr)
    for p in possible_src_paths:
        try:
            exists = p.exists()
            is_dir = p.is_dir() if exists else False
        except Exception:
            exists = False
            is_dir = False
        print(f"  - {p}", file=sys.stderr)
        print(f"    exists={exists}, is_dir={is_dir}", file=sys.stderr)

    # Helpful macOS-specific hint
    print("", file=sys.stderr)
    print("Expected locations:", file=sys.stderr)
    print(f"  - {script_dir.parent / 'Resources' / 'src'} (macOS)", file=sys.stderr)
    print(f"  - {script_dir / 'src'} (Windows/Linux)", file=sys.stderr)
    print(f"Script location: {script_dir}", file=sys.stderr)
    sys.exit(1)


# Optional: verify imports from src now work (helps pinpoint issues)
try:
    import src  # noqa: F401
except Exception as e:
    print(f"ERROR: src directory found at {src_path_used} but `import src` failed: {e}", file=sys.stderr)
    print("sys.path (first 10):", file=sys.stderr)
    for p in sys.path[:10]:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)


# Load main_processor.py WITHOUT adding app bundle dirs to sys.path
# This avoids Blender importing from Contents/MacOS via sys.path.
try:
    main_proc_path = script_dir / "main_processor.py"
    if not main_proc_path.exists():
        raise FileNotFoundError(f"main_processor.py not found at: {main_proc_path}")

    spec = importlib.util.spec_from_file_location("oa_main_processor", str(main_proc_path))
    if spec is None or spec.loader is None:
        raise ImportError("Could not create import spec for main_processor.py")

    main_processor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_processor)

    if __name__ == "__main__":
        sys.exit(main_processor.main())

except Exception as e:
    print(f"ERROR: Failed to load or run main_processor.py: {e}", file=sys.stderr)
    print(f"main_processor path: {script_dir / 'main_processor.py'}", file=sys.stderr)
    print("", file=sys.stderr)
    print("sys.path (first 10):", file=sys.stderr)
    for p in sys.path[:10]:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)
