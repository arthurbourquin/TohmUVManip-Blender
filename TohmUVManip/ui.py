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
        layout.operator("tohm.uvgraph_print", text="Print UvCorn")
        layout.operator("tohm.uvgraph_straighten", text="Straighten Path")
