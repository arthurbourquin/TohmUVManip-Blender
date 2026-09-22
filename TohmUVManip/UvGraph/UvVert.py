print("### UvVert.py RELOADED ###")

class UvVert:
    def __init__(self, uvmap):
        self.uv = None
        self.loops = set()
        self.neighbors = {}
        self.index = -1
        self.depth = -1
        self.select = False
        self.uvmap = uvmap
        self.isvisited = False # utility for each BFS

    @property
    def isleaf(self): return len(self.neighbors.values()) <= 1
    @property
    def isisolated(self): return len(self.neighbors.values()) == 0
    @property
    def isroot(self): return self.depth == 0 or self.depth == -1

    def add_loop(self, loop):
        return self.loops.add(loop)

    def update_select(self):
        self.select = any(l.uv_select_vert for l in self.loops)

    def set_uv(self, u, v):
        self.uv = (u, v)
        for l in self.loops:
            l[self.uvmap].uv = (u, v)