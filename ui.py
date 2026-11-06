import bpy


class VIEW3D_PT_UvGraph_Pannel(bpy.types.Panel):
    name = "Tohm UV Manip"
    bl_label = name
    bl_idname = "VIEW3D_PT_UvGraph_Pannel"
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'UI'
    bl_category = name

    def draw(self, context):
        layout = self.layout
        layout.label(text="Selection")
        layout.operator("tohm.select_edges_by_angle")
        layout.label(text="Paths Modifications")
        layout.operator("tohm.uvgraph_straighten_paths")
        layout.operator("tohm.reverse_paths")
        layout.operator("tohm.uvgraph_align_paths")
        layout.operator("tohm.uvgraph_align_paths_on_grid")
        layout.label(text="Grid Modifications")
        layout.operator("tohm.uvgraph_align_grids")
        layout.label(text="Informations")
        layout.operator("tohm.uvgraph_print")

# · • – — ← → ↑ ↓ ○ ● □ ■ △ ◇ ± × ÷ ≠ ≤ ≥ ≈ ° Ø × ✓
