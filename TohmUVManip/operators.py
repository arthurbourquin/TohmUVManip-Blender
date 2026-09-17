import bpy
import bmesh

from .UvGraph import UvGraph


#=========#=========#=========#=========#=========#=========#=========#=========
# FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

# HELPER

def get_bmesh_stuff():
    obj = bpy.context.active._object # working on uvs, we want the active object
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    uvmap = bm.loops.layers.uv.active
    uvsync = bpy.context.scene.tool_settings.use_uv_select_sync
    return [obj, mesh, bm, uvmap, uvsync]


# FUNCTIONS

def print_uvgraph():
    [obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    uvgraph = UvGraph(bm)
    uvgraph.print_self(0)


def straighten():
    [obj, mesh, bm, uvmap, uvsync] = get_bmesh_stuff()
    uvgraph = UvGraph(bm)
    uvgraph.straighten()
    bmesh.update_edit_mesh(mesh)


#=========#=========#=========#=========#=========#=========#=========#=========
# OPERATORS
#=========#=========#=========#=========#=========#=========#=========#=========

class OBJECT_OT_PrintUvGraph(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_print"
    bl_label = "Print UV Graph"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        print_uvgraph()
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