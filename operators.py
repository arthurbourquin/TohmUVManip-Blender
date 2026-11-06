# python
import math

# Blender
import bpy
import bmesh

# Tohm UV Manip
from . import UvGraph
from . import utils










#=========#=========#=========#=========#=========#=========#=========#=========
# OPERATORS
#=========#=========#=========#=========#=========#=========#=========#=========

class OBJECT_OT_SelectByAngle(bpy.types.Operator):
    bl_idname = "tohm.select_edges_by_angle"
    bl_label = "Select Edges By Angle"
    bl_options = {'REGISTER', 'UNDO'}

    angle:     bpy.props.FloatProperty(name="Angle (deg)", default=0.0)
    tolerance: bpy.props.FloatProperty(name="Tolerance (deg)", default=30)
    additive:  bpy.props.BoolProperty( name="Additive", default=False)

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        angle = (self.angle * math.pi / 180) % math.pi
        tolerance = (self.tolerance * math.pi / 180) % math.pi
        if not self.additive:
            for f in bm.faces:
                for l in f.loops:
                    l.uv_select_edge_set(False)
                    l.uv_select_vert_set(False)
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
                if diff < tolerance:
                    l.uv_select_edge_set(True)
                    l.uv_select_vert_set(True)
                    l.link_loop_next.uv_select_vert_set(True)
        bmesh.update_edit_mesh(mesh)
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True










#=========#=========#=========#=========#=========#=========#=========#=========
# OPERATORS USING UVGRAPH
#=========#=========#=========#=========#=========#=========#=========#=========

class OBJECT_OT_PrintUvGraph(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_print"
    bl_label = "Print UvGraph"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        uvmesh = UvGraph.UvMesh(obj, mesh, bm, uvmap)
        message = UvGraph.print_uvmesh(uvmesh)
        utils.alert(message)
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
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        uvmesh = UvGraph.UvMesh(obj, mesh, bm, uvmap)
        UvGraph.straighten_paths(
            uvmesh,
            self.keep_paths_length,
            self.even_point_distribution,
            self.center_mode
        )
        bmesh.update_edit_mesh(mesh)
        return {'FINISHED'}

    def check(self, context):
        self.execute(context)
        return True



class OBJECT_OT_ReversePaths(bpy.types.Operator):
    bl_idname = "tohm.reverse_paths"
    bl_label = "Reverse Paths"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        uvmesh = UvGraph.UvMesh(obj, mesh, bm, uvmap)
        UvGraph.reverse_paths(uvmesh)
        bmesh.update_edit_mesh(mesh)
        return {'FINISHED'}



class OBJECT_OT_AlignPaths(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_align_paths"
    bl_label = "Align Paths"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        uvmesh = UvGraph.UvMesh(obj, mesh, bm, uvmap)
        UvGraph.align_paths(uvmesh)
        bmesh.update_edit_mesh(mesh)
        return {"FINISHED"}



class OBJECT_OT_AlignPathsOnGrid(bpy.types.Operator):
    bl_idname = "tohm.uvgraph_align_paths_on_grid"
    bl_label = "Align Paths On A Grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        [obj, mesh, bm, uvmap] = utils.get_bmesh_stuff()
        if not obj: return {'CANCELLED'}
        uvmesh = UvGraph.UvMesh(obj, mesh, bm, uvmap)
        UvGraph.align_paths_on_grid(uvmesh)
        bmesh.update_edit_mesh(mesh)
        return {'FINISHED'}