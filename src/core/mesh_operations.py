"""
Mesh operations including vertex and face queries.
"""
import bpy
import bmesh
from mathutils import Vector


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
    """Get all face areas of a mesh object with normals and centers."""
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


def force_scene_update():
    """Force Blender to update all objects and transforms."""
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()


def force_object_update(obj):
    """Force update of a specific object."""
    obj.update_tag(refresh={'OBJECT'})
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    depsgraph.update()

