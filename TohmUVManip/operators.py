import bpy
import bmesh
import math

from .UvGraph import UvGraph


#=========#=========#=========#=========#=========#=========#=========#=========
# FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

# HELPER

def get_bmesh_stuff():
    obj = bpy.context.active_object # working on uvs, we want the active object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    uvmap = bm.loops.layers.uv.active
    uvsync = bpy.context.scene.tool_settings.use_uv_select_sync
    return [obj, mesh, bm, uvmap, uvsync]


# FUNCTIONS

# Selection

def select_edges_by_angle(angle, tolerance, additive):
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
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

def straignten_paths():
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
    uvgraph = UvGraph(obj, mesh, bm, uvmap, sync)
    uvgraph.straignten_paths()
    bmesh.update_edit_mesh(mesh)

def reverse_paths():
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
    uvgraph = UvGraph(obj, mesh, bm, uvmap, sync)
    uvgraph.reverse_paths()
    bmesh.update_edit_mesh(mesh)

def align_paths_on_grid():
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
    uvgraph = UvGraph(obj, mesh, bm, uvmap, sync)
    uvgraph.align_paths_on_grid()
    bmesh.update_edit_mesh(mesh)


def put_path_en_bas():
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
    uvgraph = UvGraph(obj, mesh, bm, uvmap, sync)
    uvgraph.put_path_en_bas()
    bmesh.update_edit_mesh(mesh)


# Print

def print_uvgraph(verbosity):
    [obj, mesh, bm, uvmap, sync] = get_bmesh_stuff()
    uvgraph = UvGraph(obj, mesh, bm, uvmap, sync)
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
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        print_uvgraph(self.verbosity)
        return {'FINISHED'}


class OBJECT_OT_StraightenPaths(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_straignten_paths"
    bl_label = "Straighten Paths"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        straignten_paths()
        return {'FINISHED'}

class OBJECT_OT_ReversePaths(bpy.types.Operator):
    bl_idname = "tohm.reverse_paths"
    bl_label = "Reverse Paths"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        reverse_paths()
        return {'FINISHED'}

class OBJECT_OT_PutPathsEnBas(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_put_path_en_bas"
    bl_label = "Put Paths En Bas Wesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        put_path_en_bas()
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

    angle: bpy.props.FloatProperty(name="Angle", default=0.0)
    tolerance: bpy.props.FloatProperty(name="Tolerance", default=0.2)
    additive: bpy.props.BoolProperty(name="Additive", default=False)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        select_edges_by_angle(self.angle, self.tolerance, self.additive)
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True