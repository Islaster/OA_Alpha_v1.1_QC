"""
Blender Bounding Box Minimizer
Main entry point for headless execution.

Mac-compatible version with cross-platform path handling.
"""
import sys
import os
import argparse
import json
import time
import logging
from pathlib import Path

# Add current directory to path for imports (cross-platform)
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

try:
    import bpy
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False
    print("Warning: bpy not available. This script must be run from within Blender.")

from utils import load_json_file, save_json_file, get_bounding_box_volume
from rotation_optimizer import RotationOptimizer
from debugger import get_debugger, reset_debugger

# Optional imports for ground detection and learning
try:
    from rotation_learner import RotationLearner
    LEARNER_AVAILABLE = True
except ImportError:
    LEARNER_AVAILABLE = False
    RotationLearner = None

try:
    from ground_detection import GroundDetectionOrchestrator
    GROUND_DETECTION_AVAILABLE = True
except ImportError:
    GROUND_DETECTION_AVAILABLE = False
    GroundDetectionOrchestrator = None


def normalize_path(path_str):
    """
    Normalize a path string for cross-platform compatibility.
    Converts backslashes to forward slashes and resolves the path.
    """
    if path_str is None:
        return None
    # Convert to Path object (handles both / and \ automatically)
    return str(Path(path_str).resolve())


