from mathutils import Vector

class UvVert:
    def __init__(self, uv, uvmap, index=-1, depth=-1, isvisited=False):
        self.uv = Vector(uv)
        self.uvmap = uvmap
        self.index = index
        self.depth = depth
        self.isvisited = isvisited

        self.select = False
        self.loops = set()  # set(BMLoop)
        self.neighbors = {} # {tuple(u,v): UvVert()}

        self.update()

    @property
    def u(self): return self.uv.x
    @property
    def v(self): return self.uv.y
    @property
    def x(self): return self.uv.x
    @property
    def y(self): return self.uv.y

    @property
    def isisolated(self): return len(self.neighbors.values()) == 0
    @property
    def isleaf(self): return len(self.neighbors.values()) <= 1
    @property
    def isroot(self): return self.depth == 0 or self.depth == -1

    def update(self):
        if self.depth == -1 and len(self.neighbors) == 0:
            self.depth = 0
        self.select = any(l.uv_select_vert for l in self.loops)


    def add_loop(self, loop):
        return self.loops.add(loop)
        self.update()

    def translate_to(self, uv):
        self.uv = Vector(uv)
        for l in self.loops:
            l[self.uvmap].uv = self.uv
        self.update()