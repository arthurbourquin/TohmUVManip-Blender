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
        self.uvedges = None
        self.length = None
        self.center_median = None
        self.center_average = None
        self.bbox = None

        # for paths
        self.head = None
        self.tail = None
        self.sorted_uvverts = []

    def update(self):
        print(self.uvverts)
        self.count = len(self.uvverts)
        # uv edges
        self.uvedges = []
        self.degree = 0
        from collections import deque
        if self.count >= 2:
            queue = deque([self.root])
            def walk(uvv):
                d = uvv.depth
                children = [
                    child
                    for child in uvv.neighbors.values()
                    if child.depth == d + 1
                ]
                self.degree = max(self.degree, len(children))
                for c in children:
                    self.uvedges.append(UvEdge(uvv, c))
                queue.extend(children)
            while queue:
                uvv = queue.popleft()
                walk(uvv)
        # topology porperties
        self.issingleton = self.count == 1
        self.iscyclic = len(self.uvedges) > self.count - 1
        self.istree = not self.iscyclic and self.degree >= 2
        self.ispath = not self.iscyclic and not self.istree and not self.issingleton
        self.isring = self.iscyclic and not self.istree
        self.ispartialmesh = self.iscyclic and self.istree
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
