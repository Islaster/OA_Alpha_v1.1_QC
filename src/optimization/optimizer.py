"""
Main rotation optimizer for bounding box minimization.
Multi-phase optimization strategy with grid search, PCA, and fine-tuning.
"""
import time
import math
from mathutils import Euler

from src.core.bounding_box import get_bounding_box_size
from src.core.rotation import degrees_to_radians, radians_to_degrees
from src.core.mesh_operations import force_object_update
from src.utils.debugger import get_debugger
from .rotation_generator import RotationGenerator
from .pca_aligner import calculate_pca_rotation


class RotationOptimizer:
    """
    Multi-phase rotation optimizer for bounding box minimization.
    
    Optimization Strategy:
        1. Learned presets (if available)
        2. Coarse grid search (45° steps)
        3. Medium refinement (15° around best)
        4. Fine refinement (5° around best)
        5. PCA alignment with smart Z-flip
        6. Fine-tune (gradient descent)
    """
    
    def __init__(self, obj, config=None, z_only=False):
        """
        Initialize optimizer for an object.
        
        Args:
            obj: Blender mesh object to optimize
            config: Configuration dict
            z_only: If True, only rotate around Z-axis (preserve upright)
        """
        self.obj = obj
        self.config = config or {}
        self.z_only = z_only
        
        # Capture initial state
        self.initial_rotation = obj.rotation_euler.copy()
        self.initial_bbox_size = self._get_bbox_size()
        
        # Best found so far
        self.best_rotation = self.initial_rotation.copy()
        self.best_bbox_size = self.initial_bbox_size
        
        # Tracking
        self.attempts = []
        self.step_count = 0
        
        # Config
        self.adaptive_steps = self.config.get("adaptive_steps", [5.0, 2.0, 1.0, 0.5, 0.2, 0.1])
        self.use_pca = self.config.get("use_pca_initial_guess", True)
        self.fast_mode = self.config.get("fast_mode", False)
        
        # Auto-enable fast mode for large meshes
        if obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
            if vert_count > 50000 and not self.fast_mode:
                self.fast_mode = True
                print(f"  [Auto-enabled fast mode for {vert_count:,} vertices]")
        
        # Initialize rotation generator
        self.generator = RotationGenerator(z_only=z_only, fast_mode=self.fast_mode)
        
        # Initialize debugger
        debug_config = self.config.get("debug", {})
        self.debugger = get_debugger(
            enabled=debug_config.get("enabled", False),
            log_file=debug_config.get("log_file", "debug_log.txt"),
            save_intermediate=debug_config.get("save_intermediate", False)
        )
    
    def _get_bbox_size(self):
        """Get bounding box volume."""
        return get_bounding_box_size(self.obj)
    
    def _force_update(self):
        """Force Blender to update the object and scene."""
        force_object_update(self.obj)
    
    def optimize(self, learned_presets=None, max_time=600):
        """
        Find optimal rotation using multi-phase strategy.
        
        Args:
            learned_presets: List of (x, y, z) degree tuples to try first
            max_time: Maximum optimization time in seconds
        
        Returns:
            tuple: (best_rotation_degrees, bbox_reduction_percent)
        """
        start_time = time.time()
        
        # Reset to initial state
        self._force_update()
        self.initial_bbox_size = self._get_bbox_size()
        self.obj.rotation_euler = self.initial_rotation.copy()
        self._force_update()
        
        self.best_bbox_size = self.initial_bbox_size
        self.best_rotation = self.initial_rotation.copy()
        
        init_deg = radians_to_degrees(self.initial_rotation)
        print(f"Starting optimization:")
        print(f"  Initial rotation: X={init_deg[0]:.1f}°, Y={init_deg[1]:.1f}°, Z={init_deg[2]:.1f}°")
        print(f"  Initial bbox size: {self.initial_bbox_size:.6f}")
        
        if self.z_only:
            print(f"  [Z-ONLY MODE: Preserving upright orientation]")
        
        self.debugger.checkpoint("optimization_start")
        self.debugger.log(f"Initial bbox size: {self.initial_bbox_size:.6f}")
        
        # Phase 1: Try learned presets
        if learned_presets and time.time() - start_time < max_time:
            print("→ Phase 1: Trying learned presets...")
            self._try_presets_as_offset(learned_presets[:10])
        
        # Phase 2: Coarse search (45° steps)
        if time.time() - start_time < max_time:
            print("→ Phase 2: Coarse search (45° steps)...")
            coarse = self.generator.generate_coarse()
            print(f"  Testing {len(coarse)} rotations...", end='', flush=True)
            self._try_presets_as_offset(coarse)
        
        # Phase 3: Medium search around best (15° steps)
        if time.time() - start_time < max_time and self.best_rotation:
            best_deg = radians_to_degrees(self.best_rotation)
            print(f"→ Phase 3: Medium search around ({best_deg[0]:.0f}°, {best_deg[1]:.0f}°, {best_deg[2]:.0f}°)...")
            medium = self.generator.generate_medium(best_deg)
            print(f"  Testing {len(medium)} rotations...", end='', flush=True)
            self._try_presets_absolute(medium)
        
        # Phase 4: Fine search around best (5° steps)
        if time.time() - start_time < max_time and self.best_rotation:
            best_deg = radians_to_degrees(self.best_rotation)
            print(f"→ Phase 4: Fine search around ({best_deg[0]:.0f}°, {best_deg[1]:.0f}°, {best_deg[2]:.0f}°)...")
            fine = self.generator.generate_fine(best_deg)
            print(f"  Testing {len(fine)} rotations...", end='', flush=True)
            self._try_presets_absolute(fine)
        
        # Phase 5: PCA alignment (skip in z_only mode)
        if self.use_pca and not self.z_only and time.time() - start_time < max_time:
            print("→ Phase 5: PCA alignment with smart Z-flip...")
            self._try_pca_rotation()
        
        # Phase 6: Fine-tune (gradient descent)
        if time.time() - start_time < max_time:
            print("→ Phase 6: Fine-tuning...")
            self._fine_tune_rotation()
        
        # Apply best rotation
        if self.best_rotation:
            self.obj.rotation_euler = self.best_rotation
            self._force_update()
        
        # Calculate results
        elapsed = time.time() - start_time
        reduction = ((self.initial_bbox_size - self.best_bbox_size) / self.initial_bbox_size) * 100
        
        best_deg = radians_to_degrees(self.best_rotation)
        print(f"\n✓ Optimization complete in {elapsed:.1f}s")
        print(f"  Best rotation: X={best_deg[0]:.2f}°, Y={best_deg[1]:.2f}°, Z={best_deg[2]:.2f}°")
        print(f"  Reduction: {reduction:.1f}%")
        
        self.debugger.checkpoint("optimization_complete")
        self.debugger.log(f"Final bbox size: {self.best_bbox_size:.6f}")
        self.debugger.log(f"Reduction: {reduction:.2f}%")
        
        return best_deg, reduction
    
    def _try_presets_as_offset(self, rotations_deg):
        """Try rotations as OFFSETS from initial rotation."""
        for i, rot_deg in enumerate(rotations_deg):
            rot_rad = degrees_to_radians(rot_deg)
            self._try_rotation_offset(rot_rad)
            
            if (i + 1) % 50 == 0:
                print('.', end='', flush=True)
        
        reduction = ((self.initial_bbox_size - self.best_bbox_size) / self.initial_bbox_size) * 100
        print(f" Done! Best: {reduction:.1f}% reduction")
    
    def _try_presets_absolute(self, rotations_deg):
        """Try rotations as ABSOLUTE values (not offsets)."""
        for i, rot_deg in enumerate(rotations_deg):
            rot_rad = degrees_to_radians(rot_deg)
            rotation_euler = Euler(rot_rad, 'XYZ')
            
            self.obj.rotation_euler = rotation_euler
            self._force_update()
            
            bbox_size = self._get_bbox_size()
            self.step_count += 1
            
            if bbox_size < self.best_bbox_size:
                self.best_bbox_size = bbox_size
                self.best_rotation = rotation_euler.copy()
            
            if (i + 1) % 50 == 0:
                print('.', end='', flush=True)
        
        reduction = ((self.initial_bbox_size - self.best_bbox_size) / self.initial_bbox_size) * 100
        print(f" Done! Best: {reduction:.1f}% reduction")
    
    def _try_rotation_offset(self, rotation_offset_rad):
        """Try a rotation OFFSET from initial rotation using matrix composition."""
        try:
            if isinstance(rotation_offset_rad, tuple):
                rotation_offset = Euler(rotation_offset_rad, 'XYZ')
            else:
                rotation_offset = rotation_offset_rad
            
            # Matrix composition: initial * offset = combined
            initial_mat = self.initial_rotation.to_matrix().to_4x4()
            offset_mat = rotation_offset.to_matrix().to_4x4()
            combined_mat = initial_mat @ offset_mat
            combined_euler = combined_mat.to_euler('XYZ')
            
            # Apply and measure
            self.obj.rotation_euler = combined_euler
            self._force_update()
            
            bbox_size = self._get_bbox_size()
            self.step_count += 1
            
            # Update best if better
            if bbox_size < self.best_bbox_size:
                self.best_bbox_size = bbox_size
                self.best_rotation = combined_euler.copy()
                
        except Exception as e:
            print(f"ERROR in _try_rotation_offset: {e}")
    
    def _try_pca_rotation(self):
        """Try PCA-based rotation alignment."""
        pca_euler = calculate_pca_rotation(self.obj)
        
        if pca_euler is None:
            return
        
        pca_deg = radians_to_degrees(pca_euler)
        print(f"  PCA result: X={pca_deg[0]:.1f}°, Y={pca_deg[1]:.1f}°, Z={pca_deg[2]:.1f}°")
        
        # Test PCA rotation and variants
        test_rotations = self.generator.generate_pca_variants(pca_euler)
        
        for rot in test_rotations:
            self.obj.rotation_euler = rot
            self._force_update()
            
            bbox_size = self._get_bbox_size()
            
            if bbox_size < self.best_bbox_size:
                self.best_bbox_size = bbox_size
                self.best_rotation = rot.copy()
                print(f"  PCA improved: bbox = {bbox_size:.6f}")
    
    def _fine_tune_rotation(self):
        """Fine-tune using gradient descent-like refinement."""
        if not self.best_rotation:
            return
        
        current_best = list(self.best_rotation)
        current_bbox = self.best_bbox_size
        
        # Decreasing step sizes
        if self.fast_mode:
            step_sizes = [5.0, 1.0, 0.1]
        else:
            step_sizes = self.adaptive_steps
        
        for step in step_sizes:
            step_rad = math.radians(step)
            improved = True
            iterations = 0
            max_iterations = 10 if self.fast_mode else 30
            
            while improved and iterations < max_iterations:
                improved = False
                iterations += 1
                
                # For z_only, only adjust Z axis
                axes = [2] if self.z_only else [0, 1, 2]
                
                for axis in axes:
                    for direction in [1, -1]:
                        test_rotation = current_best.copy()
                        test_rotation[axis] += direction * step_rad
                        
                        self.obj.rotation_euler = Euler(test_rotation, 'XYZ')
                        self._force_update()
                        
                        bbox_size = self._get_bbox_size()
                        
                        if bbox_size < current_bbox - 1e-9:
                            current_bbox = bbox_size
                            current_best = test_rotation.copy()
                            improved = True
        
        # Update if improved
        if current_bbox < self.best_bbox_size:
            self.best_bbox_size = current_bbox
            self.best_rotation = Euler(current_best, 'XYZ')
            rot_deg = radians_to_degrees(self.best_rotation)
            print(f"  Fine-tuned: X={rot_deg[0]:.2f}°, Y={rot_deg[1]:.2f}°, Z={rot_deg[2]:.2f}°")

