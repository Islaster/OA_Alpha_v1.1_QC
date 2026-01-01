"""
Ground positioning utilities.
Centers and grounds objects at Z=0.
"""
import bpy
from mathutils import Vector, Matrix


def position_at_ground_zero(obj):
    """
    Position an object so:
      - the bottom of its WORLD-space bounding box rests at Z=0
      - the WORLD-space AABB center is at X=0, Y=0

    This version applies the translation in WORLD space (matrix_world),
    so it remains correct even if the object is parented/instanced/etc.
    It also uses evaluated mesh data (modifiers included).
    """
    if obj is None or obj.type != "MESH":
        return

    try:
        # Ensure transforms are current
        try:
            bpy.context.view_layer.update()
        except Exception:
            pass

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)

        # Evaluated mesh (includes modifiers)
        mesh_eval = obj_eval.to_mesh()
        if mesh_eval is None or len(mesh_eval.vertices) == 0:
            try:
                obj_eval.to_mesh_clear()
            except Exception:
                pass
            return

        mw = obj_eval.matrix_world

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        for v in mesh_eval.vertices:
            w = mw @ v.co
            if w.x < min_x: min_x = w.x
            if w.x > max_x: max_x = w.x
            if w.y < min_y: min_y = w.y
            if w.y > max_y: max_y = w.y
            if w.z < min_z: min_z = w.z
            if w.z > max_z: max_z = w.z

        # AABB center in world space
        center_x = (min_x + max_x) * 0.5
        center_y = (min_y + max_y) * 0.5

        print(f"  Positioning {obj.name}:", flush=True)
        print(f"    World bounds: X[{min_x:.4f},{max_x:.4f}] Y[{min_y:.4f},{max_y:.4f}] Z[{min_z:.4f},{max_z:.4f}]", flush=True)
        print(f"    World center: ({center_x:.4f}, {center_y:.4f}), min_z={min_z:.4f}", flush=True)

        # World-space delta to move center->(0,0) and min_z->0
        delta = Vector((-center_x, -center_y, -min_z))

        # Apply delta in world space
        # (Matrix.Translation(delta) @ matrix_world) moves object in world coords
        obj.matrix_world = Matrix.Translation(delta) @ obj.matrix_world

        try:
            bpy.context.view_layer.update()
        except Exception:
            pass

        # --- Verify both XY center and Z grounding ---
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval2 = obj.evaluated_get(depsgraph)
        mesh_eval2 = obj_eval2.to_mesh()
        mw2 = obj_eval2.matrix_world

        vws = [mw2 @ v.co for v in mesh_eval2.vertices]
        new_min_z = min(v.z for v in vws)
        new_min_x = min(v.x for v in vws)
        new_max_x = max(v.x for v in vws)
        new_min_y = min(v.y for v in vws)
        new_max_y = max(v.y for v in vws)
        new_cx = (new_min_x + new_max_x) * 0.5
        new_cy = (new_min_y + new_max_y) * 0.5

        print(f"    Verified: center=({new_cx:.6f},{new_cy:.6f}), min_z={new_min_z:.6f}", flush=True)

        # Tight correction if needed
        if abs(new_min_z) > 0.001 or abs(new_cx) > 0.001 or abs(new_cy) > 0.001:
            corr = Vector((-new_cx, -new_cy, -new_min_z))
            obj.matrix_world = Matrix.Translation(corr) @ obj.matrix_world
            try:
                bpy.context.view_layer.update()
            except Exception:
                pass
            print("    ⚠️ Applied final correction pass.", flush=True)

        # cleanup evaluated meshes
        try:
            obj_eval.to_mesh_clear()
        except Exception:
            pass
        try:
            obj_eval2.to_mesh_clear()
        except Exception:
            pass

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

