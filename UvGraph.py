# python
from math import sqrt, sin, cos, atan2, pi

# Blender
import bmesh
from mathutils import Vector, Matrix

# Tohm UV Manip
from . import utils








#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - CLASSES
#=========#=========#=========#=========#=========#=========#=========#=========






# MARK: - UvVert

class UVVert:
    def __init__(self, uvmap):
        self.uvmap = uvmap
        self.select = None
        self.depth = -1
        self.isvisited = False

        self.loops_list = []
        self.uvverts_set = set()
        self.uvedges_set = set()

    @property
    def uv(self): return self.loops_list[0][self.uvmap].uv if self.loops_list else (None, None)
    @property
    def u(self): return self.uv.x
    @property
    def v(self): return self.uv.y

    def move(self, uv): # need bmesh.update_edit_mesh(mesh) after
        for l in self.loops_list:
            l[self.uvmap].uv = uv
        



# MARK: - UvEdge

class UVEdge:
    def __init__(self, uvv1, uvv2):
        self.uvv1 = uvv1
        self.uvv2 = uvv2
        self.select = None
        self.uvedges_set = set()

    @property
    def length(self):
        du = self.uvv2.uv.x - self.uvv1.uv.x
        dv = self.uvv2.uv.y - self.uvv1.uv.y
        return sqrt(du*du + dv*dv)



# MARK: - UvIsland

class UVIsland:
    def __init__(self, uvverts=None, uvedges=None):
        uvverts = uvverts if uvverts is not None else set()
        uvedges = uvedges if uvedges is not None else set()

        self.uvverts_set = set(uvverts)
        self.uvedges_set = set(uvedges)
        self.root = None

        # for paths
        self.sorted_uvverts = None
        self.sorted_uvedges = None
        self.head = None
        self.tail = None

        for uve in self.uvedges_set:
            self.uvverts_set.add(uve.uvv1)
            self.uvverts_set.add(uve.uvv2)

        for uvv in self.uvverts_set:
            self.uvedges_set.update(uvv.uvedges_set)

        if self.istree:
            self.root = [uvv for uvv in self.uvverts_set if uvv.depth == 0][0]

        if self.ispath:
            leaves = [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 1]
            self.head, self.tail = sorted(leaves, key=lambda uvv: uvv.depth)

            self.sorted_uvverts = sorted(self.uvverts_set, key=lambda uvv: uvv.depth)

            self.sorted_uvedges = []
            for i in range(len(self.sorted_uvverts) - 1):
                uvv1, uvv2 = order_pair(self.sorted_uvverts[i], self.sorted_uvverts[i + 1])
                uve = next((uve for uve in self.uvedges_set if uve.uvv1 == uvv1 and uve.uvv2 == uvv2), None)
                assert uve is not None, "No uvedge found in island"
                self.sorted_uvedges.append(uve)

        if self.isgrid:
            # mesh       dA         dB         s          i          j
            # A . . N    0 1 2 3    2 3 4 5    0 2 4 6    0 1 2 3    0 0 0 0
            # . . . .    1 2 3 4    1 2 3 4    0 2 4 6    0 1 2 3    1 1 1 1
            # M . . O    2 3 4 5    0 1 2 3    0 2 4 6    0 1 2 3    2 2 2 2
            # m=3, n=4
            a = 1

    @property
    def degree(self): return max([len(uvv.uvverts_set) for uvv in self.uvverts_set], default=0)
    @property
    def length(self): return sum([uve.length for uve in self.uvedges_set])

    def get_leaves(self):
        return [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 1]

    @property
    def ispath(self):
        has_two_leaves = len(self.get_leaves()) == 2
        return has_two_leaves and self.degree <= 2
    @property
    def isring(self):
        has_no_leaves = len(self.get_leaves()) == 0
        return has_no_leaves and self.degree == 2
    @property
    def istree(self): # but not path!
        is_tree = len(self.uvverts_set) == len(self.uvedges_set) + 1
        is_not_path = self.degree > 2
        return is_tree and is_not_path

    @property
    def isgrid(self):
        corners = [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 2]
        if len(corners) != 4:
            return False
        borders = [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 3]
        interns = [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 4]
        if len(corners) + len(borders) + len(interns) != len(self.uvverts_set):
            return False
        if len(borders) % 4 != 0:
            return False
        
        

    def who_am_i(self):
        str = ""
        if self.ispath:
            str += "Path, "
        elif self.isring:
            str += "Ring, "
        elif self.istree:
            str += "Tree, "
        else:
            str += f"Cyclic island, "
        str += f"{len(self.uvverts_set)} uvverts, "
        str += f"{len(self.uvedges_set)} uvedges, "
        str += f"length {self.length:.2f}, "
        str += f"degree {self.degree}"
        return str



