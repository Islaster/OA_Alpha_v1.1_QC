"""
3D file export with multiple format support.
"""
import logging
from pathlib import Path
from typing import Optional
import bpy

from src.security.validators import validate_file_path, ALLOWED_3D_FORMATS, ValidationError


logger = logging.getLogger(__name__)


def export_object(
    obj: bpy.types.Object,
    output_path: str | Path,
    format: Optional[str] = None,
    use_selection: bool = True
) -> None:
    """
    Export object to file.
    
    Args:
        obj: Blender object to export
        output_path: Output file path
        format: Override format (default: detect from extension)
        use_selection: Export only selected objects
    
    Raises:
        ValidationError: If output path is invalid
        RuntimeError: If export fails
    """
    # Validate output path
    try:
        validated_path = validate_file_path(
            output_path,
            purpose="export",
            must_exist=False,
            allowed_extensions=ALLOWED_3D_FORMATS | {'.blend'}
        )
        output_path = str(validated_path)
    except ValidationError as e:
        logger.error(f"Invalid output path: {e}")
        raise
    ext = Path(output_path).suffix.lower() if format is None else f".{format}"
    
    # Ensure object is selected
    if use_selection:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    
    try:
        if ext == '.blend':
            _export_blend(output_path)
        elif ext == '.obj':
            _export_obj(output_path, use_selection)
        elif ext == '.fbx':
            _export_fbx(output_path, use_selection)
        elif ext == '.ply':
            _export_ply(output_path, use_selection)
        elif ext in ['.gltf', '.glb']:
            _export_gltf(output_path, use_selection)
        else:
            raise ValueError(f"Unsupported format: {ext}")
        
        logger.info(f"Exported to {output_path}")
        
    except Exception as e:
        logger.error(f"Failed to export {output_path}: {e}")
        raise


def _export_blend(filepath):
    """Export as .blend file."""
    bpy.ops.wm.save_as_mainfile(filepath=filepath)


def _export_obj(filepath, use_selection):
    """Export as .obj file."""
    try:
        # Blender 4.0+ OBJ export
        bpy.ops.wm.obj_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            global_scale=1.0,
            apply_modifiers=True,
            export_triangulated_mesh=False
        )
    except (AttributeError, RuntimeError) as e:
        # Blender 3.x OBJ export
        logger.debug(f"Blender 4.0+ OBJ export failed: {e}, trying Blender 3.x method")
        bpy.ops.export_scene.obj(
            filepath=filepath,
            use_selection=use_selection,
            use_materials=True,
            global_scale=1.0
        )


def _export_fbx(filepath, use_selection):
    """Export as .fbx file."""
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=use_selection,
        global_scale=1.0,
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False
    )


def _export_ply(filepath, use_selection):
    """Export as .ply file."""
    try:
        # Blender 4.0+ PLY export
        bpy.ops.wm.ply_export(
            filepath=filepath,
            export_selected_objects=use_selection,
            global_scale=1.0
        )
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Blender 4.0+ PLY export failed: {e}, trying Blender 3.x method")
        try:
            # Blender 3.x PLY export
            bpy.ops.export_mesh.ply(filepath=filepath)
        except Exception as e2:
            logger.debug(f"Blender 3.x PLY export failed: {e2}, enabling addon and retrying")
            # Enable addon and retry
            try:
                import addon_utils
                addon_utils.enable("io_mesh_ply", default_set=True, persistent=True)
                bpy.ops.export_mesh.ply(filepath=filepath)
            except Exception as e3:
                logger.error(f"PLY export failed after all fallback methods: {e3}")
                raise


def _export_gltf(filepath, use_selection):
    """Export as .gltf/.glb file."""
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        use_selection=use_selection,
        export_apply_modifiers=True
    )


def export_collection_objects(collection_name, base_path, export_format):
    """
    Export all objects in a collection.
    
    Args:
        collection_name: Name of collection to export
        base_path: Base output path (without extension)
        export_format: File format (.obj, .fbx, etc.)
    
    Returns:
        Path to exported file or None if collection not found
    """
    collection = None
    for col in bpy.data.collections:
        if collection_name in col.name:
            collection = col
            break
    
    if not collection or len(collection.objects) == 0:
        return None
    
    # Select all objects in collection
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
    
    # Export
    export_path = f"{base_path}{export_format}"
    
    try:
        if export_format == '.obj':
            _export_obj(export_path, use_selection=True)
        elif export_format == '.fbx':
            _export_fbx(export_path, use_selection=True)
        elif export_format == '.ply':
            _export_ply(export_path, use_selection=True)
        elif export_format in ['.gltf', '.glb']:
            _export_gltf(export_path, use_selection=True)
        
        return export_path
    except Exception as e:
        logger.warning(f"Failed to export collection {collection_name}: {e}")
        return None

