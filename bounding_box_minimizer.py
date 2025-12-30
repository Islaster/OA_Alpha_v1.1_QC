"""
Blender script for bounding box minimization.
This script is executed by Blender via: blender --background --python bounding_box_minimizer.py -- [args]

This is a thin wrapper that calls main_processor.py if available, otherwise uses inline logic.
"""
import sys
import os
from pathlib import Path

# Add script directory to path
script_dir = Path(__file__).parent.absolute()
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

# Try to import and use main_processor if available
try:
    import main_processor
    # main_processor already handles Blender execution and argument parsing
    if __name__ == "__main__":
        sys.exit(main_processor.main())
except ImportError:
    # Fallback: inline implementation (shouldn't normally happen)
    # This matches the logic from main_processor.py
    import argparse
    
    # Add src directory to path
    possible_src_paths = [
        script_dir / "src",
        script_dir.parent / "src",
        Path.cwd() / "src",
    ]
    
    for src_path in possible_src_paths:
        if src_path.exists() and str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            break
    
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