# MARK: - UvMesh

class UvMesh:
    def __init__(self, obj, mesh, bm, uvmap):
        self.obj   = obj
        self.mesh  = mesh
        self.bm    = bm
        self.uvmap = uvmap

        self.precision = 5
        self.epsilon = 10 ** -self.precision

        self.islands = []

        # SNAP LOOPS (why? why not? idk...)
        for f in bm.faces:
            for l in f.loops:
                u, v = l[self.uvmap].uv
                u = round(u, self.precision)
                v = round(v, self.precision)
                l[self.uvmap].uv = Vector((u, v))
        bmesh.update_edit_mesh(mesh)

        # GET UVVERTS AND UVEDGES
        uvvert_dict = {}
        for f in bm.faces:
            for l in f.loops:
                uv = tuple(l[self.uvmap].uv)
                if uv not in uvvert_dict:
                    uvvert_dict[uv] = UVVert(self.uvmap)
                uvvert_dict[uv].loops_list.append(l)

        uvedge_dict = {}
        for f in bm.faces:
            for l in f.loops:
                uva = tuple(l[self.uvmap].uv)
                uvb = tuple(l.link_loop_next[self.uvmap].uv)
                uvva = uvvert_dict[uva]
                uvvb = uvvert_dict[uvb]
                uvv_pair = order_pair(uvva, uvvb)
                if not uvv_pair in uvedge_dict:
                    uvv1, uvv2 = uvv_pair
                    uvedge_dict[uvv_pair] = UVEdge(uvv1, uvv2)

        # SET SELECTED
        # set selection based on loops uv_select_edge
        for uve in uvedge_dict.values():
            for l in uve.uvv1.loops_list:
                if l.uv_select_edge:
                    if l.link_loop_next[self.uvmap].uv == uve.uvv2.uv:
                        uve.select = True
                        break
            if uve.select:
                continue
            for l in uve.uvv2.loops_list:
                if l.uv_select_edge:
                    if l.link_loop_next[self.uvmap].uv == uve.uvv1.uv:
                        uve.select = True
                        break

        selected_uvedge_dict = {k: uve for k, uve in uvedge_dict.items() if uve.select}

        for uve in selected_uvedge_dict.values():
            uve.uvv1.select = True
            uve.uvv2.select = True

        selected_uvvert_dict = {k: uvv for k, uvv in uvvert_dict.items() if uvv.select}

        # LINK
        for uve in selected_uvedge_dict.values():
            uve.uvv1.uvverts_set.add(uve.uvv2)
            uve.uvv2.uvverts_set.add(uve.uvv1)
            uve.uvv1.uvedges_set.add(uve)
            uve.uvv2.uvedges_set.add(uve)
        for uvv in selected_uvvert_dict.values():
            for uvea in uvv.uvedges_set:
                for uveb in uvv.uvedges_set:
                    if uvea is not uveb:
                        uvea.uvedges_set.add(uveb)


        # CREATE ISLANDS

        islands_uvvert_lists = []

        # with leaf islands
        leaves = set([uvv for uvv in selected_uvvert_dict.values() if len(uvv.uvverts_set) == 1])
        while leaves:
            island = set()
            islands_uvvert_lists.append(island)
            root = leaves.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                island.add(cur_uvv)
                for nxt in cur_uvv.uvverts_set:
                    stack.append((nxt, depth + 1))
            leaves -= island

        # without leaves islands
        uvverts_left = set([uvv for uvv in selected_uvvert_dict.values() if not uvv.isvisited])
        while uvverts_left:
            island = set()
            islands_uvvert_lists.append(island)
            root = uvverts_left.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                island.add(cur_uvv)
                for nxt in cur_uvv.uvverts_set:
                    stack.append((nxt, depth + 1))
            uvverts_left -= island

        self.islands = [UVIsland(uvverts=uvvs) for uvvs in islands_uvvert_lists]










