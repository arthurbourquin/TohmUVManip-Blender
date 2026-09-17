bl_info = {
    "name": "UV Manip",
    "author": "Tohm",
    "version": (0, 1, 0),
    "blender": (5, 2, 0),
    "location": "UV Editor > N-Panel > Tohm UV Manip",
    "description": "Graph-based UV manipulation tools",
    "category": "UV",
}

import bpy
from . import ui
from . import operators


classes = (
    ui.VIEW3D_PT_UvGraph_Pannel,

    operators.OBJECT_OT_PrintUvGraph,
    operators.OBJECT_OT_StraightenPaths,
    operators.OBJECT_OT_PutPathsEnBas,
    operators.OBJECT_OT_ReversePaths,
    operators.OBJECT_OT_AlignPathsOnGrid,
    operators.OBJECT_OT_SelectByAngle,
)


def register():
    for c in classes:
        bpy.utils.register_class(c)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
