"""
Generate rotation candidates for optimization.
Unified rotation generation with configurable granularity.
"""


class RotationGenerator:
    """Generate rotation candidates at various levels of granularity."""
    
    def __init__(self, z_only=False, fast_mode=False):
        """
        Initialize rotation generator.
        
        Args:
            z_only: Only generate Z-axis rotations
            fast_mode: Use faster but less thorough generation
        """
        self.z_only = z_only
        self.fast_mode = fast_mode
    
    def generate_coarse(self):
        """
        Generate coarse rotation offsets (45° steps).
        
        Returns:
            List of (x, y, z) rotation tuples in degrees
        """
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
    
    def generate_medium(self, center, radius=45, step=15):
        """
        Generate medium rotations around a center point.
        
        Args:
            center: (x, y, z) center rotation in degrees
            radius: Search radius in degrees
            step: Step size in degrees
            
        Returns:
            List of (x, y, z) rotation tuples in degrees
        """
        rotations = []
        cx, cy, cz = center
        
        if self.z_only:
            for z in range(int(cz - radius), int(cz + radius + 1), step):
                rotations.append((0, 0, z))
            return rotations
        
        if self.fast_mode:
            step = 30
            radius = 30
        
        for x in range(int(cx - radius), int(cx + radius + 1), step):
            for y in range(int(cy - radius), int(cy + radius + 1), step):
                for z in range(int(cz - radius), int(cz + radius + 1), step):
                    rotations.append((x, y, z))
        
        return rotations
    
    def generate_fine(self, center, radius=15, step=5):
        """
        Generate fine rotations around a center point.
        
        Args:
            center: (x, y, z) center rotation in degrees
            radius: Search radius in degrees
            step: Step size in degrees
            
        Returns:
            List of (x, y, z) rotation tuples in degrees
        """
        rotations = []
        cx, cy, cz = center
        
        if self.z_only:
            for z in range(int(cz - radius), int(cz + radius + 1), step):
                rotations.append((0, 0, z))
            return rotations
        
        if self.fast_mode:
            step = 15
            radius = 15
        
        for x in range(int(cx - radius), int(cx + radius + 1), step):
            for y in range(int(cy - radius), int(cy + radius + 1), step):
                for z in range(int(cz - radius), int(cz + radius + 1), step):
                    rotations.append((x, y, z))
        
        return rotations
    
    def generate_pca_variants(self, pca_euler):
        """
        Generate PCA rotation and 90° variants.
        
        Args:
            pca_euler: Base PCA Euler rotation
            
        Returns:
            List of Euler rotations
        """
        import math
        from mathutils import Euler
        
        variants = [
            pca_euler,
            Euler((pca_euler.x + math.pi/2, pca_euler.y, pca_euler.z)),
            Euler((pca_euler.x - math.pi/2, pca_euler.y, pca_euler.z)),
            Euler((pca_euler.x, pca_euler.y + math.pi/2, pca_euler.z)),
            Euler((pca_euler.x, pca_euler.y - math.pi/2, pca_euler.z)),
            Euler((pca_euler.x, pca_euler.y, pca_euler.z + math.pi/2)),
            Euler((pca_euler.x, pca_euler.y, pca_euler.z - math.pi/2)),
        ]
        
        return variants

