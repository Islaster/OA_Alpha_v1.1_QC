"""
Bounding box calculation utilities.
Provides fast AABB calculations with numpy acceleration and Python fallback.
"""
import bpy
from mathutils import Vector


def get_aabb_metrics(obj, sample_rate=1):
    """
    Get axis-aligned bounding box metrics for an object.
    
    This is the primary function for calculating bounding box information.
    Uses numpy for fast computation when available, falls back to pure Python.
    
    Args:
        obj: Blender mesh object
        sample_rate: Use every Nth vertex (1 = all, 2 = every other, etc.)
                    Higher values = faster but less accurate
    
    Returns:
        dict with keys:
            - volume: Total bounding box volume (width * depth * height)
            - footprint: XY area (width * depth) - important for ground stability
            - width: X dimension
            - depth: Y dimension  
            - height: Z dimension
            - dims: Tuple of (width, depth, height)
            - min_point: (min_x, min_y, min_z)
            - max_point: (max_x, max_y, max_z)
        
        Returns None if object has no vertices.
    """
    # Force scene update to get current transforms
    bpy.context.view_layer.update()
    
    mesh = obj.data
    matrix = obj.matrix_world
    
    if not mesh.vertices:
        return None
    
    try:
        import numpy as np
        return _get_aabb_numpy(mesh, matrix, sample_rate)
    except ImportError:
        return _get_aabb_python(mesh, matrix, sample_rate)


def _get_aabb_numpy(mesh, matrix, sample_rate):
    """Fast numpy-based AABB calculation."""
    import numpy as np
    
    vert_count = len(mesh.vertices)
    
    # Get all vertex coordinates efficiently
    coords = np.empty(vert_count * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape((vert_count, 3))
    
    # Sample vertices if requested (for large meshes)
    if sample_rate > 1 and vert_count > 1000:
        indices = np.arange(0, vert_count, sample_rate)
        coords = coords[indices]
    
    # Transform to world space using matrix multiplication
    mat = np.array([list(row) for row in matrix])
    
    # Add homogeneous coordinate (w=1) for 4x4 matrix multiplication
    ones = np.ones((len(coords), 1), dtype=np.float32)
    coords_h = np.hstack([coords, ones])
    
    # Transform: (N, 4) @ (4, 4).T = (N, 4)
    world = coords_h @ mat.T
    
    # Extract XYZ and find bounds
    min_xyz = world[:, :3].min(axis=0)
    max_xyz = world[:, :3].max(axis=0)
    
    min_x, min_y, min_z = min_xyz
    max_x, max_y, max_z = max_xyz
    
    # Calculate dimensions
    width = max_x - min_x    # X
    depth = max_y - min_y    # Y
    height = max_z - min_z   # Z
    
    volume = width * depth * height
    footprint = width * depth  # XY area (ground plane)
    
    return {
        "volume": float(volume),
        "footprint": float(footprint),
        "width": float(width),
        "depth": float(depth),
        "height": float(height),
        "dims": (float(width), float(depth), float(height)),
        "min_point": (float(min_x), float(min_y), float(min_z)),
        "max_point": (float(max_x), float(max_y), float(max_z))
    }


def _get_aabb_python(mesh, matrix, sample_rate):
    """Pure Python AABB calculation (fallback when numpy unavailable)."""
    # Transform vertices to world space
    world_verts = [matrix @ v.co for v in mesh.vertices[::sample_rate]]
    
    if not world_verts:
        return None
    
    # Find bounds
    min_x = min(v.x for v in world_verts)
    max_x = max(v.x for v in world_verts)
    min_y = min(v.y for v in world_verts)
    max_y = max(v.y for v in world_verts)
    min_z = min(v.z for v in world_verts)
    max_z = max(v.z for v in world_verts)
    
    # Calculate dimensions
    width = max_x - min_x
    depth = max_y - min_y
    height = max_z - min_z
    
    volume = width * depth * height
    footprint = width * depth
    
    return {
        "volume": volume,
        "footprint": footprint,
        "width": width,
        "depth": depth,
        "height": height,
        "dims": (width, depth, height),
        "min_point": (min_x, min_y, min_z),
        "max_point": (max_x, max_y, max_z)
    }


def get_bounding_box_volume(obj, sample_rate=1):
    """
    Get bounding box volume and dimensions.
    
    Convenience wrapper for legacy compatibility.
    
    Args:
        obj: Blender mesh object
        sample_rate: Vertex sampling rate
    
    Returns:
        tuple: (volume, (width, depth, height))
    """
    metrics = get_aabb_metrics(obj, sample_rate)
    if metrics is None:
        return 0, (0, 0, 0)
    return metrics['volume'], metrics['dims']


def get_bounding_box_size(obj, sample_rate=1):
    """Get the size (volume) of the bounding box."""
    return get_bounding_box_volume(obj, sample_rate)[0]


def get_min_z(obj):
    """
    Get the minimum Z coordinate in world space.
    Useful for positioning objects on the ground.
    """
    metrics = get_aabb_metrics(obj)
    if metrics is None:
        return 0
    return metrics['min_point'][2]


def get_center_xy(obj):
    """Get the center point in XY plane."""
    metrics = get_aabb_metrics(obj)
    if metrics is None:
        return (0, 0)
    
    min_x, min_y, _ = metrics['min_point']
    max_x, max_y, _ = metrics['max_point']
    
    return ((min_x + max_x) / 2, (min_y + max_y) / 2)

