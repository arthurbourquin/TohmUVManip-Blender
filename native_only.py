import bpy
import bmesh
import math

from .utils import alert, get_bmesh_stuff



def select_edges_by_angle(angle, tolerance, additive):
    [obj, mesh, bm, uvmap] = get_bmesh_stuff()
    if not obj:
        return

    ts = bpy.context.tool_settings
    ts.mesh_select_mode = (False, True,  False)
    ts.uv_select_mode = 'EDGE'

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

    bmesh.update_edit_mesh(mesh)