#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - UTILITY
#=========#=========#=========#=========#=========#=========#=========#=========

def order_pair(uvva, uvvb):
    au, av = uvva.uv
    bu, bv = uvvb.uv
    if au == bu and av == bv:
        raise AssertionError("Identical uvvert pair coordinates")
        return
    if au != bu:
        if   au < bu: return (uvva, uvvb)
        elif au > bu: return (uvvb, uvva)
    else:
        if   av < bv: return (uvva, uvvb)
        elif av > bv: return (uvvb, uvva)










def lerp(a, b, w):
    return a * (1 - w) + b * w

def uvvs_angle(uvv1, uvv2): # [-pi,pi]
    du, dv = Vector(uvv2.uv) - Vector(uvv1.uv)
    return atan2(dv, du)

def get_bounding_box(uvvs):
    us = [uvv.u for uvv in uvvs]
    vs = [uvv.v for uvv in uvvs]
    return [[min(us), min(vs)], [max(us), max(vs)]]

def get_center(island, mode):
    uvvs = list(island.uvverts_set)
    if mode == "BBOX":
        [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
        uv = ((mu + Mu) / 2, (mv + Mv) / 2)
        return Vector(uv)
    elif mode == "MEDIAN":
        mid = len(uvvs) // 2
        u = sorted([uvv.u for uvv in uvvs])[mid]
        v = sorted([uvv.v for uvv in uvvs])[mid]
        return Vector((u, v))
    elif mode == "AVERAGE":
        sum_u = sum([uvv.u for uvv in uvvs])
        sum_v = sum([uvv.v for uvv in uvvs])
        count = len(uvvs)
        return Vector((sum_u, sum_v)) / count
    elif mode == "HEADTAIL":
        if not island.ispath:
            print("Can't get head-tail midpoint: UvConnectedGraph is not a path.")
            return None
        uv1 = Vector(island.head.uv)
        uv2 = Vector(island.tail.uv)
        return (uv1 + uv2) / 2
    else:
        print(f"Unknown center mode: {mode}")
        return None










def rotate(uvvs, angle, center):
    M = Matrix.Rotation(angle, 2)
    center = Vector(center)
    for uvv in uvvs:
        uv = M @ (uvv.uv - center) + center
        for l in uvv.loops_list:
            l[uvv.uvmap].uv = uv








#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

def reverse_path(island):
    if island.ispath:
        n = len(island.sorted_uvverts)
        for i, uvv in enumerate(island.sorted_uvverts):
            uvv.depth = n - 1 - i
        island.head, island.tail = (island.tail, island.head)

def reverse_paths(uvmesh):
    for island in uvmesh.islands:
        reverse_path(island)










def straighten_path(island, keep_paths_length, even_point_distribution, center_mode):
    if island.ispath:
        uv_head = Vector(island.head.uv)
        uv_tail = Vector(island.tail.uv)
        htcenter = (uv_head + uv_tail) / 2
        target_center = get_center(island, center_mode)
        offset = target_center - htcenter
        htdist = (uv_head - uv_tail).length
        if keep_paths_length:
            ratio = island.length / htdist
            uv_head = htcenter + ratio * (uv_head - htcenter)
            uv_tail = htcenter + ratio * (uv_tail - htcenter)
        uv_head += offset
        uv_tail += offset

        # === length distribution example ===
        # uvedge idx (3)         0      1        2
        # path (1)           o-------o-----o------------o
        # uvvert idx (4)     0       1     2            3
        # distribution (4)   0       0.3   0.5          1.0  (normalized)
        uvv_count = len(island.uvverts_set)
        uve_count = uvv_count - 1
        distribution = [0.0] * uvv_count # init only size
        if even_point_distribution:
            for i in range(uvv_count):
                distribution[i] = i / (uvv_count - 1)
        else:
            acc = 0.0
            for i in range(uve_count):
                acc += island.sorted_uvedges[i].length
                distribution[i + 1] = acc / island.length

        for i, uvv in enumerate(island.sorted_uvverts):
            uv = lerp(uv_head, uv_tail, distribution[i])
            uvv.move(uv)

def straighten_paths(uvmesh, keep_paths_length, even_point_distribution, center_mode):
    for island in uvmesh.islands:
        straighten_path(island, keep_paths_length, even_point_distribution, center_mode)










def align_paths(uvmesh):
    # Assert paths are straight
    paths = [isl for isl in uvmesh.islands if isl.ispath]
    angles = [uvvs_angle(p.head, p.tail) for p in paths]
    # Mean undirected angle
    c = sum(cos(2 * a) for a in angles)
    s = sum(sin(2 * a) for a in angles)
    mean = (0.5 * atan2(s, c)) % pi
    # Minimal rotation to mean
    for p, a in zip(paths, angles):
        delta = (mean - a + pi / 2) % pi - pi / 2
        center = get_center(p, "HEADTAIL")
        rotate(p.uvverts_set, delta, center)










def align_paths_on_grid(uvmesh):
    paths = [isl for isl in uvmesh.islands if isl.ispath]
    if len(paths) <= 1:
        utils.alert(f"Need at least 2 paths, found {len(paths)}")
        return

    uvvs = []
    for p in paths:
        uvvs.extend(p.uvverts_set)

    [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
    width = Mu - mu
    height = Mv - mv
    print(Mv, mv, height)
    if width <= uvmesh.epsilon or height <= uvmesh.epsilon:
        lines = ["Unable to guess grid layout, bbox is flat."]
        if width <= uvmesh.epsilon:
            lines.append(f"width: {width}")
        elif height <= uvmesh.epsilon:
            lines.append(f"height: {height}")
        else:
            lines.append(f"width: {width}, height: {height}")
        utils.alert(lines)
        return

    straighten_paths(uvmesh, False, True, "HEADTAIL")

    vertical_count = 0
    horizontal_count = 0
    for p in paths:
        u1, v1 = p.head.uv
        u2, v2 = p.tail.uv
        if abs(u1 - u2) > abs(v1 - v2):
            horizontal_count += 1
        else:
            vertical_count += 1
    horizontal_paths_piled_vertically = horizontal_count > vertical_count

    if horizontal_paths_piled_vertically:
        spaths = sorted(paths, key=lambda path: get_center(path, "HEADTAIL").y)
    else:
        spaths = sorted(paths, key=lambda path: get_center(path, "HEADTAIL").x)

    if horizontal_paths_piled_vertically:
        countY = len(spaths)
        for y, p in enumerate(spaths):
            countX = len(p.uvverts_set)
            reverse = p.head.uv[0] > p.tail.uv[0]
            for x, uvv in enumerate(p.sorted_uvverts):
                wx = (x / (countX - 1)) # (no div 0: path has min 2 uvv)
                wy = 1 if countY == 1 else y / (countY - 1) # (no div 0: paths has min 2 path)
                if reverse:
                    wx = 1 - wx
                u = lerp(mu, Mu, wx)
                v = lerp(mv, Mv, wy)
                uvv.move((u, v))
    else:
        countX = len(spaths)
        for x, p in enumerate(spaths):
            countY = len(p.uvverts_set)
            reverse = p.head.uv[1] > p.tail.uv[1]
            for y, uvv in enumerate(p.sorted_uvverts):
                wx = x / (countX - 1)
                wy = (y / (countY - 1)) if not reverse else (1 - y / (countY - 1))
                u = lerp(mu, Mu, wx)
                v = lerp(mv, Mv, wy)
                uvv.move((u, v))










#=========#=========#=========#=========#=========#=========#=========#=========
# PRINT
#=========#=========#=========#=========#=========#=========#=========#=========

def print_uvmesh(uvmesh):
    lines = []
    from datetime import datetime

    lines.append("")
    lines.append(f"=== UvMesh Diagnostic === {datetime.now().strftime("%H:%M:%S")}")

    lines.append(f"{len(uvmesh.islands)} islands")
    lines.append(f"- {len([isl for isl in uvmesh.islands if isl.ispath])} path(s)")
    lines.append(f"- {len([isl for isl in uvmesh.islands if isl.isring])} ring(s)")
    lines.append(f"- {len([isl for isl in uvmesh.islands if isl.istree])} tree(s)")

    lines.append("==========================")
    print("\n".join(lines))
    return lines
