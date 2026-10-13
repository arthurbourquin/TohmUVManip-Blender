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

        self.uvverts = {} # {(u, v): uvvert}
        self.uvedges = set() # ((uvv1, uvv2)) ; UvEdge(a, b) == UvEdge(b, a)

        self.root = None # uvvert

        self.degree = None
        self.length = None

        # for paths
        self.head = None
        self.tail = None
        self.sorted_uvverts = []
        self.sorted_uvedges = []

    def set_singleton(self):
        self.issingleton = True
        self.ispath = False
        self.isring = False
        self.istree = False
        self.ispartialmesh = False
        self.iscyclic = False
        self.degree = 0
        self.length = 0

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

    def update(self):
        count = len(self.uvverts)

        if count == 1:
            self.set_singleton()
            return

        if count == 2:
            self.set_single_edge()
            return

        # uv edges
        self.degree = 1
        from collections import deque
        for uvv in self.uvverts.values():
            uvv.isvisited = False
        if count >= 2:
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
        self.iscyclic = len(self.uvedges) > (count - 1)
        self.istree = not self.iscyclic and self.degree >= 2
        self.ispath = not self.iscyclic and not self.istree and not self.issingleton
        self.isring = self.iscyclic and self.degree == 1
        self.ispartialmesh = self.iscyclic and self.degree > 1
        if self.ispath:
            self.sorted_uvverts = sorted(self.uvverts.values(), key=lambda uvv: uvv.depth)
            self.head = self.sorted_uvverts[0]
            self.tail = self.sorted_uvverts[count - 1]
            edges_by_vertices = {frozenset((edge.uvv1, edge.uvv2)): edge for edge in self.uvedges}
            self.sorted_uvedges = [
                edges_by_vertices[frozenset((a, b))]
                for a, b in zip(
                    self.sorted_uvverts,
                    self.sorted_uvverts[1:]
                )
            ]
        self.length = sum(uve.length for uve in self.uvedges)


    def get_center(self, mode):
        uvvs = list(self.uvverts)
        if mode == "BBOX":
            [[mu, mv], [Mu, Mv]] = self.get_bounding_box(uvvs)
            return [(mu + Mu) / 2, (mv + Mv) / 2]
        elif mode == "MEDIAN":
            mid = len(uvvs) // 2
            u = sorted([uvv[0] for uvv in uvvs])[mid]
            v = sorted([uvv[1] for uvv in uvvs])[mid]
            return [u, v]
        elif mode == "AVERAGE":
            count = len(uvvs)
            us = [uvv[0] for uvv in uvvs]
            vs = [uvv[1] for uvv in uvvs]
            return [sum(us) / count, sum(vs) / count]
        elif mode == "HEADTAIL":
            if not self.ispath:
                print("Can't get head-tail midpoint: UvConnectedGraph is not a path.")
                return None
            return [(self.head.x + self.tail.x) / 2, (self.head.y + self.tail.y) / 2]
        else:
            print(f"Unknown center mode: {mode}")
            return None
