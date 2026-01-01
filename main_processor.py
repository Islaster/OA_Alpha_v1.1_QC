"""
OA - Orientation Automator - Main Processor
Command-line interface for bounding box minimization.
Refactored modular version (legacy .blend packaging restored).

Legacy-like .blend contents:
  - 1_Original        (original import, untouched)
  - 2_Optimized       (optimized: rotated + optional ground positioning)
  - 3_Optimized_Baked (baked copy of optimized: transforms applied)

Executed by Blender via:
  blender --background --python bounding_box_minimizer.py -- [args]
"""

from __future__ import annotations

import sys
import os
import argparse
import time
import logging
from pathlib import Path
from typing import Optional, Tuple, Any

# Blender imports
try:
    import bpy
    BLENDER_AVAILABLE = True
except Exception:
    BLENDER_AVAILABLE = False

from src.core.bounding_box import get_bounding_box_volume
from src.io.file_loader import load_object
from src.io.file_exporter import export_object
from src.optimization.optimizer import RotationOptimizer
from src.learning.rotation_learner import RotationLearner
from src.positioning.ground_positioner import position_at_ground_zero
from src.utils.config_manager import ConfigManager, save_json_file
from src.utils.debugger import get_debugger, reset_debugger
from src.utils.paths import normalize_path


# -----------------------------------------------------------------------------
# Safety helpers (avoid dict/path errors)
# -----------------------------------------------------------------------------
def _as_str_path(value: Any, default: str) -> str:
    """
    Ensure a safe string filepath.
    If a config value is mistakenly a dict/list/etc, fall back to default.
    """
    if isinstance(value, (str, Path)):
        return str(value)
    return default


def _as_log_level(value: Any, default: int = logging.INFO) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return getattr(logging, value.strip().upper(), default)
    return default


def _ensure_parent_dir(filepath: str) -> None:
    try:
        Path(filepath).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# -----------------------------------------------------------------------------
# Blender helpers (legacy .blend staging)
# -----------------------------------------------------------------------------
def _ensure_object_mode() -> None:
    if not BLENDER_AVAILABLE:
        return
    try:
        if bpy.context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
    except Exception:
        pass


def _get_or_create_collection(name: str):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _remove_objects_in_collection(col) -> None:
    # Remove existing staged objects from previous runs
    for o in list(col.objects):
        try:
            bpy.data.objects.remove(o, do_unlink=True)
        except Exception:
            pass


def _unlink_from_all_collections(obj) -> None:
    try:
        for col in list(obj.users_collection):
            try:
                col.objects.unlink(obj)
            except Exception:
                pass
    except Exception:
        pass


def _duplicate_object(obj, new_name: str, *, copy_mesh: bool = True):
    new_data = obj.data
    if copy_mesh and getattr(obj, "data", None) is not None:
        try:
            new_data = obj.data.copy()
        except Exception:
            new_data = obj.data

    dup = bpy.data.objects.new(new_name, new_data)
    dup.matrix_world = obj.matrix_world.copy()
    return dup


def _bake_transforms(obj) -> None:
    _ensure_object_mode()
    try:
        bpy.ops.object.select_all(action="DESELECT")
    except Exception:
        pass

    try:
        obj.hide_set(False)
    except Exception:
        pass

    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def _stage_blend_like_legacy(original_obj, optimized_obj):
    """
    Build the legacy .blend structure:
      1_Original / 2_Optimized / 3_Optimized_Baked
    Returns baked_obj.
    """
    col_original = _get_or_create_collection("1_Original")
    col_optimized = _get_or_create_collection("2_Optimized")
    col_baked = _get_or_create_collection("3_Optimized_Baked")

    _remove_objects_in_collection(col_original)
    _remove_objects_in_collection(col_optimized)
    _remove_objects_in_collection(col_baked)

    _unlink_from_all_collections(original_obj)
    _unlink_from_all_collections(optimized_obj)

    col_original.objects.link(original_obj)
    col_optimized.objects.link(optimized_obj)

    baked_obj = _duplicate_object(optimized_obj, f"{optimized_obj.name}_baked", copy_mesh=True)
    _unlink_from_all_collections(baked_obj)
    col_baked.objects.link(baked_obj)
    _bake_transforms(baked_obj)

    print("✓ Staged .blend collections: 1_Original, 2_Optimized, 3_Optimized_Baked", flush=True)
    return baked_obj


