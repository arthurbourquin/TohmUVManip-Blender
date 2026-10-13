import bpy
import bmesh



def alert(message, title="Tohm UV Manip", icon='INFO'):
    def draw(self, context):
        for line in str(message).split("\n"):
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


"""
def switch_off_uvsync(bm):
    # turn off uvsync
    bpy.context.tool_settings.use_uv_select_sync = False
    # in 3D View only, select all (vtx, edg, fce)
    # for v in bm.verts: v.select_set(True) # not working: select all in UV Editor (don't know why)
    # for e in bm.edges: e.select_set(True) # not working: select all in UV Editor (don't know why)
    # for f in bm.faces: f.select_set(True) # not working: select all in UV Editor (don't know why)
    # for v in bm.verts: v.select = True    # same shit
    bmesh.update_edit_mesh(bpy.context.active_object.data)
"""


def get_bmesh_stuff():
    _FAIL = (None, None, None, None)
    if bpy.context.tool_settings.use_uv_select_sync == True:
        alert("Tohm UV Manip doesn't work in UV Sync Selection mode")
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
    uvmap = bm.loops.layers.uv.active
    if not uvmap:
        alert("Mesh has no UV map")
        return _FAIL

    return obj, mesh, bm, uvmap