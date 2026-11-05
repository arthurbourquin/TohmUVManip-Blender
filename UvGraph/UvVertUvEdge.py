# python
from __future__ import annotations
from math import atan2, sqrt

# blender
from mathutils import Vector



class UvVerts:
    def __init__(self, uvmap):
        self.uvverts: dict[tuple[float, float], UvVert] = {}
        self.uvmap = uvmap

    # mimicking regular dict
    def __getitem__(self, uv): return self.uvverts[tuple(uv)]
    def __setitem__(self, uv, uvv): self.uvverts[tuple(uv)] = uvv
    def __delitem__(self, uv): del self.uvverts[tuple(uv)]
    def __contains__(self, uv): return uv in self.uvverts
    from collections.abc import KeysView, ValuesView, ItemsView
    def keys(self):   return self.uvverts.keys()
    def values(self): return self.uvverts.values()
    def items(self):  return self.uvverts.items()
    def __len__(self): return len(self.uvverts)

    # cutsom
    def add(self, uvv):
        uvvkey = uvv.uv
        if not uvvkey in self.uvverts:
            self.uvverts[uvvkey] = uvv

    def get_or_create(self, uv):
        uv = tuple(uv)
        if uv not in self.uvverts:
            self.uvverts[uv] = UvVert(uv, self.uvmap)
        return self.uvverts[uv]



class UvVert:
    def __init__(self, uv, uvmap, index=-1, depth=-1, isvisited=False):
        self.uv = tuple(uv)
        self.uvmap = uvmap
        self.index = index
        self.depth = depth
        self.isvisited = isvisited

        self.select = False
        self.loops = set()  # set(BMLoop)
        self.neighbors = UvVerts(uvmap)
        self.uvedges = UvEdges(uvmap)

        self.update_select()

    @property
    def u(self): return self.uv[0]
    @property
    def v(self): return self.uv[1]
    @property
    def x(self): return self.uv[0]
    @property
    def y(self): return self.uv[1]

    @property
    def isisolated(self): return not self.neighbors
    @property
    def isleaf(self): return len(self.neighbors) <= 1
    @property
    def isroot(self): return self.depth == 0 or self.depth == -1

    def update_select(self):
        for l in self.loops:
            case_a = l.uv_select_vert
            case_b = l.uv_select_edge
            case_c = l.link_loop_prev.uv_select_edge
            self.select = any([case_a, case_b, case_c])

    def add_loop(self, loop):
        self.loops.add(loop)
        self.update_select()

    def move(self, uv):
        uv = tuple(uv)
        self.uv = uv
        for l in self.loops:
            l[self.uvmap].uv = uv


























def order_pair(uvv_pair):
    uvva, uvvb = uvv_pair
    au, av = uvva.uv
    bu, bv = uvvb.uv
    if au == bu and av == bv:
        raise AssertionError("Identical uvvert pair coordinates")
        return
    if au != bu:
        if   au < bu: return (uvva, uvvb)
        elif au > bu: return (uvvb, uvva)
    else:
        if   av < bv: return (uvva, uvvb)
        elif av > bv: return (uvvb, uvva)


class UvEdges:
    def __init__(self, uvmap):
        self.uvedges: dict[tuple[UvVert, UvVert], UvEdge] = {}
        self.uvmap = uvmap

    # mimicking regular dict
    def __getitem__(self, uvv_pair): return self.uvedges[order_pair(uvv_pair)]
    def __setitem__(self, uvv_pair, uve): self.uvedges[order_pair(uvv_pair)] = uve
    def __delitem__(self, uvv_pair): del self.uvedges[order_pair(uvv_pair)]
    def __contains__(self, uvv_pair): return order_pair(uvv_pair) in self.uvedges
    from collections.abc import KeysView, ValuesView, ItemsView
    def keys(self):   return self.uvedges.keys()
    def values(self): return self.uvedges.values()
    def items(self):  return self.uvedges.items()
    def __len__(self): return len(self.uvedges)

    # custom
    def add(self, uve):
        uvekey = (uve.uvv1, uve.uvv2)
        if not uvekey in self.uvedges:
            self.uvedges[uvekey] = uve

    def get_or_create(self, uvv_pair):
        uvv_pair = order_pair(uvv_pair)
        if uvv_pair in self.uvedges:
            return self.uvedges[uvv_pair]
        else:
            uvv1, uvv2 = uvv_pair
            self.uvedges[uvv_pair] = UvEdge(uvv1, uvv2, self.uvmap)
            return self.uvedges[uvv_pair]



class UvEdge:
    def __init__(self, uvv_a, uvv_b, uvmap):
        self.uvv1, self.uvv2 = order_pair((uvv_a, uvv_b))
        self.uvmap = uvmap
        self.select = None

        self.update_select()

    @property
    def key(self): return (self.uvv1, self.uvv2)

    @property
    def vecdir(self):
        return Vector(self.uvv2.uv) - Vector(self.uvv1.uv)
    @property
    def length(self):
        vec = self.vecdir
        return sqrt(vec.x ** 2 + vec.y ** 2)
    @property
    def angle(self):
        vec = self.vecdir
        return atan2(vec.y, vec.x)

    def __eq__(self, other): # for using uve1 == uve2
        if not isinstance(other, UvEdge):
            return NotImplemented
        return self.uvv1 is other.uvv1 and self.uvv2 is other.uvv2

    def __hash__(self): # needed for set/dict usage
        return hash(self.key)


    def update_select(self):
        self.select = False
        for l in self.uvv1.loops:
            if l.uv_select_edge and l.link_loop_next[self.uvmap].uv == self.uvv2.uv:
                self.select = True
                break
        if not self.select:
            for l in self.uvv2.loops:
                if l.uv_select_edge and l.link_loop_next[self.uvmap].uv == self.uvv1.uv:
                    self.select = True
                    break
