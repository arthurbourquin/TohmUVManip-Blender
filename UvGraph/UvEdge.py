from __future__ import annotations
from math import sqrt, atan2
from mathutils import Vector

from .UvVert import UvVert

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