class BoundingBoxMinimizer:
    def __init__(self, config_path="config.json"):
        """Initialize the minimizer with configuration."""
        # Normalize config path
        config_path = normalize_path(config_path)
        if not os.path.exists(config_path):
            # Try looking in the same directory as the script
            script_dir = Path(__file__).parent
            config_path = str(script_dir / "config.json")
        
        self.config = load_json_file(config_path, default={})
        self.setup_logging()
        
        # Initialize debugger
        debug_config = self.config.get("debug", {})
        reset_debugger()  # Reset any existing debugger
        self.debugger = get_debugger(
            enabled=debug_config.get("enabled", False),
            log_file=debug_config.get("log_file", "debug_log.txt"),
            save_intermediate=debug_config.get("save_intermediate", False)
        )
        self.debugger.log("BoundingBoxMinimizer initialized")
        
        # Initialize components
        presets_file = self.config.get("paths", {}).get("presets_file", "rotation_presets.json")
        
        # Initialize learner if available
        if LEARNER_AVAILABLE:
            self.learner = RotationLearner(presets_file)
        else:
            self.learner = None
        
        # Initialize ground detection if available
        if GROUND_DETECTION_AVAILABLE:
            ground_config = self.config.get("ground_detection", {})
            self.ground_detector = GroundDetectionOrchestrator({
                'use_learned': ground_config.get('use_learned', True),
                'use_physics': ground_config.get('use_physics', True),
                'use_ai': ground_config.get('use_ai', False),
                'ai_provider': ground_config.get('ai_provider', 'openai'),
                'ai_api_key': ground_config.get('ai_api_key', ''),
                'confidence_threshold': ground_config.get('confidence_threshold', 0.8),
                'learning_file': ground_config.get('learning_file', 'orientation_learning.json')
            })
        else:
            self.ground_detector = None
        
        # Pass debug config to rotation config
        if "rotation" not in self.config:
            self.config["rotation"] = {}
        self.config["rotation"]["debug"] = debug_config
    
    def setup_logging(self):
        """Setup logging configuration."""
        log_config = self.config.get("logging", {})
        log_level = getattr(logging, log_config.get("log_level", "INFO"))
        log_file = log_config.get("log_file", "processing_log.txt")
        
        # Ensure log directory exists
        log_path = Path(log_file)
        if log_path.parent != Path('.'):
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def load_object(self, filepath):
        """
        Load a 3D object from file.
        
        Args:
            filepath: Path to object file (obj, fbx, blend, etc.)
            
        Returns:
            Blender object or None
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender API not available")
        
        # Normalize path for cross-platform compatibility
        filepath = normalize_path(filepath)
        ext = os.path.splitext(filepath)[1].lower()
        
        print(f"Loading {ext.upper()} file...", flush=True)
        load_start = time.time()
        
        # Clear existing meshes
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        
        try:
            if ext == '.blend':
                # Load from blend file
                with bpy.data.libraries.load(filepath) as (data_from, data_to):
                    data_to.objects = data_from.objects
                
                for obj in data_to.objects:
                    if obj is not None:
                        bpy.context.collection.objects.link(obj)
                        return obj
            elif ext == '.obj':
                # OBJ import - try multiple methods for compatibility
                try:
                    # Blender 4.0+ uses wm.obj_import
                    bpy.ops.wm.obj_import(filepath=filepath)
                except AttributeError:
                    try:
                        # Blender 3.x and earlier
                        bpy.ops.import_scene.obj(filepath=filepath)
                    except:
                        # Manual OBJ loading as fallback
                        self.logger.warning("Using manual OBJ import method")
                        self._manual_obj_import(filepath)
            elif ext == '.fbx':
                bpy.ops.import_scene.fbx(filepath=filepath)
            elif ext == '.ply':
                # PLY import - try different methods based on Blender version
                self._import_ply(filepath)
            elif ext in ['.gltf', '.glb']:
                bpy.ops.import_scene.gltf(filepath=filepath)
            else:
                # Try generic import
                bpy.ops.wm.open_mainfile(filepath=filepath)
            
            # Get the imported object
            if bpy.context.selected_objects:
                obj = bpy.context.selected_objects[0]
            elif bpy.context.scene.objects:
                obj = bpy.context.scene.objects[0]
            else:
                return None
            
            load_time = time.time() - load_start
            vert_count = len(obj.data.vertices) if obj.type == 'MESH' else 0
            print(f"✓ Loaded in {load_time:.1f}s ({vert_count:,} vertices)", flush=True)
            
            return obj
            
        except Exception as e:
            self.logger.error(f"Failed to load {filepath}: {e}")
            return None
    
    def _manual_obj_import(self, filepath):
        """Manual OBJ file import as fallback."""
        import bmesh
        vertices = []
        faces = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('v '):
                    coords = line.split()[1:4]
                    vertices.append([float(x) for x in coords])
                elif line.startswith('f '):
                    face_indices = [int(x.split('/')[0]) - 1 for x in line.split()[1:]]
                    faces.append(face_indices)
        
        # Create mesh from vertices and faces
        mesh = bpy.data.meshes.new("imported")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new("imported", mesh)
        bpy.context.collection.objects.link(obj)
    
    def _import_ply(self, filepath):
        """Import PLY file with fallback methods."""
        try:
            # Blender 4.0+ PLY import
            bpy.ops.wm.ply_import(filepath=filepath)
        except:
            try:
                # Blender 3.x built-in PLY import
                bpy.ops.import_mesh.ply(filepath=filepath)
            except:
                # Enable PLY addon if available and try again
                try:
                    import addon_utils
                    addon_utils.enable("io_mesh_ply", default_set=True, persistent=True)
                    bpy.ops.import_mesh.ply(filepath=filepath)
                except:
                    self.logger.error("PLY import failed. Please ensure PLY import addon is enabled in Blender.")
                    raise
    
    def _move_ground_to_zero(self, obj):
        """
        Move the object so its lowest point (ground) is at Z=0.
        Also centers the object on X and Y axes.
        """
        if not BLENDER_AVAILABLE or obj.type != 'MESH':
            return
        
        try:
            # Update to get current transforms
            bpy.context.view_layer.update()
            
            # Get all vertices in world space
            matrix_world = obj.matrix_world
            mesh = obj.data
            vert_count = len(mesh.vertices)
            
            if vert_count == 0:
                return
            
            # Try numpy for speed, fall back to pure Python
            try:
                import numpy as np
                
                coords = np.empty(vert_count * 3, dtype=np.float32)
                mesh.vertices.foreach_get('co', coords)
                coords = coords.reshape((vert_count, 3))
                
                # Transform to world space
                mat_np = np.array([list(row) for row in matrix_world])
                ones = np.ones((vert_count, 1), dtype=np.float32)
                coords_homo = np.hstack([coords, ones])
                transformed = coords_homo @ mat_np.T
                
                # Get min/max
                min_x, min_y, min_z = transformed[:, :3].min(axis=0)
                max_x, max_y, max_z = transformed[:, :3].max(axis=0)
                
            except ImportError:
                # Fallback without numpy
                from mathutils import Vector
                world_coords = [matrix_world @ v.co for v in mesh.vertices]
                min_x = min(v.x for v in world_coords)
                max_x = max(v.x for v in world_coords)
                min_y = min(v.y for v in world_coords)
                max_y = max(v.y for v in world_coords)
                min_z = min(v.z for v in world_coords)
                max_z = max(v.z for v in world_coords)
            
            # Calculate center on X and Y
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # Move object to origin
            obj.location.x -= center_x
            obj.location.y -= center_y
            obj.location.z -= min_z
            
            bpy.context.view_layer.update()
            
            print(f"✓ Moved to origin: ground at Z=0, centered at X=0, Y=0", flush=True)
            self.logger.info(f"Moved object to origin (offset: X={-center_x:.2f}, Y={-center_y:.2f}, Z={-min_z:.2f})")
            
        except Exception as e:
            self.logger.warning(f"Could not move to origin: {e}")
            print(f"⚠️ Could not move to origin: {e}", flush=True)
    
    def _position_object_at_ground_zero(self, obj):
        """
        Position an object so the bottom of its world-space bounding box is at Z=0.
        This properly handles rotated objects by calculating true world-space bounds.
        """
        if not BLENDER_AVAILABLE or obj.type != 'MESH':
            return
        
        try:
            from mathutils import Vector
            
            mesh = obj.data
            if len(mesh.vertices) == 0:
                return
            
            # Force scene update to ensure transforms are current
            bpy.context.view_layer.update()
            
            # Get current location BEFORE calculating bounds
            current_loc = obj.location.copy()
            matrix_world = obj.matrix_world.copy()
            
            print(f"  Positioning {obj.name}:", flush=True)
            print(f"    Current location: ({current_loc.x:.4f}, {current_loc.y:.4f}, {current_loc.z:.4f})", flush=True)
            print(f"    Rotation: ({obj.rotation_euler.x:.4f}, {obj.rotation_euler.y:.4f}, {obj.rotation_euler.z:.4f})", flush=True)
            
            # Calculate world-space bounds by transforming ALL vertices
            min_x = min_y = min_z = float('inf')
            max_x = max_y = max_z = float('-inf')
            
            for v in mesh.vertices:
                world_co = matrix_world @ v.co
                min_x = min(min_x, world_co.x)
                max_x = max(max_x, world_co.x)
                min_y = min(min_y, world_co.y)
                max_y = max(max_y, world_co.y)
                min_z = min(min_z, world_co.z)
                max_z = max(max_z, world_co.z)
            
            print(f"    World bounds: X[{min_x:.4f}, {max_x:.4f}] Y[{min_y:.4f}, {max_y:.4f}] Z[{min_z:.4f}, {max_z:.4f}]", flush=True)
            
            # Calculate center for X/Y positioning
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            # Set new location directly
            new_loc_x = current_loc.x - center_x
            new_loc_y = current_loc.y - center_y
            new_loc_z = current_loc.z - min_z
            
            print(f"    New location: ({new_loc_x:.4f}, {new_loc_y:.4f}, {new_loc_z:.4f})", flush=True)
            
            obj.location.x = new_loc_x
            obj.location.y = new_loc_y
            obj.location.z = new_loc_z
            
            # Force update
            bpy.context.view_layer.update()
            
            # Verify the positioning worked
            matrix_world = obj.matrix_world.copy()
            new_min_z = float('inf')
            for v in mesh.vertices:
                world_co = matrix_world @ v.co
                new_min_z = min(new_min_z, world_co.z)
            
            print(f"    Verified: new min_z = {new_min_z:.6f} (should be ~0)", flush=True)
            
            if abs(new_min_z) > 0.001:
                print(f"    ⚠️ WARNING: Object not at ground! Attempting correction...", flush=True)
                obj.location.z -= new_min_z
                bpy.context.view_layer.update()
            
        except Exception as e:
            self.logger.warning(f"Could not position at ground zero: {e}")
            print(f"  ⚠️ Position error: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    def process_object(self, obj, object_name=None, object_type="unknown", 
                      apply_ground_detection=True, use_learning=True, save_rotation=True, 
                      input_filepath=None, output_filepath=None):
        """
        Process a single object to minimize bounding box.
        
        Args:
            obj: Blender object
            object_name: Name identifier for learning
            object_type: Type/category for learning
            apply_ground_detection: Whether to apply ground detection
            use_learning: Whether to use previously learned rotations
            save_rotation: Whether to save successful rotation to learning system
            input_filepath: Original input file path (for naming)
            output_filepath: Final output file path (for export)
            
        Returns:
            dict: Processing results
        """
        if object_name is None:
            object_name = obj.name
        
        self.logger.info(f"Processing object: {object_name}")
        
        start_time = time.time()
        
        # Determine base name and directory for .blend files (cross-platform)
        if output_filepath:
            output_path = Path(output_filepath).resolve()
            output_dir = str(output_path.parent)
            base_name = output_path.stem
            if not output_path.parent.exists():
                if input_filepath:
                    output_dir = str(Path(input_filepath).parent.resolve())
                else:
                    output_dir = os.getcwd()
        elif input_filepath:
            input_path = Path(input_filepath).resolve()
            output_dir = str(input_path.parent)
            base_name = input_path.stem
        else:
            output_dir = os.getcwd()
            base_name = object_name
        
        # Store original state for later saving
        original_location = obj.location.copy()
        original_rotation = obj.rotation_euler.copy()
        original_scale = obj.scale.copy()
        
        # Get initial bounding box
        initial_volume, initial_dims = get_bounding_box_volume(obj)
        self.logger.info(f"Initial bounding box: {initial_dims} (volume: {initial_volume:.6f})")
        
        # Step 1: Ground detection (if enabled)
        ground_rotation = None
        ground_result = None
        needs_manual = False
        
        # Check if we have a pre-approved rotation (from GUI review workflow)
        pre_approved_rotation = self.config.get("apply_rotation")
        
        if pre_approved_rotation:
            # Apply the pre-approved rotation directly
            from mathutils import Euler
            import math
            obj.rotation_euler = Euler((
                pre_approved_rotation[0] * math.pi / 180,
                pre_approved_rotation[1] * math.pi / 180,
                pre_approved_rotation[2] * math.pi / 180
            ), 'XYZ')
            bpy.context.view_layer.update()
            self.logger.info(f"Applied pre-approved rotation: {pre_approved_rotation}")
            print(f"Applied pre-approved rotation: X={pre_approved_rotation[0]}°, Y={pre_approved_rotation[1]}°, Z={pre_approved_rotation[2]}°", flush=True)
            
            # Move object so lowest point is at Z=0
            self._move_ground_to_zero(obj)
            
        elif apply_ground_detection and self.ground_detector:
            self.logger.info("Detecting ground orientation...")
            try:
                ground_result = self.ground_detector.detect_ground(
                    obj, 
                    object_type=object_type, 
                    object_name=object_name
                )
            except Exception as e:
                self.logger.error(f"Ground detection failed: {e}", exc_info=True)
                print(f"ERROR in ground detection: {e}", flush=True)
                import traceback
                traceback.print_exc()
                ground_result = None
            
            if ground_result:
                needs_manual = ground_result.get('needs_manual', False)
                confidence = ground_result.get('confidence', 0)
                method = ground_result.get('method', 'unknown')
                
                if needs_manual:
                    print("\n" + "="*60)
                    print("⚠️  MANUAL INTERVENTION REQUIRED")
                    print("="*60)
                    print(f"Object: {object_name}")
                    print(f"Best guess: {method} with {confidence:.0%} confidence")
                    print(f"Reasoning: {ground_result.get('reasoning', 'All automatic methods failed')}")
                    print("\nPlease use manual 3-point marking:")
                    print("1. Open object in Blender")
                    print("2. Mark 3 points on the surface that should touch the ground")
                    print("3. System will calculate the correct rotation")
                    print("="*60 + "\n")
                    
                    ground_rotation = ground_result.get('rotation', (0, 0, 0))
                    self.logger.warning(f"Ground detection low confidence ({confidence:.0%}), manual marking recommended")
                else:
                    ground_rotation = ground_result.get('rotation', (0, 0, 0))
                    self.logger.info(f"Ground detection: {method} (confidence: {confidence:.0%})")
                    print(f"✓ Ground detected: {method} ({confidence:.0%} confidence)", flush=True)
                
                # Apply ground rotation
                if ground_rotation and ground_rotation != (0, 0, 0):
                    from mathutils import Euler
                    import math
                    x, y, z = ground_rotation
                    obj.rotation_euler = Euler((
                        x * math.pi / 180,
                        y * math.pi / 180,
                        z * math.pi / 180
                    ), 'XYZ')
                    bpy.context.view_layer.update()
                    self.logger.info(f"Applied ground rotation: {ground_rotation}")
                
                self._move_ground_to_zero(obj)
                
                if 'translation_z' in ground_result:
                    obj.location.z += ground_result['translation_z']
                    bpy.context.view_layer.update()
        
        # Step 2: Get learned presets (skip if using pre-approved rotation or use_learning=False)
        learned_presets = []
        skip_optimization = pre_approved_rotation is not None
        
        if not skip_optimization and use_learning and self.learner and self.config.get("learning", {}).get("enable_learning", True):
            learned_presets = self.learner.get_presets_for_object(object_name, object_type)
            if learned_presets:
                self.logger.info(f"Found {len(learned_presets)} learned presets")
        
        # Step 3: Optimize rotation
        if skip_optimization:
            best_rotation_deg = pre_approved_rotation
            bbox_reduction = 0
            self.logger.info(f"Using pre-approved rotation, skipping optimization")
            print(f"✓ Using pre-approved rotation (optimization already done)", flush=True)
            optimizer = RotationOptimizer(obj, self.config.get("rotation", {}))  # For attempts count
        else:
            self.logger.info("Optimizing rotation...")
            rotation_config = self.config.get("rotation", {})
            optimizer = RotationOptimizer(obj, rotation_config)
            best_rotation_deg, bbox_reduction = optimizer.optimize(learned_presets)
        
        # Step 4: Final positioning
        print("Positioning object at origin...", flush=True)
        self._move_ground_to_zero(obj)
        
        # Get final bounding box
        final_volume, final_dims = get_bounding_box_volume(obj)
        
        processing_time = time.time() - start_time
        
        self.logger.info(f"Final bounding box: {final_dims} (volume: {final_volume:.6f})")
        self.logger.info(f"Reduction: {bbox_reduction:.2f}%")
        self.logger.info(f"Processing time: {processing_time:.2f}s")
        
        # Save to learning system
        if save_rotation and bbox_reduction > 0 and self.learner:
            self.learner.save_rotation(
                object_name, object_type, best_rotation_deg, bbox_reduction
            )
            self.logger.info("Saved rotation to learning system")
        
        # Save ground detection choice
        if apply_ground_detection and ground_result and ground_rotation:
            save_name = object_name if object_name else (obj.name if BLENDER_AVAILABLE else "unknown")
            
            if isinstance(ground_result, dict) and "best" in ground_result:
                method = ground_result["best"].get("method", "auto")
            elif isinstance(ground_result, dict) and "method" in ground_result:
                method = ground_result["method"]
            else:
                method = "auto"
            
            if save_name and save_name != "unknown" and self.ground_detector:
                try:
                    self.ground_detector.update_pattern_feedback(
                        save_name, ground_rotation, was_correct=True
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to save ground detection pattern: {e}")
        
        # Check for ground rotation override from command line
        config_ground_rot = self.config.get("ground_rotation")
        if config_ground_rot is not None:
            ground_rotation = config_ground_rot
            print(f"Using ground rotation from config: {ground_rotation}", flush=True)
        
        # Save all versions in ONE .blend file
        blend_path = os.path.join(output_dir, f"{base_name}.blend")
        num_collections = 5 if (ground_rotation and ground_rotation != (0, 0, 0)) else 3
        print(f"Saving .blend file with {num_collections} collections...", flush=True)
        self.logger.info(f"Saving to: {blend_path}")
        
        # Get input format for exporting baked meshes
        input_format = None
        if input_filepath:
            input_format = Path(input_filepath).suffix.lower()
        
        try:
            obj = self._save_blend_with_both_versions(
                obj, 
                blend_path,
                original_location,
                original_rotation,
                original_scale,
                ground_rot=ground_rotation,
                input_format=input_format
            )
        except Exception as e:
            print(f"ERROR: Failed to save .blend file: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Failed to save .blend file: {e}")
        
        # If output filepath specified and it's not .blend, export to that format
        if output_filepath:
            output_ext = Path(output_filepath).suffix.lower()
            if output_ext and output_ext != '.blend':
                print(f"Exporting to {output_ext.upper()} format...")
                self.logger.info(f"Exporting to: {output_filepath}")
                self.save_object(obj, output_filepath, save_all_versions=False)
                print(f"✓ Exported to: {output_filepath}")
        
        # Calculate total rotation
        total_rotation = best_rotation_deg
        if ground_rotation and ground_rotation != (0, 0, 0):
            total_rotation = tuple(
                best_rotation_deg[i] + ground_rotation[i] 
                for i in range(3)
            )
        
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
            "ground_rotation": ground_rotation,
            "total_rotation": total_rotation,
            "rotation_x": best_rotation_deg[0],
            "rotation_y": best_rotation_deg[1],
            "rotation_z": best_rotation_deg[2],
            "bbox_reduction_percent": bbox_reduction,
            "processing_time": processing_time,
            "attempts": len(optimizer.attempts)
        }
    
    def _save_blend_with_both_versions(self, obj, base_path, orig_loc, orig_rot, orig_scale, ground_rot=None, input_format=None):
        """
        Save object as .blend file with collections, and optionally export baked meshes.
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender API not available")
        
        from mathutils import Euler
        import math
        
        # Ensure .blend extension and normalize path
        base_path = normalize_path(base_path)
        if not base_path.lower().endswith('.blend'):
            base_path = base_path + '.blend'
        
        # Store current (final) state
        final_location = obj.location.copy()
        final_rotation = obj.rotation_euler.copy()
        final_scale = obj.scale.copy()
        original_obj = obj
        
        # Check for ground detection options
        has_auto_ground = ground_rot and ground_rot != (0, 0, 0)
        threepoint_rotation = self.config.get("threepoint_rotation")
        threepoint_location = self.config.get("threepoint_location", (0, 0, 0))
        has_3point = threepoint_rotation is not None
        has_ground = has_auto_ground or has_3point
        has_both = has_auto_ground and has_3point
        
        if has_both:
            print(f"Creating 7 collections (auto ground + 3-point)", flush=True)
        elif has_3point:
            print(f"Creating 5 collections (3-point only)", flush=True)
        elif has_auto_ground:
            print(f"Creating 5 collections (auto ground only)", flush=True)
        else:
            print(f"Creating 3 collections (bbox only)", flush=True)
        
        try:
            # Store mesh data and object name BEFORE clearing scene
            mesh_data = original_obj.data.copy()
            obj_name = original_obj.name
            
            # Clear the scene
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            
            # Remove all existing collections
            for collection in list(bpy.data.collections):
                bpy.data.collections.remove(collection)
            
            # Create collections
            col_original = bpy.data.collections.new("1_Original")
            col_optimized = bpy.data.collections.new("2_Optimized")
            col_optimized_baked = bpy.data.collections.new("3_Optimized_Baked")
            
            bpy.context.scene.collection.children.link(col_original)
            bpy.context.scene.collection.children.link(col_optimized)
            bpy.context.scene.collection.children.link(col_optimized_baked)
            
            # 1. Original
            obj_original = bpy.data.objects.new(obj_name + "_original", mesh_data.copy())
            obj_original.location = orig_loc
            obj_original.rotation_euler = orig_rot
            obj_original.scale = orig_scale
            col_original.objects.link(obj_original)
            
            if has_ground:
                # 2. Optimized (bbox only)
                obj_optimized = bpy.data.objects.new(obj_name + "_optimized", mesh_data.copy())
                obj_optimized.location = (0, 0, 0)
                obj_optimized.rotation_euler = final_rotation
                obj_optimized.scale = final_scale
                col_optimized.objects.link(obj_optimized)
                
                bpy.context.view_layer.update()
                self._position_object_at_ground_zero(obj_optimized)
                
                # 3. Optimized baked
                obj_opt_baked = bpy.data.objects.new(obj_name + "_optimized_baked", mesh_data.copy())
                obj_opt_baked.location = obj_optimized.location.copy()
                obj_opt_baked.rotation_euler = final_rotation
                obj_opt_baked.scale = final_scale
                col_optimized_baked.objects.link(obj_opt_baked)
                
                bpy.ops.object.select_all(action='DESELECT')
                obj_opt_baked.select_set(True)
                bpy.context.view_layer.objects.active = obj_opt_baked
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                
                next_col_num = 4
                
                # Auto ground detection collections
                if has_auto_ground:
                    col_name_4 = f"{next_col_num}_Auto_Ground"
                    col_name_5 = f"{next_col_num+1}_Auto_Ground_Baked"
                    col_auto_ground = bpy.data.collections.new(col_name_4)
                    bpy.context.scene.collection.children.link(col_auto_ground)
                    
                    obj_auto_ground = bpy.data.objects.new(obj_name + "_auto_ground", mesh_data.copy())
                    
                    mat_bbox = final_rotation.to_matrix().to_4x4()
                    ground_euler = Euler((
                        ground_rot[0] * math.pi / 180,
                        ground_rot[1] * math.pi / 180,
                        ground_rot[2] * math.pi / 180
                    ), 'XYZ')
                    mat_ground = ground_euler.to_matrix().to_4x4()
                    mat_combined = mat_ground @ mat_bbox
                    combined_rot = mat_combined.to_euler('XYZ')
                    
                    obj_auto_ground.location = (0, 0, 0)
                    obj_auto_ground.rotation_euler = combined_rot
                    obj_auto_ground.scale = final_scale
                    col_auto_ground.objects.link(obj_auto_ground)
                    
                    bpy.context.view_layer.update()
                    self._position_object_at_ground_zero(obj_auto_ground)
                    bpy.context.view_layer.update()
                    
                    # Baked version
                    col_auto_baked = bpy.data.collections.new(col_name_5)
                    bpy.context.scene.collection.children.link(col_auto_baked)
                    
                    obj_auto_baked = bpy.data.objects.new(obj_name + "_auto_ground_baked", mesh_data.copy())
                    obj_auto_baked.location = obj_auto_ground.location.copy()
                    obj_auto_baked.rotation_euler = obj_auto_ground.rotation_euler.copy()
                    obj_auto_baked.scale = obj_auto_ground.scale.copy()
                    col_auto_baked.objects.link(obj_auto_baked)
                    
                    bpy.context.view_layer.update()
                    bpy.ops.object.select_all(action='DESELECT')
                    obj_auto_baked.select_set(True)
                    bpy.context.view_layer.objects.active = obj_auto_baked
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    
                    print(f"✓ Created collections {next_col_num}-{next_col_num+1}: Auto Ground", flush=True)
                    next_col_num += 2
                
                # Manual 3-point ground collections
                if has_3point:
                    col_name_manual = f"{next_col_num}_Manual_Ground"
                    col_name_manual_baked = f"{next_col_num+1}_Manual_Ground_Baked"
                    col_manual = bpy.data.collections.new(col_name_manual)
                    bpy.context.scene.collection.children.link(col_manual)
                    
                    obj_manual = bpy.data.objects.new(obj_name + "_manual_ground", mesh_data.copy())
                    obj_manual.rotation_euler = Euler((
                        threepoint_rotation[0] * math.pi / 180,
                        threepoint_rotation[1] * math.pi / 180,
                        threepoint_rotation[2] * math.pi / 180
                    ), 'XYZ')
                    obj_manual.location = (0, 0, 0)
                    obj_manual.scale = final_scale
                    col_manual.objects.link(obj_manual)
                    
                    bpy.context.view_layer.update()
                    self._position_object_at_ground_zero(obj_manual)
                    bpy.context.view_layer.update()
                    
                    # Baked version
                    col_manual_baked = bpy.data.collections.new(col_name_manual_baked)
                    bpy.context.scene.collection.children.link(col_manual_baked)
                    
                    obj_manual_baked = bpy.data.objects.new(obj_name + "_manual_ground_baked", mesh_data.copy())
                    obj_manual_baked.location = obj_manual.location.copy()
                    obj_manual_baked.rotation_euler = obj_manual.rotation_euler.copy()
                    obj_manual_baked.scale = obj_manual.scale.copy()
                    col_manual_baked.objects.link(obj_manual_baked)
                    
                    bpy.context.view_layer.update()
                    bpy.ops.object.select_all(action='DESELECT')
                    obj_manual_baked.select_set(True)
                    bpy.context.view_layer.objects.active = obj_manual_baked
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    
                    print(f"✓ Created collections {next_col_num}-{next_col_num+1}: Manual 3-Point", flush=True)
                    next_col_num += 2
                
                total_collections = next_col_num - 1
                print(f"✓ Saved {total_collections} collections total", flush=True)
            else:
                # Without ground detection: just 3 collections
                obj_optimized = bpy.data.objects.new(obj_name + "_optimized", mesh_data.copy())
                obj_optimized.location = (0, 0, 0)
                obj_optimized.rotation_euler = final_rotation
                obj_optimized.scale = final_scale
                col_optimized.objects.link(obj_optimized)
                
                bpy.context.view_layer.update()
                self._position_object_at_ground_zero(obj_optimized)
                
                # Optimized baked
                obj_opt_baked = bpy.data.objects.new(obj_name + "_optimized_baked", mesh_data.copy())
                obj_opt_baked.location = obj_optimized.location.copy()
                obj_opt_baked.rotation_euler = final_rotation
                obj_opt_baked.scale = final_scale
                col_optimized_baked.objects.link(obj_opt_baked)
                
                bpy.ops.object.select_all(action='DESELECT')
                obj_opt_baked.select_set(True)
                bpy.context.view_layer.objects.active = obj_opt_baked
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                
                print(f"✓ Saved 3 collections: Original, Optimized, Optimized_Baked", flush=True)
            
            # Save the file
            bpy.ops.wm.save_as_mainfile(filepath=base_path)
            
            # Export baked meshes if requested
            if input_format and input_format.lower() in ['.obj', '.fbx', '.ply', '.gltf', '.glb']:
                self._export_baked_collections(base_path, input_format, has_auto_ground, has_3point, has_both)
            
            # Restore original object to scene
            bpy.ops.object.select_all(action='SELECT')
            bpy.ops.object.delete()
            
            for collection in list(bpy.data.collections):
                bpy.data.collections.remove(collection)
            
            obj_restored = bpy.data.objects.new(obj_name, mesh_data.copy())
            obj_restored.location = orig_loc
            obj_restored.rotation_euler = orig_rot
            obj_restored.scale = orig_scale
            bpy.context.collection.objects.link(obj_restored)
            
            bpy.ops.object.select_all(action='DESELECT')
            obj_restored.select_set(True)
            bpy.context.view_layer.objects.active = obj_restored
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            
            return obj_restored
            
        except Exception as e:
            error_msg = f"Failed to save .blend versions: {e}"
            print(f"ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            self.logger.error(error_msg)
            return obj
    
    def _export_baked_collections(self, blend_path, export_format, has_auto_ground, has_3point, has_both):
        """Export baked collections in the specified format."""
        try:
            base_path = str(Path(blend_path).with_suffix(''))
            ext = export_format.lower()
            
            baked_collections = [("Optimized_Baked", "_optimized_baked")]
            
            if has_auto_ground:
                baked_collections.append(("Auto_Ground_Baked", "_auto_ground_baked"))
            
            if has_3point:
                baked_collections.append(("Manual_Ground_Baked", "_manual_ground_baked"))
            
            for collection_pattern, suffix in baked_collections:
                collection = None
                for col in bpy.data.collections:
                    if collection_pattern in col.name:
                        collection = col
                        break
                
                if not collection or len(collection.objects) == 0:
                    continue
                
                bpy.ops.object.select_all(action='DESELECT')
                for obj in collection.objects:
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                
                export_path = f"{base_path}{suffix}{ext}"
                
                if ext == '.obj':
                    try:
                        bpy.ops.wm.obj_export(
                            filepath=export_path,
                            export_selected_objects=True,
                            global_scale=1.0,
                            apply_modifiers=True,
                            export_triangulated_mesh=False
                        )
                    except:
                        bpy.ops.export_scene.obj(
                            filepath=export_path,
                            use_selection=True,
                            use_materials=True,
                            global_scale=1.0
                        )
                elif ext == '.fbx':
                    bpy.ops.export_scene.fbx(
                        filepath=export_path,
                        use_selection=True,
                        global_scale=1.0,
                        apply_scale_options='FBX_SCALE_ALL',
                        bake_space_transform=False
                    )
                elif ext == '.ply':
                    try:
                        bpy.ops.wm.ply_export(
                            filepath=export_path,
                            export_selected_objects=True,
                            global_scale=1.0
                        )
                    except:
                        try:
                            bpy.ops.export_mesh.ply(filepath=export_path)
                        except:
                            import addon_utils
                            addon_utils.enable("io_mesh_ply", default_set=True, persistent=True)
                            bpy.ops.export_mesh.ply(filepath=export_path)
                elif ext in ['.gltf', '.glb']:
                    bpy.ops.export_scene.gltf(
                        filepath=export_path,
                        use_selection=True,
                        export_apply_modifiers=True
                    )
                
                print(f"✓ Exported: {Path(export_path).name}", flush=True)
                self.logger.info(f"Exported baked mesh: {export_path}")
                
        except Exception as e:
            print(f"Warning: Export failed: {e}", flush=True)
            self.logger.warning(f"Failed to export baked meshes: {e}")
    
    def save_object(self, obj, output_path, format=None, save_all_versions=False):
        """Save object to file."""
        if not BLENDER_AVAILABLE:
            raise RuntimeError("Blender API not available")
        
        output_path = normalize_path(output_path)
        base_path = str(Path(output_path).with_suffix(''))
        ext = Path(output_path).suffix.lower() if format is None else f".{format}"
        
        original_location = obj.location.copy()
        original_rotation = obj.rotation_euler.copy()
        original_scale = obj.scale.copy()
        
        try:
            if ext == '.blend':
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.wm.save_as_mainfile(filepath=output_path)
                self.logger.info(f"Saved .blend file: {output_path}")
            else:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                
                if ext == '.obj':
                    try:
                        bpy.ops.wm.obj_export(filepath=output_path, export_selected_objects=True)
                    except:
                        bpy.ops.export_scene.obj(filepath=output_path, use_selection=True, use_materials=False)
                elif ext == '.fbx':
                    bpy.ops.export_scene.fbx(filepath=output_path, use_selection=True)
                elif ext == '.ply':
                    self._export_ply(output_path)
                elif ext in ['.gltf', '.glb']:
                    bpy.ops.export_scene.gltf(filepath=output_path, use_selection=True)
                else:
                    raise ValueError(f"Unsupported format: {ext}")
                
                self.logger.info(f"Saved object to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save {output_path}: {e}")
            raise
        finally:
            obj.location = original_location
            obj.rotation_euler = original_rotation
            obj.scale = original_scale
    
    def _export_ply(self, filepath):
        """Export PLY with fallback methods."""
        try:
            bpy.ops.wm.ply_export(filepath=filepath)
        except:
            try:
                bpy.ops.export_mesh.ply(filepath=filepath)
            except:
                import addon_utils
                addon_utils.enable("io_mesh_ply", default_set=True, persistent=True)
                bpy.ops.export_mesh.ply(filepath=filepath)


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
        "-o", "--output",
        help="Output file path (default: input with _optimized suffix)"
    )
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Configuration file path (default: config.json)"
    )
    parser.add_argument(
        "--no-ground",
        action="store_true",
        help="Skip ground detection"
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
        "--use-ai",
        action="store_true",
        help="Enable AI vision detection (requires API key in config)"
    )
    parser.add_argument(
        "--ai-provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="AI provider to use (default: openai)"
    )
    parser.add_argument(
        "--ai-key",
        help="AI API key (overrides config file)"
    )
    parser.add_argument(
        "--ai-threshold",
        type=float,
        default=0.7,
        help="Only use AI if physics confidence below this (0-1, default: 0.7)"
    )
    parser.add_argument(
        "--detect-only",
        action="store_true",
        help="Only run ground detection, output result as JSON, don't optimize"
    )
    parser.add_argument(
        "--apply-rotation",
        help="Apply this rotation (x,y,z degrees) instead of detecting. Format: 'x,y,z'"
    )
    parser.add_argument(
        "--ground-rotation",
        help="Ground rotation that was applied (for collection naming). Format: 'x,y,z'"
    )
    parser.add_argument(
        "--3point-rotation",
        dest="threepoint_rotation",
        help="Total rotation from 3-point selection (x,y,z degrees)"
    )
    parser.add_argument(
        "--3point-location",
        dest="threepoint_location",
        help="Total location from 3-point selection (x,y,z)"
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
    
    # Initialize minimizer
    minimizer = BoundingBoxMinimizer(args.config)
    
    # Override AI settings if requested
    if GROUND_DETECTION_AVAILABLE and (args.use_ai or args.ai_key):
        ground_config = minimizer.config.get("ground_detection", {})
        ground_config["use_ai"] = True
        if args.ai_key:
            ground_config["ai_api_key"] = args.ai_key
        if args.ai_provider:
            ground_config["ai_provider"] = args.ai_provider
        if args.ai_threshold:
            ground_config["ai_threshold"] = args.ai_threshold
        
        minimizer.ground_detector = GroundDetectionOrchestrator({
            'use_learned': ground_config.get('use_learned', True),
            'use_physics': ground_config.get('use_physics', True),
            'use_ai': ground_config.get('use_ai', False),
            'ai_provider': ground_config.get('ai_provider', 'openai'),
            'ai_api_key': ground_config.get('ai_api_key', ''),
            'confidence_threshold': ground_config.get('confidence_threshold', 0.8),
            'learning_file': ground_config.get('learning_file', 'orientation_learning.json')
        })
    
    # Enable debug if requested
    if args.debug:
        minimizer.config["debug"]["enabled"] = True
        minimizer.debugger.enabled = True
        minimizer.debugger.log("Debug mode enabled from command line")
    
    # Load object
    obj = minimizer.load_object(args.input)
    if obj is None:
        minimizer.logger.error("Failed to load object")
        return 1
    
    # Handle detect-only mode
    if args.detect_only:
        import json as json_module
        import math
        from mathutils import Euler
        
        if args.apply_rotation:
            try:
                x, y, z = map(float, args.apply_rotation.split(','))
                obj.rotation_euler = Euler((
                    x * math.pi / 180,
                    y * math.pi / 180,
                    z * math.pi / 180
                ), 'XYZ')
                bpy.context.view_layer.update()
                print(f"Applied pre-rotation before detection: ({x}, {y}, {z})", flush=True)
            except ValueError:
                print(f"WARNING: Invalid pre-rotation format, detecting on original", flush=True)
        
        skip_learned = args.apply_rotation is not None
        
        print("===DETECTION_RESULT_START===", flush=True)
        try:
            ground_result = minimizer.ground_detector.detect_ground(
                obj,
                object_type=args.type,
                object_name=Path(args.input).name,
                skip_learned=skip_learned
            )
            
            detection_output = {
                "success": True,
                "object_name": Path(args.input).name,
                "object_type": args.type,
                "method": ground_result.get("method", "unknown") if isinstance(ground_result, dict) else "unknown",
                "confidence": ground_result.get("confidence", 0) if isinstance(ground_result, dict) else 0,
                "rotation": list(ground_result.get("rotation", [0,0,0])) if isinstance(ground_result, dict) else [0,0,0],
                "reasoning": ground_result.get("reasoning", "") if isinstance(ground_result, dict) else ""
            }
            print(json_module.dumps(detection_output))
        except Exception as e:
            print(json_module.dumps({
                "success": False,
                "error": str(e),
                "object_name": Path(args.input).name
            }))
        print("===DETECTION_RESULT_END===", flush=True)
        return 0
    
    # Handle apply-rotation mode
    if args.apply_rotation:
        try:
            x, y, z = map(float, args.apply_rotation.split(','))
            print(f"Applying pre-approved rotation: ({x}, {y}, {z})", flush=True)
            minimizer.config["apply_rotation"] = (x, y, z)
        except ValueError:
            print(f"ERROR: Invalid rotation format. Use 'x,y,z' e.g. '90,0,0'", flush=True)
            return 1
    
    # Handle ground-rotation
    if args.ground_rotation:
        try:
            gx, gy, gz = map(float, args.ground_rotation.split(','))
            minimizer.config["ground_rotation"] = (gx, gy, gz)
            print(f"Ground rotation was applied: ({gx}, {gy}, {gz})", flush=True)
        except ValueError:
            print(f"WARNING: Invalid ground rotation format, ignoring", flush=True)
            minimizer.config["ground_rotation"] = None
    else:
        minimizer.config["ground_rotation"] = None
    
    # Handle 3-point rotation
    if args.threepoint_rotation:
        try:
            rx, ry, rz = map(float, args.threepoint_rotation.split(','))
            minimizer.config["threepoint_rotation"] = (rx, ry, rz)
            print(f"Using 3-point total rotation: ({rx}, {ry}, {rz})", flush=True)
        except:
            minimizer.config["threepoint_rotation"] = None
    else:
        minimizer.config["threepoint_rotation"] = None
    
    if args.threepoint_location:
        try:
            lx, ly, lz = map(float, args.threepoint_location.split(','))
            minimizer.config["threepoint_location"] = (lx, ly, lz)
            print(f"Using 3-point location: ({lx}, {ly}, {lz})", flush=True)
        except:
            minimizer.config["threepoint_location"] = None
    else:
        minimizer.config["threepoint_location"] = None
    
    # Process object
    result = minimizer.process_object(
        obj,
        object_name=Path(args.input).name,
        object_type=args.type,
        apply_ground_detection=not args.no_ground,
        use_learning=not args.no_learning,
        save_rotation=not args.no_save_learning,
        input_filepath=args.input,
        output_filepath=args.output if args.output else None
    )
    
    # Export if needed
    if args.output:
        output_ext = Path(args.output).suffix.lower()
        if output_ext and output_ext != '.blend':
            minimizer.logger.info(f"Exporting to specified format: {args.output}")
            minimizer.save_object(obj, args.output, save_all_versions=False)
    
    # Save or print report
    if args.report:
        save_json_file(args.report, result)
        minimizer.logger.info(f"Saved report to {args.report}")
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
        if result.get('ground_rotation') and result['ground_rotation'] != (0, 0, 0):
            print(f"\nGround Rotation: {result['ground_rotation']}")
            print(f"Total Rotation: {result.get('total_rotation', 'N/A')}")
        print(f"\nTime: {result['processing_time']:.2f}s")
        print(f"Attempts: {result['attempts']}")
        
        if args.output:
            output_path = Path(args.output)
            output_dir = output_path.parent
            base_name = output_path.stem
        else:
            input_path = Path(args.input)
            output_dir = input_path.parent
            base_name = input_path.stem
        
        blend_file = output_dir / f"{base_name}.blend"
        
        print(f"\n.blend file saved: {blend_file}")
        print(f"  Contains 3 collections:")
        print(f"    • Original_With_Transforms")
        print(f"    • Optimized_With_Transforms")
        print(f"    • Optimized_Baked (used for export)")
        
        if args.output and not args.output.lower().endswith('.blend'):
            print(f"\nExported to: {args.output}")
        
        print("="*50)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    if exit_code is not None:
        sys.exit(exit_code)

