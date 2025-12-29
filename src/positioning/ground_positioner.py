"""
Ground positioning utilities.
Centers and grounds objects at Z=0.
"""
import bpy
from mathutils import Vector


def position_at_ground_zero(obj):
    """
    Position an object so the bottom of its world-space bounding box is at Z=0.
    This properly handles rotated objects by calculating true world-space bounds.
    
    Args:
        obj: Blender mesh object
    """
    if obj.type != 'MESH':
        return
    
    try:
        mesh = obj.data
        if len(mesh.vertices) == 0:
            return
        
        # Force scene update to ensure transforms are current
        bpy.context.view_layer.update()
        
        # Get current location and matrix BEFORE calculating bounds
        current_loc = obj.location.copy()
        matrix_world = obj.matrix_world.copy()
        
        print(f"  Positioning {obj.name}:", flush=True)
        print(f"    Current location: ({current_loc.x:.4f}, {current_loc.y:.4f}, {current_loc.z:.4f})", flush=True)
        
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
        print(f"  ⚠️ Position error: {e}", flush=True)
        import traceback
        traceback.print_exc()


def move_to_origin_simple(obj):
    """
    Simple method to move object to origin (ground at Z=0, centered at X=0, Y=0).
    Uses numpy if available for speed.
    
    Args:
        obj: Blender mesh object
    """
    if obj.type != 'MESH':
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
            world_coords = [matrix_world @ v.co for v in mesh.vertices]
            min_x = min(v.x for v in world_coords)
            max_x = max(v.x for v in world_coords)
            min_y = min(v.y for v in world_coords)
            max_y = max(v.y for v in world_coords)
            min_z = min(v.z for v in world_coords)
        
        # Calculate center on X and Y
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        # Move object to origin
        obj.location.x -= center_x
        obj.location.y -= center_y
        obj.location.z -= min_z
        
        bpy.context.view_layer.update()
        
        print(f"✓ Moved to origin: ground at Z=0, centered at X=0, Y=0", flush=True)
        
    except Exception as e:
        print(f"⚠️ Could not move to origin: {e}", flush=True)

