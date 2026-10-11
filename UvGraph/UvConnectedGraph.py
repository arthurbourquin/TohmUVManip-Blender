from math import inf

from .UvEdge import UvEdge

class UvConnectedGraph:
    def __init__(self):
        self.index = -1

        self.issingleton = None
        self.ispath = None
        self.isring = None
        self.istree = None
        self.ispartialmesh = None
        self.iscyclic = None

        self.uvverts = {}
        self.count = None
        self.root = None

        self.degree = None
        self.uvedges = set()
        self.length = None
        self.center_median = None
        self.center_average = None
        self.bbox = None

        # for paths
        self.head = None
        self.tail = None
        self.sorted_uvverts = []

    def set_singleton(self):
        self.issingleton = True
        self.ispath = False
        self.isring = False
        self.istree = False
        self.ispartialmesh = False
        self.iscyclic = False
        self.degree = 0
        self.length = 0
        uv = self.uvverts.values()[0].uv
        self.center_median = uv
        self.center_average = uv
        self.bbox = [uv, uv]

    def set_single_edge(self):
        self.issingleton = False
        self.ispath = True
        self.isring = False
        self.istree = False
        self.ispartialmesh = False
        self.iscyclic = False
        self.degree = 1
        uvv1, uvv2 = self.uvverts.values()
        uvedge = UvEdge(uvv1, uvv2)
        self.uvedges.add(uvedge)
        self.length = uvedge.length
        u1, v1 = uvv1.uv
        u2, v2 = uvv2.uv
        cu = (u1 + u2) / 2
        cv = (v1 + v2) / 2
        self.center_median = (cu, cv)
        self.center_average = (cu, cv)
        self.bbox = [[min(u1, u2), min(v1, v2)], max(u1, u2), max(v1, v2)]

    def update(self):
        self.count = len(self.uvverts)

        if self.count == 1:
            self.set_singleton()
            return

        if self.count == 2:
            self.set_single_edge()
            return

        # uv edges
        self.degree = 1
        from collections import deque
        for uvv in self.uvverts.values():
            uvv.isvisited = False
        if self.count >= 2:
            queue = deque([self.root])
            while queue:
                uvv = queue.popleft()
                uvv.isvisited = True
                neighbors = uvv.neighbors.values()
                self.degree = max(self.degree, len(neighbors) - 1)
                for n in neighbors:
                    self.uvedges.add(UvEdge(uvv, n))
                    if not n.isvisited:
                        queue.append(n)
        # topology porperties
        self.iscyclic = len(self.uvedges) > (self.count - 1)
        self.istree = not self.iscyclic and self.degree >= 2
        self.ispath = not self.iscyclic and not self.istree and not self.issingleton
        self.isring = self.iscyclic and self.degree == 1
        self.ispartialmesh = self.iscyclic and self.degree > 1
        if self.ispath:
            self.sorted_uvverts = sorted(self.uvverts.values(), key=lambda uvv: uvv.depth)
            self.head = self.sorted_uvverts[0]
            self.tail = self.sorted_uvverts[self.count - 1]
        # values properties
        self.length = sum(uve.length for uve in self.uvedges)
        self.bbox = [[inf, inf], [-inf, -inf]]
        self.bbox[0][0] = min(uvv.uv[0] for uvv in self.uvverts.values())
        self.bbox[0][1] = min(uvv.uv[1] for uvv in self.uvverts.values())
        self.bbox[1][0] = max(uvv.uv[0] for uvv in self.uvverts.values())
        self.bbox[1][1] = max(uvv.uv[1] for uvv in self.uvverts.values())
        cau = sum(uvv.uv[0] for uvv in self.uvverts.values()) / self.count
        cav = sum(uvv.uv[1] for uvv in self.uvverts.values()) / self.count
        self.center_average = (cau, cav)
        cmu = sorted(self.uvverts.values(), key=lambda uvv: uvv.uv[0])[self.count // 2]
        cmv = sorted(self.uvverts.values(), key=lambda uvv: uvv.uv[1])[self.count // 2]
        self.center_median = (cmu, cmv)

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
