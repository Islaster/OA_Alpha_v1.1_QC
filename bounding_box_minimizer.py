"""
Blender script for bounding box minimization.
This script is executed by Blender via: blender --background --python bounding_box_minimizer.py -- [args]

This is a thin wrapper that calls main_processor.py if available, otherwise uses inline logic.
"""
import sys
import os
from pathlib import Path

# Add script directory to path
# Use resolve() to handle symlinks (important for macOS AppTranslocation)
script_dir = Path(__file__).resolve().parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Add src directory to path (for compiled apps, build process copies src to Contents/Resources/src)
# Check standard locations where the build process places src
# Use resolve() for all paths to handle symlinks
possible_src_paths = [
    (script_dir.parent / "Resources" / "src").resolve(),  # Contents/Resources/src (macOS app bundle)
    (script_dir / "src").resolve(),  # Same directory as script (Windows/Linux)
    (script_dir.parent.parent / "Resources" / "src").resolve(),  # App bundle root/Resources/src
    Path.cwd() / "src",  # Current working directory (development)
    (script_dir.parent / "src").resolve(),  # Contents/src (alternative)
]

# Remove duplicates while preserving order
seen = set()
unique_paths = []
for p in possible_src_paths:
    p_str = str(p)
    if p_str not in seen:
        seen.add(p_str)
        unique_paths.append(p)
possible_src_paths = unique_paths

# Debug: print where we're looking (always print if src not found, or if BLENDER_DEBUG is set)
debug_enabled = os.getenv("BLENDER_DEBUG") is not None

src_found = False
src_path_used = None
for src_path in possible_src_paths:
    # Check if path exists and is a directory
    try:
        resolved_path = src_path.resolve() if hasattr(src_path, 'resolve') else src_path
        if resolved_path.exists() and resolved_path.is_dir():
            # Verify it actually contains Python modules (has __init__.py or subdirectories)
            has_init = (resolved_path / "__init__.py").exists()
            has_subdirs = any(item.is_dir() for item in resolved_path.iterdir() if item.name != "__pycache__")
            
            if has_init or has_subdirs:
                src_path_str = str(resolved_path)
                if src_path_str not in sys.path:
                    sys.path.insert(0, src_path_str)
                    src_found = True
                    src_path_used = resolved_path
                    # Always print when src is found (helps with debugging)
                    print(f"✓ Found src directory at: {resolved_path}", file=sys.stderr)
                    break
    except Exception as e:
        # Skip paths that cause errors (permissions, etc.)
        if os.getenv("BLENDER_DEBUG"):
            print(f"DEBUG: Error checking {src_path}: {e}", file=sys.stderr)
        continue

