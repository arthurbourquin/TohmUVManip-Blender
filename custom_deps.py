import bpy
import bmesh

from .utils import alert, get_bmesh_stuff
from .UvGraph.UvGraph import UvGraph



#==========#==========#==========#==========#==========#==========#==========#==========
# MODIFICATIONS
#==========#==========#==========#==========#==========#==========#==========#==========

def straighten_paths(keep_paths_length, even_point_distribution, center_mode, orthogonalize):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.straighten_paths(keep_paths_length, even_point_distribution, center_mode, orthogonalize)
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



#==========#==========#==========#==========#==========#==========#==========#==========
# INFOS / PRINT
#==========#==========#==========#==========#==========#==========#==========#==========

def print_uvgraph(verbosity):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj: return
    uvgraph = UvGraph(obj, mesh, bm, uvmap)
    uvgraph.print_self(verbosity)
