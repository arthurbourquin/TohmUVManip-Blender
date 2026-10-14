from mathutils import Vector, Matrix
from math import sin, cos, atan2, sqrt


def lerp(a, b, w):
    return a * (1 - w) + b * w


def dist(uvv1, uvv2):
    du = uvv1.uv[0] - uvv2.uv[0]
    dv = uvv1.uv[1] - uvv2.uv[1]
    return sqrt(du*du + dv*dv)


def get_angle(uvv1, uvv2): # [-pi,pi]
    du, dv = Vector(uvv2.uv) - Vector(uvv1.uv)
    return atan2(dv, du)


def get_bounding_box(uvvs):
    us = [uvv.u for uvv in uvvs]
    vs = [uvv.v for uvv in uvvs]
    return [[min(us), min(vs)], [max(us), max(vs)]]


def get_center(cgrph, mode):
    uvvs = list(cgrph.uvverts.values())
    if mode == "BBOX":
        [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
        uv = ((mu + Mu) / 2, (mv + Mv) / 2)
        return Vector(uv)
    elif mode == "MEDIAN":
        mid = len(uvvs) // 2
        u = sorted([uvv.u for uvv in uvvs])[mid]
        v = sorted([uvv.v for uvv in uvvs])[mid]
        uv = (u, v)
        return Vector(uv)
    elif mode == "AVERAGE":
        count = len(uvvs)
        us = [uvv.u for uvv in uvvs]
        vs = [uvv.v for uvv in uvvs]
        uv = (sum(us) / count, sum(vs) / count)
        return Vector(uv)
    elif mode == "HEADTAIL":
        if not cgrph.ispath:
            print("Can't get head-tail midpoint: UvConnectedGraph is not a path.")
            return None
        return (cgrph.head.uv + cgrph.tail.uv) / 2
    else:
        print(f"Unknown center mode: {mode}")
        return None