"""
PCA-based rotation alignment for optimal bounding box orientation.
Uses Principal Component Analysis to find the best-aligned rotation.
"""
import math
import logging


logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None


def calculate_pca_rotation(obj):
    """
    Calculate PCA-based rotation for an object.
    
    Uses smart Z-flip detection and pitch fine-tuning for best results.
    
    Args:
        obj: Blender mesh object
        
    Returns:
        Euler rotation or None if PCA unavailable/failed
    """
    if not NUMPY_AVAILABLE:
        logger.info("PCA: numpy not available")
        return None
    
    if obj.type != 'MESH':
        return None
    
    try:
        from mathutils import Matrix, Euler
        
        mesh = obj.data
        vert_count = len(mesh.vertices)
        
        if vert_count < 3:
            return None
        
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
        
        # Smart Z-flip detection: test base and flipped orientations
        best_euler = _choose_best_orientation(base_rot_mat, coords)
        
        # Fine-tune pitch to minimize height
        final_euler = _fine_tune_pitch(best_euler, coords)
        
        return final_euler
        
    except Exception as e:
        logger.warning(f"PCA failed: {e}")
        return None


def _choose_best_orientation(base_rot_mat, coords):
    """
    Choose between base rotation and 180° X-flip.
    Selects orientation with largest "bottom footprint".
    
    Args:
        base_rot_mat: Base rotation matrix
        coords: Vertex coordinates
        
    Returns:
        Best Euler rotation
    """
    from mathutils import Matrix, Euler
    
    base_euler = base_rot_mat.to_euler('XYZ')
    
    # Test candidates: base and X-flipped
    candidates = [base_euler]
    
    flip_x = Matrix.Rotation(math.radians(180), 4, 'X')
    flipped_mat = flip_x @ base_rot_mat
    candidates.append(flipped_mat.to_euler('XYZ'))
    
    # Choose candidate with largest bottom footprint
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
    
    return best_cand


def _fine_tune_pitch(euler, coords):
    """
    Fine-tune pitch (rotation around width axis) to minimize Z height.
    
    Args:
        euler: Initial Euler rotation
        coords: Vertex coordinates
        
    Returns:
        Fine-tuned Euler rotation
    """
    from mathutils import Matrix, Euler
    
    # Apply euler to get transformed coords
    rot_mat = euler.to_matrix().to_4x4()
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
    
    final_mat = corr_mat @ euler.to_matrix().to_4x4()
    return final_mat.to_euler('XYZ')

