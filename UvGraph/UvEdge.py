from math import sqrt, atan2
from __future__ import annotations

from mathutils import Vector



class UvEdges:
    def __init__(self, uvmap):
        #                             (u1     v1)          (u2     v2)      uvedge
        self.uvedges: dict[tuple[tuple[float, float], tuple[float, float]], UvEdge] = {}
        self.uvmap = uvmap

    # mimicing regular dict
    def __getitem__(self, pair):
        if pair in self.uvedges:
            return self.uvedges[pair] # 1. pair exist
        else:
            uvv1, uvv2 = pair
            return self.uvedges[(uvv2, uvv1)] # 2. flip exist 3. neither pair nor flip exists

    def __setitem__(self, pair, uve):
        a = 1

    def __delitem__(self, pair):
        a = 1

    def __contains__(self, pair):
        a = 1

    from collections.abc import KeysView, ValuesView, ItemsView
    def keys(self):   return self.uvedges.keys()
    def values(self): return self.uvedges.values()
    def items(self):  return self.uvedges.items()
    def __len__(self): return len(self.uvedges)

    # custom
    def get_or_create(self, pair):
        a = 1


class UvEdge:
    def __init__(self, uvv_a, uvv_b, uvmap):
        self.uvv1 = None # UvVert()
        self.uvv2 = None # UvVert()
        self.uvmap = uvmap
        self.select = None

        if uvv_a.u < uvv_b.u:
            self.uvv1 = uvv_a
            self.uvv2 = uvv_b
        elif uvv_a.u > uvv_b.u:
            self.uvv1 = uvv_b
            self.uvv2 = uvv_a
        else:
            if uvv_a.v < uvv_b.v:
                self.uvv1 = uvv_a
                self.uvv2 = uvv_b
            elif uvv_a.v > uvv_b.v:
                self.uvv1 = uvv_b
                self.uvv2 = uvv_a
            else:
                raise AssertionError("UvEdge made of UvVerts considered identicals")

        # Taking loops
        #      o----o       UvEdge (single)
        #      o--> o-->    Clockwise loops (0 or more)
        #   <--o <--o       Anticlockwise loops (0 or more)
        l_candidates = set(self.uvv1.loops) | set(self.uvv2.loops)
        loops = set()
        for l in l_candidates:
            if l.uv_select_edge == True:
                co1 = l[self.uvmap].uv
                co2 = l.link_loop_next[self.uvmap].uv
                # access uvedges really need a dict... so WIP

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
        return hash((self.uvv1, self.uvv2))