# -----------------------------------------------------------------------------
# Processor
# -----------------------------------------------------------------------------
class BoundingBoxProcessor:
    """Main processor for bounding box minimization."""

    def __init__(self, config_path: str = "config.json"):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config or {}

        self.logger = logging.getLogger(__name__)
        self.setup_logging()

        # Debugger (harden file path)
        debug_config = self.config.get("debug", {}) or {}
        reset_debugger()
        dbg_log_file = _as_str_path(debug_config.get("log_file"), "debug_log.txt")

        self.debugger = get_debugger(
            enabled=bool(debug_config.get("enabled", False)),
            log_file=dbg_log_file,
            save_intermediate=bool(debug_config.get("save_intermediate", False)),
            verbose=bool(debug_config.get("verbose", False)),
        )
        self.debugger.log("BoundingBoxProcessor initialized")

        # Learner (harden presets path)
        paths_cfg = self.config.get("paths", {}) or {}
        presets_file = _as_str_path(paths_cfg.get("presets_file"), "rotation_presets.json")
        self.learner = RotationLearner(presets_file)

    def setup_logging(self) -> None:
        """Setup logging configuration (hardened)."""
        log_config = self.config.get("logging", {}) or {}

        log_level = _as_log_level(log_config.get("log_level"), logging.INFO)
        log_file = _as_str_path(log_config.get("log_file"), "processing_log.txt")

        _ensure_parent_dir(log_file)

        # Avoid adding multiple handlers if Blender imports/reloads
        root = logging.getLogger()
        if root.handlers:
            root.setLevel(log_level)
            self.logger = logging.getLogger(__name__)
            return

        root.setLevel(log_level)
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

        sh = logging.StreamHandler(sys.stderr)
        sh.setFormatter(fmt)
        root.addHandler(sh)

        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(fmt)
            root.addHandler(fh)
        except Exception as e:
            # Don't crash Blender if file logging fails
            print(f"WARNING: Could not open log file '{log_file}': {e}", file=sys.stderr, flush=True)

        self.logger = logging.getLogger(__name__)

    def process_file(
        self,
        input_filepath: str,
        object_name: Optional[str] = None,
        object_type: str = "unknown",
        use_learning: bool = True,
        save_rotation: bool = True,
        no_ground: bool = False,
    ) -> Optional[dict]:
        if not BLENDER_AVAILABLE:
            print("ERROR: bpy not available. Must run inside Blender.", file=sys.stderr, flush=True)
            return None

        start_time = time.time()

        input_filepath = normalize_path(input_filepath)
        input_path = Path(input_filepath)

        self.logger.info(f"Processing object: {input_path.name}")

        # Load original import
        imported_obj = load_object(input_filepath)
        if imported_obj is None:
            self.logger.error("Failed to load object")
            return None

        # Legacy wants OG + optimized + baked inside blend.
        # Keep imported_obj as original (untouched), optimize a duplicate.
        original_obj = imported_obj
        optimized_obj = _duplicate_object(original_obj, f"{original_obj.name}_optimized", copy_mesh=True)

        # Link optimized into scene temporarily (it will be re-linked during staging)
        try:
            bpy.context.scene.collection.objects.link(optimized_obj)
        except Exception:
            try:
                bpy.context.collection.objects.link(optimized_obj)
            except Exception:
                pass

        if object_name is None:
            object_name = input_path.stem

        # Initial bbox on optimized copy (same as original at this moment)
        initial_volume, initial_dims = get_bounding_box_volume(optimized_obj)
        self.logger.info(f"Initial bounding box: {initial_dims} (volume: {initial_volume:.6f})")

        # Learned presets
        learned_presets = []
        if use_learning and self.config.get("learning", {}).get("enable_learning", True):
            learned_presets = self.learner.get_presets_for_object(object_name, object_type)
            self.logger.info(f"Found {len(learned_presets)} learned presets")

        # Optimize rotation on optimized_obj
        self.logger.info("Optimizing rotation...")
        optimizer = RotationOptimizer(optimized_obj)

        best_rotation_deg, bbox_reduction = optimizer.optimize(learned_presets)

        # Optional ground positioning (on optimized only)
        # Always place the optimized object nicely for viewing in Blender:
        # center on X/Y and sit on Z=0 (matches OG blend behavior).
        position_at_ground_zero(optimized_obj)
        
        # If you still want --no-ground to skip some *extra* ground variants,
        # keep that logic separate from the basic placement above.
        if no_ground:
            print("NOTE: --no-ground enabled (skipping extra ground variants), but still centering/grounding for .blend view.", flush=True)

        # Final bbox (optimized)
        final_volume, final_dims = get_bounding_box_volume(optimized_obj)
        processing_time = time.time() - start_time

        self.logger.info(f"Final bounding box: {final_dims} (volume: {final_volume:.6f})")
        self.logger.info(f"Reduction: {bbox_reduction:.2f}%")
        self.logger.info(f"Processing time: {processing_time:.2f}s")

        # Save rotation learning
        if save_rotation and bbox_reduction > 0:
            try:
                self.learner.save_rotation(object_name, object_type, best_rotation_deg, bbox_reduction)
                self.logger.info("Saved rotation to learning system")
            except Exception as e:
                self.logger.warning(f"Could not save rotation preset: {e}")

        # Output blend path
        output_dir = input_path.parent
        base_name = input_path.stem
        blend_path = output_dir / f"{base_name}_optimized.blend"

        # Stage OG + optimized + baked into named collections before saving .blend
        _stage_blend_like_legacy(original_obj, optimized_obj)

        # Choose baked export format based on input extension (so baked matches input type)
        in_ext = input_path.suffix.lower()
        if in_ext in {".obj", ".fbx", ".ply", ".gltf", ".glb"}:
            os.environ["OA_BAKED_FORMAT"] = in_ext
        else:
            os.environ.pop("OA_BAKED_FORMAT", None)

        print(f"Saving to: {blend_path}", flush=True)

        # Save .blend (exporter will also try baked exports if baked collections exist)
        export_object(optimized_obj, str(blend_path), format="blend")

        # Attempts count (best-effort)
        attempts = 0
        try:
            attempts = len(getattr(optimizer, "attempts", []))
        except Exception:
            attempts = 0

        return {
            "input_file": str(input_path),
            "output_blend": str(blend_path),
            "initial_bbox": {"dimensions": initial_dims, "volume": initial_volume},
            "final_bbox": {"dimensions": final_dims, "volume": final_volume},
            "rotation_applied": best_rotation_deg,
            "rotation_x": best_rotation_deg[0],
            "rotation_y": best_rotation_deg[1],
            "rotation_z": best_rotation_deg[2],
            "bbox_reduction_percent": bbox_reduction,
            "processing_time": processing_time,
            "attempts": attempts,
        }


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------
def main() -> int:
    """Main entry point for command-line execution (runs inside Blender)."""
    parser = argparse.ArgumentParser(
        description="Minimize bounding box of 3D objects through rotation optimization"
    )
    parser.add_argument("input", help="Input file path (obj, fbx, blend, etc.)")
    parser.add_argument("-c", "--config", default="config.json", help="Configuration file path")
    parser.add_argument("--type", default="unknown", help="Object type/category for learning")
    parser.add_argument("--no-learning", action="store_true", help="Disable learned presets")
    parser.add_argument("--no-save-learning", action="store_true", help="Do not save learned rotation")
    parser.add_argument("--no-ground", action="store_true", help="Skip positioning at ground zero")
    parser.add_argument("--report", default=None, help="Write a JSON report to this path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    # Blender provides args after '--'
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = argv[1:]

    args = parser.parse_args(argv)

    processor = BoundingBoxProcessor(args.config)

    # Enable debug if requested
    if args.debug:
        processor.config.setdefault("debug", {})
        processor.config["debug"]["enabled"] = True
        try:
            processor.debugger.enabled = True
        except Exception:
            pass
        processor.debugger.log("Debug mode enabled from command line")

    result = processor.process_file(
        args.input,
        object_name=Path(args.input).stem,
        object_type=args.type,
        use_learning=not args.no_learning,
        save_rotation=not args.no_save_learning,
        no_ground=args.no_ground,
    )

    if result is None:
        return 1

    if args.report:
        try:
            save_json_file(args.report, result)
            processor.logger.info(f"Saved report to {args.report}")
        except Exception as e:
            processor.logger.warning(f"Failed to write report: {e}")
    else:
        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Reduction: {result['bbox_reduction_percent']:.2f}%")
        print(f"Initial Volume: {result['initial_bbox']['volume']:.6f}")
        print(f"Final Volume: {result['final_bbox']['volume']:.6f}")
        print("\nBest Rotation:")
        print(f"  X-axis: {result['rotation_x']:.2f}°")
        print(f"  Y-axis: {result['rotation_y']:.2f}°")
        print(f"  Z-axis: {result['rotation_z']:.2f}°")
        print(f"\nTime: {result['processing_time']:.2f}s")
        print(f"Attempts: {result['attempts']}")
        print("=" * 50)

    return 0


if __name__ == "__main__":
    code = main()
    if code is not None:
        sys.exit(code)
