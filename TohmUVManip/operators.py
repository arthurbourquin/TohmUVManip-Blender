import bpy
import bmesh
import math

from .UvGraph.UvGraph import UvGraph


#=========#=========#=========#=========#=========#=========#=========#=========
# FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

# HELPER

def get_bmesh_stuff():
    prefix = 'UvGraph issue: '
    valid = True
    obj = mesh = bm = uvmap = uvsync = None

    obj = bpy.context.active_object # working on uvs, we want the active object
    if obj is None:
        valid = False
        print(f"{prefix}No active object")
    if valid and obj.type != "MESH":
        valid = False
        print(f"{prefix}Active object is not a mesh: {obj.type}")
    if valid and obj.mode != "EDIT":
        valid = False
        print(f"{prefix}Can only run in Edit Mode")

    if valid:
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        uvmap = bm.loops.layers.uv.active

    if valid and uvmap is None:
        valid = False
        print(f"{prefix}Mesh has no UV map")

    if valid:
        uvsync = bpy.context.scene.tool_settings.use_uv_select_sync

    return [valid, obj, mesh, bm, uvmap, uvsync]
    

# FUNCTIONS

# Selection

def select_edges_by_angle(angle, tolerance, additive):
    [valid, obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    if not valid: return
    if sync: bm.uv_select_sync_from_mesh()
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
    if sync: bm.uv_select_sync_to_mesh()
    bmesh.update_edit_mesh(mesh)



# Modification

def straighten_paths(center, keeplength):
    print('wesh Blender Development')
    [valid, obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    if not valid: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap, uvsync)
    uvgraph.straighten_paths(center, keeplength)
    bmesh.update_edit_mesh(mesh)

def reverse_paths():
    [valid, obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    if not valid: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap, uvsync)
    uvgraph.reverse_paths()
    bmesh.update_edit_mesh(mesh)

def align_paths_on_grid():
    [valid, obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    if not valid: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap, uvsync)
    uvgraph.align_paths_on_grid()
    bmesh.update_edit_mesh(mesh)


# Print

def print_uvgraph(verbosity):
    [valid, obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    if not valid: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap, uvsync)
    uvgraph.print_self(verbosity)



#=========#=========#=========#=========#=========#=========#=========#=========
# OPERATORS
#=========#=========#=========#=========#=========#=========#=========#=========

class OBJECT_OT_PrintUvGraph(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_print"
    bl_label = "Print UV Graph"
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

    keeplength:   bpy.props.BoolProperty(name="Keep Length", default=False)

    center: bpy.props.EnumProperty(
        name="Center",
        items=[
            ('BBOX', "Bounding Box", "Use the bounding box center"),
            ('HEADTAIL', "Head-Tail", "Use head-tail midpoint"),
        ],
        default='BBOX'
    )

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        straighten_paths(self.center, self.keeplength)
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
    bl_label = "Select By Angle"
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