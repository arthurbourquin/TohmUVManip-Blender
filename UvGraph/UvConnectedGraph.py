from mathutils import Vector, Matrix
from .UvEdge import UvEdge

from .utils import lerp, dist, get_angle, get_bounding_box, get_center


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
        self.uvedges = set()

        self.root = None
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

    def update(self):
        uvv_count = len(self.uvverts)

        if uvv_count == 1:
            self.set_singleton()
            return

        # uv edges
        self.degree = 1
        from collections import deque
        for uvv in self.uvverts.values():
            uvv.isvisited = False
        if uvv_count >= 2:
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
            uvv.set_uv(new_pos)


    def straighten_path(self, keep_paths_length, even_point_distribution, center_mode):
        htcenter = (self.head.uv + self.tail.uv) / 2
        target_center = get_center(self, center_mode)
        offset = target_center - htcenter
        htdist = dist(self.head, self.tail)
        start = Vector(self.head.uv)
        end = Vector(self.tail.uv)
        if keep_paths_length:
            ratio = self.length / htdist
            start = htcenter + ratio * (start - htcenter)
            end = htcenter + ratio * (end - htcenter)
        start += offset
        end += offset

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
            uvv.set_uv(lerp(start, end, distribution[i]))
