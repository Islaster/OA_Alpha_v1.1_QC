"""
3D file loading with multiple format support and fallback methods.
SECURITY: Input validation and sanitization applied.
"""
import os
import time
import logging
from pathlib import Path
import bpy

from src.security.validators import validate_3d_file_path, ValidationError
from src.security.error_handler import secure_function, SecureError


logger = logging.getLogger(__name__)


@secure_function(error_code='file_read_error', user_message="Unable to load 3D file")
def load_object(filepath):
    """
    Load a 3D object from file (SECURE VERSION).
    
    Supports: .obj, .fbx, .ply, .blend, .gltf, .glb
    
    Args:
        filepath: Path to object file
        
    Returns:
        Blender object or None
        
    Raises:
        SecureError: If validation fails or file cannot be loaded
    """
    # SECURITY: Validate file path
    try:
        validated_path = validate_3d_file_path(filepath, must_exist=True)
        filepath = str(validated_path)
    except ValidationError as e:
        raise SecureError(
            "Invalid file path provided",
            f"File validation failed: {e}",
            'invalid_input'
        )
    ext = os.path.splitext(filepath)[1].lower()
    
    print(f"Loading {ext.upper()} file...", flush=True)
    load_start = time.time()
    
    # Clear existing meshes
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    
    try:
        if ext == '.blend':
            obj = _load_blend(filepath)
        elif ext == '.obj':
            obj = _load_obj(filepath)
        elif ext == '.fbx':
            obj = _load_fbx(filepath)
        elif ext == '.ply':
            obj = _load_ply(filepath)
        elif ext in ['.gltf', '.glb']:
            obj = _load_gltf(filepath)
        else:
            # Try generic import
            bpy.ops.wm.open_mainfile(filepath=filepath)
            obj = _get_first_object()
        
        if obj is None:
            return None
        
        load_time = time.time() - load_start
        vert_count = len(obj.data.vertices) if obj.type == 'MESH' else 0
        print(f"✓ Loaded in {load_time:.1f}s ({vert_count:,} vertices)", flush=True)
        
        return obj
        
    except Exception as e:
        logger.error(f"Failed to load {filepath}: {e}")
        return None


def _load_blend(filepath):
    """Load from .blend file."""
    with bpy.data.libraries.load(filepath) as (data_from, data_to):
        data_to.objects = data_from.objects
    
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
            return obj
    return None


def _load_obj(filepath):
    """Load .obj file with version-specific methods."""
    try:
        # Blender 4.0+ uses wm.obj_import
        bpy.ops.wm.obj_import(filepath=filepath)
    except AttributeError:
        try:
            # Blender 3.x and earlier
            bpy.ops.import_scene.obj(filepath=filepath)
        except:
            # Manual OBJ loading as fallback
            logger.warning("Using manual OBJ import method")
            _manual_obj_import(filepath)
    
    return _get_first_object()


def _manual_obj_import(filepath):
    """Manual OBJ file import as fallback."""
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


def _load_fbx(filepath):
    """Load .fbx file."""
    bpy.ops.import_scene.fbx(filepath=filepath)
    return _get_first_object()


def _load_ply(filepath):
    """Load .ply file with fallback methods."""
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
                logger.error("PLY import failed. Please ensure PLY import addon is enabled.")
                raise
    
    return _get_first_object()


def _load_gltf(filepath):
    """Load .gltf/.glb file."""
    bpy.ops.import_scene.gltf(filepath=filepath)
    return _get_first_object()


def _get_first_object():
    """Get the first imported object from scene."""
    if bpy.context.selected_objects:
        return bpy.context.selected_objects[0]
    elif bpy.context.scene.objects:
        return bpy.context.scene.objects[0]
    return None

