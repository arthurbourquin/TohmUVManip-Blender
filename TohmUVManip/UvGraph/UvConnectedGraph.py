class UvConnectedGraph:
    def __init__(self):
        self.index = -1

        self.issingleton = False
        self.ispath = False
        self.isring = False
        self.istree = False
        self.ispartialmesh = False

        self.uvverts = {}
        self.root = None

        # for paths
        self.head = None
        self.tail = None
        self.sorted_uvverts = []

    @property
    def count(self): return len(self.uvverts.values())

    def get_center(self, mode):
        if mode == "head-tail":
            if self.ispath:
                u = (self.head.uv[0] + self.tail.uv[0]) / 2
                v = (self.head.uv[1] + self.tail.uv[1]) / 2
                return (u, v)
            else:
                return False                
        elif mode == "average":
            count = self.count
            u = sum([uvv.uv[0] for uvv in self.sorted_uvverts]) / count
            v = sum([uvv.uv[1] for uvv in self.sorted_uvverts]) / count
            return (u, v)
