import bpy


class VIEW3D_PT_UvGraph_Pannel(bpy.types.Panel):
    name = "UvGraph"
    bl_label = name
    bl_idname = "VIEW3D_PT_UvGraph_Pannel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = name

    def draw(self, context):
        layout = self.layout
        layout.operator("tohm.uvgraph_straighten_paths", text="Straighten Path")
        layout.operator("tohm.reverse_paths", text="Reverse Paths")
        layout.operator("tohm.uvgraph_align_paths_on_grid", text="Grid Align")
        layout.operator("tohm.select_edges_by_angle", text="Select By Angle")
        layout.operator("tohm.uvgraph_print", text="Diagnostics")
