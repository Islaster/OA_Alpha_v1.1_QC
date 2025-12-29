"""
Rotation Optimizer - PRO v2.1 Algorithm
========================================
Multi-phase rotation optimization for bounding box minimization.
Uses PCA with smart Z-flip detection and pitch fine-tuning.

Mac-compatible version with cross-platform support.
"""
import math
import time

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

try:
    import bpy
    from mathutils import Euler, Matrix, Vector
    BLENDER_AVAILABLE = True
except ImportError:
    BLENDER_AVAILABLE = False

from utils import get_aabb_metrics, get_bounding_box_size, degrees_to_radians, radians_to_degrees
from debugger import get_debugger


class RotationOptimizer:
    """
    Multi-phase rotation optimizer for bounding box minimization.
    
    Optimization Strategy (from PRO v2.1):
        1. Coarse grid search (45° steps)
        2. Medium refinement (15° around best)
        3. Fine refinement (5° around best)
        4. PCA alignment with smart Z-flip
        5. Fine-tune (gradient descent)
    """
    
    def __init__(self, obj, config=None, z_only=False):
        """
        Initialize optimizer for an object.
        
        Args:
            obj: Blender mesh object to optimize
            config: Configuration dict
            z_only: If True, only rotate around Z-axis (preserve upright)
        """
        if not BLENDER_AVAILABLE:
            raise RuntimeError("This module requires Blender")
        
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
        self.common_presets = self.config.get("common_presets", [-90, -45, 0, 45, 90, 180])
        self.adaptive_steps = self.config.get("adaptive_steps", [5.0, 2.0, 1.0, 0.5, 0.2, 0.1])
        self.use_pca = self.config.get("use_pca_initial_guess", True)
        self.fast_mode = self.config.get("fast_mode", False)
        
        # Auto-enable fast mode for large meshes
        if obj.type == 'MESH':
            vert_count = len(obj.data.vertices)
            if vert_count > 50000 and not self.fast_mode:
                self.fast_mode = True
                print(f"  [Auto-enabled fast mode for {vert_count:,} vertices]")
        
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
        self.obj.update_tag(refresh={'OBJECT'})
        bpy.context.view_layer.update()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        depsgraph.update()
    
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
        
        # Force initial update
        self._force_update()
        self.initial_bbox_size = self._get_bbox_size()
        
        # Reset to initial state
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
            coarse = self._generate_coarse_rotations()
            print(f"  Testing {len(coarse)} rotations...", end='', flush=True)
            self._try_presets_as_offset(coarse)
        
        # Phase 3: Medium search around best (15° steps)
        if time.time() - start_time < max_time and self.best_rotation:
            best_deg = radians_to_degrees(self.best_rotation)
            print(f"→ Phase 3: Medium search around ({best_deg[0]:.0f}°, {best_deg[1]:.0f}°, {best_deg[2]:.0f}°)...")
            medium = self._generate_medium_rotations(best_deg)
            print(f"  Testing {len(medium)} rotations...", end='', flush=True)
            self._try_presets_absolute(medium)
        
        # Phase 4: Fine search around best (5° steps)
        if time.time() - start_time < max_time and self.best_rotation:
            best_deg = radians_to_degrees(self.best_rotation)
            print(f"→ Phase 4: Fine search around ({best_deg[0]:.0f}°, {best_deg[1]:.0f}°, {best_deg[2]:.0f}°)...")
            fine = self._generate_fine_rotations(best_deg)
            print(f"  Testing {len(fine)} rotations...", end='', flush=True)
            self._try_presets_absolute(fine)
        
        # Phase 5: PCA alignment with smart Z-flip (skip in z_only or fast mode)
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
    
    def _generate_coarse_rotations(self):
        """Generate coarse rotation offsets (45° steps)."""
        rotations = []
        
        if self.z_only:
            # Z-only: Only rotate around Z-axis
            z_angles = list(range(0, 360, 15))
            for z in z_angles:
                rotations.append((0, 0, z))
            return rotations
        
        if self.fast_mode:
            angles = [0, 45, 90, 180]
        else:
            angles = [0, 45, -45, 90, -90, 180]
        
        for x in angles:
            for y in angles:
                for z in angles:
                    if (x, y, z) not in rotations:
                        rotations.append((x, y, z))
        
        return rotations
    
    def _generate_medium_rotations(self, center):
        """Generate medium rotations around a center point (15° steps)."""
        rotations = []
        cx, cy, cz = center
        
        if self.z_only:
            step = 15
            radius = 30
            for z in range(int(cz - radius), int(cz + radius + 1), step):
                rotations.append((0, 0, z))
            return rotations
        
        if self.fast_mode:
            step = 30
            radius = 30
        else:
            step = 15
            radius = 45
        
        for x in range(int(cx - radius), int(cx + radius + 1), step):
            for y in range(int(cy - radius), int(cy + radius + 1), step):
                for z in range(int(cz - radius), int(cz + radius + 1), step):
                    rotations.append((x, y, z))
        
        return rotations
    
    def _generate_fine_rotations(self, center):
        """Generate fine rotations around a center point (5° steps)."""
        rotations = []
        cx, cy, cz = center
        
        if self.z_only:
            step = 5
            radius = 15
            for z in range(int(cz - radius), int(cz + radius + 1), step):
                rotations.append((0, 0, z))
            return rotations
        
        if self.fast_mode:
            step = 15
            radius = 15
        else:
            step = 5
            radius = 15
        
        for x in range(int(cx - radius), int(cx + radius + 1), step):
            for y in range(int(cy - radius), int(cy + radius + 1), step):
                for z in range(int(cz - radius), int(cz + radius + 1), step):
                    rotations.append((x, y, z))
        
        return rotations
    
    def _try_presets_as_offset(self, rotations_deg):
        """
        Try rotations as OFFSETS from initial rotation.
        Uses proper matrix composition.
        """
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
        """
        Try a rotation OFFSET from initial rotation.
        
        Uses matrix composition: final_rotation = initial_rotation @ offset_rotation
        """
        try:
            # Ensure Euler object
            if isinstance(rotation_offset_rad, tuple):
                rotation_offset = Euler(rotation_offset_rad, 'XYZ')
            else:
                rotation_offset = rotation_offset_rad
            
            # MATRIX COMPOSITION: initial * offset = combined
            initial_mat = self.initial_rotation.to_matrix().to_4x4()
            offset_mat = rotation_offset.to_matrix().to_4x4()
            combined_mat = initial_mat @ offset_mat
            
            # Extract final Euler
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
        """
        Use PCA with smart Z-flip detection and pitch fine-tuning.
        
        This is the key algorithm from PRO v2.1 that gives the best results:
        1. Calculate PCA axes from vertex distribution
        2. Test base rotation AND 180° X-flip
        3. Choose orientation with largest "bottom footprint"
        4. Fine-tune pitch ±5° to minimize height
        """
        if not NUMPY_AVAILABLE:
            print("  PCA: numpy not available")
            return
        
        if self.obj.type != 'MESH':
            return
        
        try:
            mesh = self.obj.data
            vert_count = len(mesh.vertices)
            
            if vert_count < 3:
                return
            
            # Get vertex coordinates
            coords = np.empty(vert_count * 3, dtype=np.float32)
            mesh.vertices.foreach_get('co', coords)
            coords = coords.reshape((vert_count, 3))
            
            # Calculate centroid and center
            mean = np.mean(coords, axis=0)
            centered = coords - mean
            
            # Covariance matrix + SVD for PCA
            cov = np.cov(centered.T)
            u, s, vh = np.linalg.svd(cov)
            
            # PCA matrix (eigenvectors as columns)
            pca_mat = Matrix(u.tolist()).to_4x4()
            
            # Base rotation (aligns PCA axes to World axes)
            base_rot_mat = pca_mat.inverted()
            base_euler = base_rot_mat.to_euler('XYZ')
            
            # === SMART Z-FLIP DETECTION ===
            # Test two candidates: base rotation and flipped (180° around X)
            candidates = [base_euler]
            
            flip_x = Matrix.Rotation(math.radians(180), 4, 'X')
            flipped_mat = flip_x @ base_rot_mat
            candidates.append(flipped_mat.to_euler('XYZ'))
            
            # Choose candidate with largest "bottom footprint"
            best_cand = base_euler
            best_score = -1
            
            for i, rot in enumerate(candidates):
                rot_mat = rot.to_matrix().to_4x4()
                
                # Transform coordinates
                ones = np.ones((len(coords), 1))
                local_coords = np.hstack([coords, ones])
                transformed = local_coords @ np.array(rot_mat.transposed())
                transformed = transformed[:, :3]
                
                # Find bottom 10% slice
                min_z = transformed[:, 2].min()
                height = transformed[:, 2].max() - min_z
                threshold = min_z + (height * 0.1)
                
                mask = transformed[:, 2] < threshold
                bottom_points = transformed[mask]
                
                if len(bottom_points) < 3:
                    score = 0
                else:
                    # Approximate footprint area of bottom slice
                    min_xy = bottom_points[:, :2].min(axis=0)
                    max_xy = bottom_points[:, :2].max(axis=0)
                    dims = max_xy - min_xy
                    score = dims[0] * dims[1]  # Area of bottom slice AABB
                
                print(f"  PCA Candidate {i}: Bottom Score = {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_cand = rot
            
            # === FINE-TUNE PITCH ===
            # Rotate around width axis to minimize Z height
            
            # Apply best candidate to get transformed coords
            rot_mat = best_cand.to_matrix().to_4x4()
            ones = np.ones((len(coords), 1))
            local_coords = np.hstack([coords, ones])
            transformed = local_coords @ np.array(rot_mat.transposed())
            transformed = transformed[:, :3]
            
            # Determine width axis (X or Y, whichever is smaller = width)
            mins = transformed.min(axis=0)
            maxs = transformed.max(axis=0)
            dims = maxs - mins
            
            if dims[0] < dims[1]:
                rotation_axis = 'X'
            else:
                rotation_axis = 'Y'
            
            print(f"  Fine-tuning pitch around {rotation_axis} axis...")
            
            # Search ±5 degrees in 0.2° increments
            best_angle = 0
            min_z_height = dims[2]
            
            for angle in range(-50, 51, 2):
                deg = angle / 10.0
                rad = math.radians(deg)
                
                # Apply rotation mathematically (faster than matrix ops)
                if rotation_axis == 'X':
                    c, s = math.cos(rad), math.sin(rad)
                    new_z = transformed[:, 1] * s + transformed[:, 2] * c
                else:
                    c, s = math.cos(rad), math.sin(rad)
                    new_z = -transformed[:, 0] * s + transformed[:, 2] * c
                
                h = new_z.max() - new_z.min()
                
                if h < min_z_height:
                    min_z_height = h
                    best_angle = rad
            
            print(f"  Pitch correction: {math.degrees(best_angle):.2f}°")
            
            # Apply correction
            if rotation_axis == 'X':
                corr_mat = Matrix.Rotation(best_angle, 4, 'X')
            else:
                corr_mat = Matrix.Rotation(best_angle, 4, 'Y')
            
            final_mat = corr_mat @ best_cand.to_matrix().to_4x4()
            pca_euler = final_mat.to_euler('XYZ')
            
            pca_deg = radians_to_degrees(pca_euler)
            print(f"  PCA result: X={pca_deg[0]:.1f}°, Y={pca_deg[1]:.1f}°, Z={pca_deg[2]:.1f}°")
            
            # Test PCA rotation and 90° variants
            test_rotations = [
                pca_euler,
                Euler((pca_euler.x + math.pi/2, pca_euler.y, pca_euler.z)),
                Euler((pca_euler.x - math.pi/2, pca_euler.y, pca_euler.z)),
                Euler((pca_euler.x, pca_euler.y + math.pi/2, pca_euler.z)),
                Euler((pca_euler.x, pca_euler.y - math.pi/2, pca_euler.z)),
                Euler((pca_euler.x, pca_euler.y, pca_euler.z + math.pi/2)),
                Euler((pca_euler.x, pca_euler.y, pca_euler.z - math.pi/2)),
            ]
            
            for rot in test_rotations:
                self.obj.rotation_euler = rot
                self._force_update()
                
                bbox_size = self._get_bbox_size()
                
                if bbox_size < self.best_bbox_size:
                    self.best_bbox_size = bbox_size
                    self.best_rotation = rot.copy()
                    rot_deg = radians_to_degrees(rot)
                    print(f"  PCA improved: bbox = {bbox_size:.6f}")
                    
        except Exception as e:
            print(f"  PCA failed: {e}")
            import traceback
            traceback.print_exc()
    
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