if not src_found:
    # Always print debug info when src is not found
    print(f"ERROR: Could not find 'src' directory. Searched:", file=sys.stderr)
    print(f"Script file: {__file__}", file=sys.stderr)
    print(f"Script directory (resolved): {script_dir}", file=sys.stderr)
    print(f"Script parent: {script_dir.parent}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Searched paths:", file=sys.stderr)
    for p in possible_src_paths:
        exists = p.exists()
        is_dir = p.is_dir() if exists else False
        print(f"  - {p}", file=sys.stderr)
        print(f"    exists={exists}, is_dir={is_dir}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Contents of {script_dir.parent}:", file=sys.stderr)
    try:
        if script_dir.parent.exists():
            for item in sorted(script_dir.parent.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                print(f"  - {item.name} ({item_type})", file=sys.stderr)
        else:
            print(f"  (Directory does not exist)", file=sys.stderr)
    except Exception as e:
        print(f"  (Could not list: {e})", file=sys.stderr)
    
    # Check if Resources directory exists
    resources_dir = script_dir.parent / "Resources"
    print(f"", file=sys.stderr)
    print(f"Resources directory: {resources_dir}", file=sys.stderr)
    print(f"  exists={resources_dir.exists()}, is_dir={resources_dir.is_dir() if resources_dir.exists() else False}", file=sys.stderr)
    if resources_dir.exists():
        print(f"  Contents:", file=sys.stderr)
        try:
            for item in sorted(resources_dir.iterdir()):
                item_type = "DIR" if item.is_dir() else "FILE"
                print(f"    - {item.name} ({item_type})", file=sys.stderr)
        except Exception as e:
            print(f"    (Could not list: {e})", file=sys.stderr)

# Try to import main_processor (requires src to be in path)
try:
    import main_processor
    # main_processor already handles Blender execution and argument parsing
    if __name__ == "__main__":
        sys.exit(main_processor.main())
except ImportError as e:
    # If import fails and we haven't found src, show the error
    if not src_found:
        # The error message below will show what we searched
        pass
    # Fallback: inline implementation (shouldn't normally happen if build process worked correctly)
    import argparse
    
    # If src still not found, show helpful error
    if "src" in str(e).lower():
        print(f"ERROR: Could not find 'src' directory. Build process should have copied it to:", file=sys.stderr)
        print(f"  - {script_dir.parent / 'Resources' / 'src'} (macOS)", file=sys.stderr)
        print(f"  - {script_dir / 'src'} (Windows/Linux)", file=sys.stderr)
        print(f"Script location: {script_dir}", file=sys.stderr)
        sys.exit(1)
    
    # The error isn't about src, so re-raise it
    raise
    
    try:
        from src.core.bounding_box import get_bounding_box_volume
        from src.io.file_loader import load_object
        from src.io.file_exporter import export_object
        from src.optimization.optimizer import RotationOptimizer
        from src.learning.rotation_learner import RotationLearner
        from src.positioning.ground_positioner import position_at_ground_zero
        from src.utils.config_manager import ConfigManager
    except ImportError as e:
        print(f"ERROR: Failed to import required modules: {e}", file=sys.stderr)
        print(f"Script directory: {script_dir}", file=sys.stderr)
        sys.exit(1)
    
    import bpy
    
    def main():
        """Main entry point - fallback implementation."""
        # Parse arguments (Blender passes args after --)
        if "--" in sys.argv:
            args_list = sys.argv[sys.argv.index("--") + 1:]
        else:
            args_list = sys.argv[1:]
        
        parser = argparse.ArgumentParser(
            description="Minimize bounding box of 3D objects through rotation optimization"
        )
        parser.add_argument("input", help="Input file path (obj, fbx, blend, etc.)")
        parser.add_argument("-c", "--config", default="config.json", help="Configuration file path")
        parser.add_argument("--no-learning", action="store_true", help="Skip using learned rotations")
        parser.add_argument("--no-ground", action="store_true", help="Skip ground positioning")
        parser.add_argument("--type", default="unknown", help="Object type/category for learning")
        
        try:
            args = parser.parse_args(args_list)
        except SystemExit:
            return 1
        
        # Clear default scene
        bpy.ops.wm.read_homefile(app_template="")
        
        # Load configuration
        config_path = Path(args.config)
        if not config_path.is_absolute():
            config_path = script_dir / config_path
        
        config_manager = ConfigManager(str(config_path))
        config = config_manager.config
        
        # Initialize learner
        presets_file = config.get("paths", {}).get("presets_file", "rotation_presets.json")
        if not Path(presets_file).is_absolute():
            presets_file = script_dir / presets_file
        learner = RotationLearner(str(presets_file))
        
        # Load object
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = Path.cwd() / input_path
        
        print(f"Loading: {input_path}", flush=True)
        obj = load_object(str(input_path))
        
        if obj is None:
            print(f"ERROR: Failed to load object from {input_path}", file=sys.stderr)
            return 1
        
        object_name = input_path.stem
        
        # Get initial bounding box
        initial_volume, initial_dims = get_bounding_box_volume(obj)
        print(f"Initial bounding box: {initial_dims} (volume: {initial_volume:.6f})", flush=True)
            
        # Get learned presets
        learned_presets = []
        if not args.no_learning and config.get("learning", {}).get("enable_learning", True):
            learned_presets = learner.get_presets_for_object(object_name, args.type)
            if learned_presets:
                print(f"Found {len(learned_presets)} learned presets", flush=True)
        
        # Optimize rotation
        print("Optimizing rotation...", flush=True)
        rotation_config = config.get("rotation", {})
        optimizer = RotationOptimizer(obj, rotation_config)
        best_rotation_deg, bbox_reduction = optimizer.optimize(learned_presets)
        
        # Position at ground (unless disabled)
        if not args.no_ground:
            print("Positioning object at origin...", flush=True)
            position_at_ground_zero(obj)
        
        # Get final bounding box
        final_volume, final_dims = get_bounding_box_volume(obj)
        print(f"Final bounding box: {final_dims} (volume: {final_volume:.6f})", flush=True)
        print(f"Reduction: {bbox_reduction:.2f}%", flush=True)
        
        # Save to learning system
        if not args.no_learning and bbox_reduction > 0:
            learner.save_rotation(object_name, args.type, best_rotation_deg, bbox_reduction)
                    
        # Save output
        output_dir = input_path.parent
        base_name = input_path.stem
        output_path = output_dir / f"{base_name}_optimized.blend"
        
        print(f"Saving to: {output_path}", flush=True)
        export_object(obj, str(output_path), format='blend')
        
        print("Done!", flush=True)
        return 0

    if __name__ == "__main__":
        sys.exit(main())
