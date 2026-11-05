# python
from math import atan2, pi
from collections import deque

# Blender
from mathutils import Vector, Matrix

# Tohm UV Manip
from .UvVertUvEdge import UvVert, UvVerts, UvEdge, UvEdges
from .utils import lerp, dist, get_center



class UvConnectedGraph:
    def __init__(self, uvmap):
        self.uvmap = uvmap
        self.index = -1

        self.isgrid = None
        self.ispartialmesh = None
        self.iscyclic = None

        self.uvverts = UvVerts(uvmap)
        self.uvedges = UvEdges(uvmap)

        self.root = None

        # for paths
        self.head = None
        self.tail = None
        self.sorted_uvverts = []
        self.sorted_uvedges = []

    @property
    def degree(self): return max([len(uvv.neighbors) for uvv in self.uvverts.values()], default=0)
    @property
    def length(self): return sum([uve.length for uve in self.uvedges.values()])

    @property
    def issingleton(self): return len(self.uvverts) == 1
    @property
    def istree(self):
        return len(self.uvverts) == len(self.uvedges) + 1
    @property
    def ispath(self):
        return len(self.uvverts) >= 2 and self.istree and self.degree <= 2
    @property
    def isring(self):
        return len(self.uvverts) >= 3 and all(len(v.neighbors) == 2 for v in self.uvverts.values())

    def set_unvisited(self, uvvs):
        for uvv in uvvs:
            uvv.isvisited = False

    def update_keys(self):
        new_uvverts = UvVerts(self.uvmap)
        for uvv in self.uvverts.values():
            new_uvverts[uvv.uv] = uvv
        self.uvverts = new_uvverts

    def init(self):
        uvv_count = len(self.uvverts)

        if uvv_count == 1:
            self.set_singleton()
            return

        # visiting uvvs
        # uv edges
        self.degree = 1
        self.set_unvisited(self.uvverts.values())
        if uvv_count >= 2:
            queue = deque([self.root])
            while queue:
                uvv = queue.popleft()
                uvv.isvisited = True
                neighbors = uvv.neighbors.values()
                self.degree = max(self.degree, len(neighbors) - 1)
                for n in neighbors:
                    self.uvedges.add(UvEdge(uvv, n, self.uvmap))
                    if not n.isvisited:
                        queue.append(n)
        self.length = sum(uve.length for uve in self.uvedges)

        # topology porperties
        self.iscyclic = len(self.uvedges) > (uvv_count - 1)
        self.istree = not self.iscyclic and self.degree >= 2
        self.ispath = not self.iscyclic and not self.istree and not self.issingleton
        self.isring = self.iscyclic and self.degree == 1
        self.ispartialmesh = self.iscyclic and self.degree > 1

        # path
        if self.ispath:
            self.sorted_uvverts = sorted(self.uvverts.values(), key=lambda uvv: uvv.depth)
            self.head = self.sorted_uvverts[0]
            self.tail = self.sorted_uvverts[uvv_count - 1]
            edges_by_vertices = {frozenset((edge.uvv1, edge.uvv2)): edge for edge in self.uvedges}
            self.sorted_uvedges = [
                edges_by_vertices[frozenset((a, b))]
                for a, b in zip(
                    self.sorted_uvverts,
                    self.sorted_uvverts[1:]
                )
            ]

        # check if is grid WIP...












    #=========#=========#=========#=========#=========#=========#=========#=========
    # MODIFICATION
    #=========#=========#=========#=========#=========#=========#=========#=========

    def reverse_path(self):
        if not self.ispath:
            return False
        self.sorted_uvverts.reverse()
        for i, uvv in enumerate(self.sorted_uvverts):
            uvv.depth = i
        self.head, self.tail = self.tail, self.head
        return True

    def rotate(self, angle, center):
        center = Vector(center)
        m2 = Matrix.Rotation(angle, 2)
        for uvv in self.uvverts.values():
            old_pos = Vector(uvv.uv)
            new_pos = center + m2 @ (old_pos - center)
            uvv.move(new_pos)
        self.update_keys()

    def straighten_path(self, keep_paths_length, even_point_distribution, center_mode):
        uv_head = Vector(self.head.uv)
        uv_tail = Vector(self.tail.uv)
        htcenter = (uv_head + uv_tail) / 2
        target_center = get_center(self, center_mode)
        offset = target_center - htcenter
        htdist = dist(self.head, self.tail)
        if keep_paths_length:
            ratio = self.length / htdist
            uv_head = htcenter + ratio * (uv_head - htcenter)
            uv_tail = htcenter + ratio * (uv_tail - htcenter)
        uv_head += offset
        uv_tail += offset

        # === length distribution example ===
        # uvedge idx (3)         0      1        2
        # path (1)           o-------o-----o------------o
        # uvvert idx (4)     0       1     2            3
        # distribution (4)   0       0.3   0.5          1.0  (normalized)
        uvv_count = len(self.sorted_uvverts)
        uve_count = uvv_count - 1
        distribution = [0.0] * uvv_count # init only size
        if even_point_distribution:
            for i in range(uvv_count):
                distribution[i] = i / (uvv_count - 1)
        else:
            acc = 0.0
            for i in range(uve_count):
                acc += self.sorted_uvedges[i].length
                distribution[i + 1] = acc / self.length

        for i, uvv in enumerate(self.sorted_uvverts):
            uvv.move(lerp(uv_head, uv_tail, distribution[i]))

        self.update_keys()
