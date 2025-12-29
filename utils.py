"""
Utility functions for bounding box minimization.
Mac-compatible version with cross-platform path handling.
"""
import json
import os
from pathlib import Path
from mathutils import Vector, Matrix
import bmesh
import bpy


def normalize_path(path_str):
    """Normalize path for cross-platform compatibility."""
    if path_str is None:
        return None
    return str(Path(path_str).resolve())


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


def apply_rotation(obj, rotation_euler):
    """Apply rotation to an object."""
    obj.rotation_euler = rotation_euler


def degrees_to_radians(degrees):
    """Convert degrees to radians."""
    import math
    return tuple(math.radians(d) for d in degrees)


def radians_to_degrees(radians):
    """Convert radians to degrees."""
    import math
    return tuple(math.degrees(r) for r in radians)


def load_json_file(filepath, default=None):
    """Load JSON file, return default if file doesn't exist."""
    if default is None:
        default = {}
    
    filepath = normalize_path(filepath) if filepath else filepath
    
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return default
    return default


def save_json_file(filepath, data):
    """Save data to JSON file."""
    filepath = normalize_path(filepath)
    
    # Ensure directory exists
    file_path = Path(filepath)
    if file_path.parent != Path('.'):
        file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def get_mesh_vertices(obj):
    """Get all vertices of a mesh object in world space."""
    if obj.type != 'MESH':
        return []
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    
    vertices = [v.co.copy() for v in bm.verts]
    bm.free()
    
    return vertices


def get_face_areas(obj):
    """Get all face areas of a mesh object."""
    if obj.type != 'MESH':
        return []
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bm.faces.ensure_lookup_table()
    
    face_data = []
    for face in bm.faces:
        area = face.calc_area()
        normal = face.normal.copy()
        center = face.calc_center_median()
        face_data.append((face.index, area, normal, center))
    
    bm.free()
    return face_data


def ensure_object_selected(obj):
    """Ensure an object is selected and active."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

