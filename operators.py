import bpy
import bmesh
import math

from .UvGraph.UvGraph import UvGraph
from .native_only import select_edges_by_angle
from .custom_deps import straighten_paths, reverse_paths, align_paths_on_grid, print_uvgraph


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
    orthogonalize: bpy.props.BoolProperty(name="Orthogonalize Paths", default=False)

    def invoke(self, context, event):
        return self.execute(context)

    def execute(self, context):
        straighten_paths(
            self.keep_paths_length,
            self.even_point_distribution,
            self.center_mode,
            self.orthogonalize
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