# python
from math import atan2, sqrt

# Blender
import bpy
import bmesh
from mathutils import Vector










def alert(message, title="Tohm UV Manip", icon='INFO'):
    if isinstance(message, list):
        lines = [str(msg) for msg in message]
    elif isinstance(message, str):
        lines = message.split("\n")
    else:
        lines = [str(message)]
    def draw(self, context):
        for l in lines:
            self.layout.label(text=l)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)










def get_bmesh_stuff():
    _FAIL = (None, None, None, None)
    if bpy.context.tool_settings.use_uv_select_sync == True:
        bpy.context.tool_settings.use_uv_select_sync == False
        alert("Tohm UV Manip doesn't support UV Sync Select mode.\nTurn it off to work with the addon.", )
        return _FAIL
    obj = bpy.context.active_object
    if obj is None:
        alert("No active object")
        return _FAIL
    if obj.type != "MESH":
        alert(f"Active object is not a mesh: {obj.type}")
        return _FAIL
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    uvmap = bm.loops.layers.uv.active
    if not uvmap:
        alert("Mesh has no UV map")
        return _FAIL

    return obj, mesh, bm, uvmap





















