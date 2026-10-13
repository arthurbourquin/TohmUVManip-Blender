import bpy
import bmesh
import math

from .UvGraph.UvGraph import UvGraph


#=========#=========#=========#=========#=========#=========#=========#=========
# FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

# HELPER

def alert(message, title="Tohm UV Manip", icon='INFO'):
    def draw(self, context):
        for line in str(message).split("\n"):
            self.layout.label(text=line)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


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
    

# FUNCTIONS

# Selection

def select_edges_by_angle(angle, tolerance, additive):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    angle = (angle * math.pi / 180) % math.pi
    tolerance = (tolerance * math.pi / 180) % math.pi
    for f in bm.faces:
        for l in f.loops:
            u1, v1 = l[uvmap].uv
            u2, v2 = l.link_loop_next[uvmap].uv
            du = u2 - u1
            dv = v2 - v1
            if du == 0 and dv == 0:
                continue
            a = math.atan2(dv, du) % math.pi
            diff = abs(a - angle)
            diff = min(diff, math.pi - diff)
            select = diff < tolerance
            if select:
                l.uv_select_edge_set(True)
            elif not additive:
                l.uv_select_edge_set(False)
    bmesh.update_edit_mesh(mesh)



# Modification

def straighten_paths(keep_paths_length, even_point_distribution, center_mode):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.straighten_paths(keep_paths_length, even_point_distribution, center_mode)
    bmesh.update_edit_mesh(mesh)

def reverse_paths():
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.reverse_paths()
    bmesh.update_edit_mesh(mesh)

def align_paths_on_grid():
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.align_paths_on_grid()
    bmesh.update_edit_mesh(mesh)


# Print

def print_uvgraph(verbosity):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.print_self(verbosity)



#=========#=========#=========#=========#=========#=========#=========#=========
# OPERATORS
#=========#=========#=========#=========#=========#=========#=========#=========

class OBJECT_OT_PrintUvGraph(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_print"
    bl_label = "Print UvGraph"
    bl_options = {'REGISTER', 'UNDO'}

    verbosity: bpy.props.IntProperty(name="verbosity", default=0)

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        print_uvgraph(self.verbosity)
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True


class OBJECT_OT_StraightenPaths(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_straighten_paths"
    bl_label = "Straighten Paths"
    bl_options = {'REGISTER', 'UNDO'}

    keep_paths_length: bpy.props.BoolProperty(name="Keep Length", default=True)
    even_point_distribution: bpy.props.BoolProperty(name="Even Points Distribution", default=False)
    center_mode: bpy.props.EnumProperty(
        name="Center",
        items=[
            ('BBOX', "Bounding Box", "Use the center of the path's bounding box"),
            ('MEDIAN', "Median", "Use the median position of the path points"),
            ('AVERAGE', "Average", "Use the average position of the path points"),
            ('HEADTAIL', "Head-Tail Midpoint", "Use the midpoint between the head and tail of the path"),
        ],
        default='BBOX'
    )

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        straighten_paths(
            self.keep_paths_length,
            self.even_point_distribution,
            self.center_mode,
        )
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True

class OBJECT_OT_ReversePaths(bpy.types.Operator):
    bl_idname = "tohm.reverse_paths"
    bl_label = "Reverse Paths"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reverse_paths()
        return {'FINISHED'}


class OBJECT_OT_AlignPathsOnGrid(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_align_paths_on_grid"
    bl_label = "Align Paths On A Grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        align_paths_on_grid()
        return {'FINISHED'}

class OBJECT_OT_SelectByAngle(bpy.types.Operator):
    bl_idname = "tohm.select_edges_by_angle"
    bl_label = "Select Edges By Angle"
    bl_options = {'REGISTER', 'UNDO'}

    angle:     bpy.props.FloatProperty(name="Angle", default=0.0)
    tolerance: bpy.props.FloatProperty(name="Tolerance", default=0.2)
    additive:  bpy.props.BoolProperty( name="Additive", default=False)

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        select_edges_by_angle(self.angle, self.tolerance, self.additive)
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True