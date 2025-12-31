"""
OA - Orientation Automator - Main Processor
Command-line interface for bounding box minimization.
Refactored modular version.
"""
import sys
import os
import argparse
import json as json_module
import time
import logging
import math
from pathlib import Path

# Blender imports
try:
    import bpy
    from mathutils import Euler
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: bpy not available. This script must be run from within Blender.")

# Local imports
from src.core.bounding_box import get_bounding_box_volume
from src.io.file_loader import load_object
from src.io.file_exporter import export_object
from src.optimization.optimizer import RotationOptimizer
from src.learning.rotation_learner import RotationLearner
from src.positioning.ground_positioner import position_at_ground_zero
from src.utils.config_manager import ConfigManager, save_json_file
from src.utils.debugger import get_debugger, reset_debugger
from src.utils.paths import normalize_path


class BoundingBoxProcessor:
    """Main processor for bounding box minimization."""
    
    def __init__(self, config_path="config.json"):
        """
        Initialize processor with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        self.setup_logging()
        
        # Initialize debugger
        debug_config = self.config.get("debug", {})
        reset_debugger()
        self.debugger = get_debugger(
            enabled=debug_config.get("enabled", False),
            log_file=debug_config.get("log_file", "debug_log.txt"),
            save_intermediate=debug_config.get("save_intermediate", False)
        )
        self.debugger.log("BoundingBoxProcessor initialized")
        
        # Initialize learner
        presets_file = self.config.get("paths", {}).get("presets_file", "rotation_presets.json")
        self.learner = RotationLearner(presets_file)
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("log_level", "INFO"))
        log_file = log_config.get("log_file", "processing_log.txt")
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def process_file(self, input_filepath, object_name=None, object_type="unknown",
                    use_learning=True, save_rotation=True, no_ground=False):
        """
        Process a 3D file to minimize its bounding box.
        
        Args:
            input_filepath: Path to input 3D file
            object_name: Name for learning system
            object_type: Type/category for learning
            use_learning: Use learned rotations
            save_rotation: Save successful rotation
            no_ground: Skip positioning object at ground zero
            
        Returns:
            dict: Processing results
        """
        start_time = time.time()
        
        # Load object
        obj = load_object(input_filepath)
        if obj is None:
            self.logger.error("Failed to load object")
            return None
        
        if object_name is None:
            object_name = Path(input_filepath).stem
        
        self.logger.info(f"Processing object: {object_name}")
        
        # Get initial bounding box
        initial_volume, initial_dims = get_bounding_box_volume(obj)
        self.logger.info(f"Initial bounding box: {initial_dims} (volume: {initial_volume:.6f})")
        
        # Get learned presets
        learned_presets = []
        if use_learning and self.config.get("learning", {}).get("enable_learning", True):
            learned_presets = self.learner.get_presets_for_object(object_name, object_type)
            if learned_presets:
                self.logger.info(f"Found {len(learned_presets)} learned presets")
        
        # Optimize rotation
        self.logger.info("Optimizing rotation...")
        rotation_config = self.config.get("rotation", {})
        optimizer = RotationOptimizer(obj, rotation_config)
        best_rotation_deg, bbox_reduction = optimizer.optimize(learned_presets)
        
        # Position at origin (unless disabled)
        if not no_ground:
            print("Positioning object at origin...", flush=True)
            position_at_ground_zero(obj)
        else:
            print("Skipping ground positioning.", flush=True)
        
        # Get final bounding box
        final_volume, final_dims = get_bounding_box_volume(obj)
        
        processing_time = time.time() - start_time
        
        self.logger.info(f"Final bounding box: {final_dims} (volume: {final_volume:.6f})")
        self.logger.info(f"Reduction: {bbox_reduction:.2f}%")
        self.logger.info(f"Processing time: {processing_time:.2f}s")
        
        # Save to learning system
        if save_rotation and bbox_reduction > 0:
            self.learner.save_rotation(
                object_name, object_type, best_rotation_deg, bbox_reduction
            )
            self.logger.info("Saved rotation to learning system")
        
        # Save output
        output_dir = Path(input_filepath).parent
        base_name = Path(input_filepath).stem
        blend_path = output_dir / f"{base_name}_optimized.blend"
        
        print(f"Saving to: {blend_path}", flush=True)
        export_object(obj, str(blend_path), format='blend')
        
        return {
            "object_name": object_name,
            "object_type": object_type,
            "initial_bbox": {
                "dimensions": initial_dims,
                "volume": initial_volume
            },
            "final_bbox": {
                "dimensions": final_dims,
                "volume": final_volume
            },
            "rotation_applied": best_rotation_deg,
            "rotation_x": best_rotation_deg[0],
            "rotation_y": best_rotation_deg[1],
            "rotation_z": best_rotation_deg[2],
            "bbox_reduction_percent": bbox_reduction,
            "processing_time": processing_time,
            "attempts": len(optimizer.attempts)
        }


def main():
    """Main entry point for command-line execution."""
    parser = argparse.ArgumentParser(
        description="Minimize bounding box of 3D objects through rotation optimization"
    )
    parser.add_argument(
        "input",
        help="Input file path (obj, fbx, blend, etc.)"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Configuration file path (default: config.json)"
    )
    parser.add_argument(
        "--no-learning",
        action="store_true",
        help="Skip using learned rotations (still records new ones)"
    )
    parser.add_argument(
        "--no-save-learning",
        action="store_true",
        help="Don't save rotations to learning system"
    )
    parser.add_argument(
        "--type",
        default="unknown",
        help="Object type/category for learning (default: unknown)"
    )
    parser.add_argument(
        "--report",
        help="Save processing report to JSON file"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging"
    )
    parser.add_argument(
        "--no-ground",
        action="store_true",
        help="Skip positioning object at ground zero"
    )
    
    # Parse arguments
    if BLENDER_AVAILABLE:
        if "--" in sys.argv:
            args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
        else:
            parser.print_help()
            return
    else:
        args = parser.parse_args()
    
    # Initialize processor
    processor = BoundingBoxProcessor(args.config)
    
    # Enable debug if requested
    if args.debug:
        processor.config["debug"]["enabled"] = True
        processor.debugger.enabled = True
        processor.debugger.log("Debug mode enabled from command line")
    
    # Process file
    result = processor.process_file(
        args.input,
        object_name=Path(args.input).name,
        object_type=args.type,
        use_learning=not args.no_learning,
        save_rotation=not args.no_save_learning,
        no_ground=args.no_ground
    )
    
    if result is None:
        return 1
    
    # Save or print report
    if args.report:
        save_json_file(args.report, result)
        processor.logger.info(f"Saved report to {args.report}")
    else:
        print("\n" + "="*50)
        print("PROCESSING SUMMARY")
        print("="*50)
        print(f"Object: {result['object_name']}")
        print(f"Initial bbox: {result['initial_bbox']['dimensions']}")
        print(f"Final bbox: {result['final_bbox']['dimensions']}")
        print(f"Reduction: {result['bbox_reduction_percent']:.2f}%")
        print(f"\nROTATION APPLIED:")
        print(f"  X-axis: {result['rotation_x']:.2f}°")
        print(f"  Y-axis: {result['rotation_y']:.2f}°")
        print(f"  Z-axis: {result['rotation_z']:.2f}°")
        print(f"\nTime: {result['processing_time']:.2f}s")
        print(f"Attempts: {result['attempts']}")
        print("="*50)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)

