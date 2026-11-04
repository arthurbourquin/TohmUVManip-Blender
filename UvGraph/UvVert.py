from __future__ import annotations

from mathutils import Vector


# naming: UvVert(s), uvvert(s), uvv(s)


class UvVerts:
    def __init__(self, uvmap):
        self.uvverts: dict[tuple[float, float], UvVert] = {}
        self.uvmap = uvmap

    # mimicing regular dict
    def __getitem__(self, uv): return self.uvverts[tuple(uv)]
    def __setitem__(self, uv, uvv): self.uvverts[tuple(uv)] = uvv
    def __delitem__(self, uv): del self.uvverts[tuple(uv)]
    def __contains__(self, uv): return uv in self.uvverts
    from collections.abc import KeysView, ValuesView, ItemsView
    def keys(self):   return self.uvverts.keys()
    def values(self): return self.uvverts.values()
    def items(self):  return self.uvverts.items()

    # custom
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
        self.neighbors = {} # {tuple(u,v): UvVert()}

        self.update()

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

    def update(self):
        if len(self.neighbors) == 0:
            self.depth = 0
        self.select = any(l.uv_select_vert for l in self.loops)

    def add_loop(self, loop):
        self.loops.add(loop)
        self.update()