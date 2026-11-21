# python
from math import sqrt, sin, cos, atan2, pi
from collections import deque

# Blender
import bmesh
from mathutils import Vector, Matrix

# Tohm UV Manip
from . import utils








#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - CLASSES
#=========#=========#=========#=========#=========#=========#=========#=========






# MARK: - UvVert

class UvVert:
    def __init__(self, uvmap):
        self.uvmap = uvmap
        self.index = None
        self.select = None
        self.depth = -1 # for bfs and paths indexing
        self.isvisited = False

        # for grid
        self.i = None
        self.j = None

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

class UvEdge:
    def __init__(self, uvv1, uvv2):
        self.index = None
        self.uvv1, self.uvv2 = order_pair(uvv1, uvv2)
        self.select = None
        self.uvedges_set = set()

    def __hash__(self):
        return hash((self.uvv1, self.uvv2))

    def __eq__(self, other):
        return (
            isinstance(other, UvEdge)
            and self.uvv1 is other.uvv1
            and self.uvv2 is other.uvv2
    )

    def get_length(self):
        du = self.uvv2.uv.x - self.uvv1.uv.x
        dv = self.uvv2.uv.y - self.uvv1.uv.y
        return sqrt(du*du + dv*dv)



# MARK: - UvQuad

class UvQuad:
    def __init__(self, uvvs):
        assert len(uvvs) == 4, "Wrong uvv count for UvQuad"
        self.uvverts_tupl = None
        self.uvedges_tupl = None
        self.i = None
        self.j = None
        # adjascent UvQuads
        self.top    = None
        self.right  = None
        self.bottom = None
        self.left   = None
        self.key = frozenset(uvvs)

        a, x, y, z = uvvs
        d_ = {x, y, z} - a.uvverts_set
        d = next(iter(d_))
        b, c = {x, y, z} - d_
        # d - c
        # |   |
        # a - b
        assert (
            quad_get_opposite_corner(a, b, c) is d
            and quad_get_opposite_corner(b, a, d) is c
            and quad_get_opposite_corner(c, a, d) is b
            and quad_get_opposite_corner(d, b, c) is a
        ), "Wrong uvvs for UvQuad"

        self.uvverts_tupl = (a, b, c, d)
        self.uvedges_tupl = (
            UvEdge(a, b),
            UvEdge(b, c),
            UvEdge(c, d),
            UvEdge(d, a)
        )

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return (isinstance(other, UvQuad)
            and other.key == self.key
        )





# MARK: - UvIsland

class UvIsland:
    def __init__(self, uvverts=None, uvedges=None):
        uvverts = uvverts if uvverts is not None else set()
        uvedges = uvedges if uvedges is not None else set()

        self.uvverts_set = None
        self.uvedges_set = None
        self.uvquads_set = set()
        self.sorted_uvverts = None
        self.sorted_uvedges = None

        self.root = None
        self.head = None
        self.tail = None

        self.is_path = None
        self.is_ring = None
        self.is_quad_grid = None
        self.is_rect_grid = None
        self.is_knot_grid = None

        self.grid_width = None
        self.grid_height = None

        self.uvedges_set = set(uvedges)
        for uve in self.uvedges_set:
            self.uvverts_set.add(uve.uvv1)
            self.uvverts_set.add(uve.uvv2)

        self.uvverts_set = set(uvverts)
        for uvv in self.uvverts_set:
            self.uvedges_set.update(uvv.uvedges_set)

        self.is_path = len(self.get_leaves()) == 2 and self.degree <= 2
        self.is_ring = len(self.get_leaves()) == 0 and self.degree == 2

        if self.is_path:
            leaves = [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 1]
            self.head, self.tail = sorted(leaves, key=lambda uvv: uvv.depth)

            self.sorted_uvverts = sorted(self.uvverts_set, key=lambda uvv: uvv.depth)

            self.sorted_uvedges = []
            for i in range(len(self.sorted_uvverts) - 1):
                uvv1, uvv2 = order_pair(self.sorted_uvverts[i], self.sorted_uvverts[i + 1])
                uve = next((uve for uve in self.uvedges_set if uve.uvv1 == uvv1 and uve.uvv2 == uvv2), None)
                assert uve is not None, "No uvedge found in island"
                self.sorted_uvedges.append(uve)

        grid_res = grid_size(self)
        if grid_res is not None:
            self.is_rect_grid = self.is_quad_grid = True
            # mesh       dA         dY         sum        x          y      
            # A . . X    0 1 2 3    2 3 4 5    2 4 6 8    0 1 2 3    0 0 0 0
            # . . . .    1 2 3 4    1 2 3 4    2 4 6 8    0 1 2 3    1 1 1 1
            # Y . . B    2 3 4 5    0 1 2 3    2 4 6 8    0 1 2 3    2 2 2 2
            self.grid_width, self.grid_height, A, X, B, Y = grid_res
            dA = rect_grid_bfs_dist(A)
            dY = rect_grid_bfs_dist(Y)
            for uvv in self.uvverts_set:
                sum = dA[uvv] + dY[uvv]
                uvv.x = (sum - (self.grid_height - 1)) // 2
                uvv.y = dA[uvv] - uvv.x
            self.sorted_uvverts = sorted(self.uvverts_set, key=lambda uvv: (uvv.x, uvv.y))

        if self.is_quad_grid is None:
            self.is_quad_grid = is_quad_grid(self)

        if self.is_quad_grid:
            self.is_knot_grid = is_knot_grid(self)

        for uvv in self.uvverts_set:
            self.uvquads_set.update(
                UvQuad((uvv, a, o, b))
                for o, (a, b) in quad_get_opposite_corners_plus(uvv).items()
            )




            

    @property
    def degree(self): return max([len(uvv.uvverts_set) for uvv in self.uvverts_set], default=0)

    def get_length(self): return sum([uve.get_length() for uve in self.uvedges_set])

    def get_leaves(self):
        return [uvv for uvv in self.uvverts_set if len(uvv.uvverts_set) == 1]





# MARK: - UvMesh

class UvMesh:
    def __init__(self, obj, mesh, bm, uvmap):
        self.obj   = obj
        self.mesh  = mesh
        self.bm    = bm
        self.uvmap = uvmap

        self.precision = 5
        self.epsilon = 10 ** -self.precision

        self.uvislands_list = []

        # SNAP LOOPS (why? why not? idk...) -> need cluterization somehow
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
                    uvvert_dict[uv] = UvVert(self.uvmap)
                uvvert_dict[uv].loops_list.append(l)
        for i, uvv in enumerate(uvvert_dict.values()):
            uvv.index = i

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
                    uvedge_dict[uvv_pair] = UvEdge(uvv1, uvv2)
        for i, uve in enumerate(uvedge_dict.values()):
            uve.index = i

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

        uvis_uvvert_lists = []

        # with leaf islands
        leaves = set([uvv for uvv in selected_uvvert_dict.values() if len(uvv.uvverts_set) == 1])
        while leaves:
            uvi = set()
            uvis_uvvert_lists.append(uvi)
            root = leaves.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                uvi.add(cur_uvv)
                for nxt in cur_uvv.uvverts_set:
                    stack.append((nxt, depth + 1))
            leaves -= uvi

        # without leaves islands
        uvverts_left = set([uvv for uvv in selected_uvvert_dict.values() if not uvv.isvisited])
        while uvverts_left:
            uvi = set()
            uvis_uvvert_lists.append(uvi)
            root = uvverts_left.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                uvi.add(cur_uvv)
                for nxt in cur_uvv.uvverts_set:
                    stack.append((nxt, depth + 1))
            uvverts_left -= uvi

        self.uvislands_list = [UvIsland(uvverts=uvvs) for uvvs in uvis_uvvert_lists]










#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - UTILITY
#=========#=========#=========#=========#=========#=========#=========#=========

def order_pair(uvva, uvvb):
    au, av = uvva.uv
    bu, bv = uvvb.uv
    assert not (au == bu and av == bv), "Identical uvvert pair coordinates"
    if au != bu:
        if   au < bu: return (uvva, uvvb)
        elif au > bu: return (uvvb, uvva)
    else:
        if   av < bv: return (uvva, uvvb)
        elif av > bv: return (uvvb, uvva)

    









def lerp(a, b, w):
    return a * (1 - w) + b * w

def bilinear(tl, tr, br, bl, wx, wy):
    t = tl * (1 - wx) + tr * wx
    b = bl * (1 - wx) + br * wx
    r = b  * (1 - wy) + t  * wy
    return r

def angle(uv1, uv2):
    du, dv = Vector(uv2) - Vector(uv1)
    return atan2(dv, du)

def uvvs_angle(uvv1, uvv2):
    return angle(uvv1.uv, uvv2.uv)

def get_bounding_box(uvvs):
    us = [uvv.u for uvv in uvvs]
    vs = [uvv.v for uvv in uvvs]
    return [[min(us), min(vs)], [max(us), max(vs)]]

def get_center(uvi, mode):
    uvvs = list(uvi.uvverts_set)
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
        if not uvi.is_path:
            print("Can't get head-tail midpoint: UvConnectedGraph is not a path.")
            return None
        uv1 = Vector(uvi.head.uv)
        uv2 = Vector(uvi.tail.uv)
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














def has_triangle(uvi):
    for uvv1 in uvi.uvverts_set:
        for uvv2 in uvv1.uvverts_set:
            if uvv1 is uvv2: # useless I think...
                continue
            if len(uvv1.uvverts_set & uvv2.uvverts_set) != 0:
                return True
    return False





def quad_get_opposite_corner(o, a, b):
    try:
        ab = a.uvverts_set & b.uvverts_set
        opp = ab - set([o])
        assert len(opp) == 1
        return next(iter(opp))
    except:
        return None


# can recieve non quad uvv
# must return [] to signify fail
def quad_get_opposite_corners(uvv):
    n = len(uvv.uvverts_set)
    if n <= 1 or n >= 5:
        return []
    if n == 2:
        a, b = uvv.uvverts_set
        c = quad_get_opposite_corner(uvv, a, b)
        return [c] if c is not None else []
    if n == 3:
        a, b, c = uvv.uvverts_set
        ab = quad_get_opposite_corner(uvv, a, b)
        bc = quad_get_opposite_corner(uvv, b, c)
        ac = quad_get_opposite_corner(uvv, a, c)
        cand = [uvv for uvv in [ab, bc, ac] if uvv is not None]
        if len(cand) != len({x for x in cand}):
            return []
        if len(cand) != 2:
            return []
        return cand
    if n == 4:
        a, b, c, d = uvv.uvverts_set
        ab = quad_get_opposite_corner(uvv, a, b)
        bc = quad_get_opposite_corner(uvv, b, c)
        cd = quad_get_opposite_corner(uvv, c, d)
        da = quad_get_opposite_corner(uvv, d, a)
        ac = quad_get_opposite_corner(uvv, a, c)
        bd = quad_get_opposite_corner(uvv, b, d)
        cand = [uvv for uvv in [ab, bc, cd, da, ac, bd] if uvv is not None]
        if len(cand) != len({x for x in cand}):
            return []
        if len(cand) not in (2, 3, 4):
            return []
        return cand


# can recieve non quad uvv
# must return {} to signify fail
def quad_get_opposite_corners_plus(uvv):
    n = len(uvv.uvverts_set)
    if n <= 1 or n >= 5:
        return {}
    neigh2 = set().union(*(n.uvverts_set for n in uvv.uvverts_set))
    if len(uvv.uvverts_set & neigh2) != 0:
        return {}
    if n == 2:
        a, b = uvv.uvverts_set
        c = quad_get_opposite_corner(uvv, a, b)
        if not c:
            return {}
        return {c: {a, b}}
    if n == 3:
        a, b, c = uvv.uvverts_set
        ab = quad_get_opposite_corner(uvv, a, b)
        bc = quad_get_opposite_corner(uvv, b, c)
        ac = quad_get_opposite_corner(uvv, a, c)
        cand = {
            ab: {a, b},
            bc: {b, c},
            ac: {a, c}
        }
        cand = {k: v for k, v in cand.items() if k is not None}
        if len(cand) != 2:
            return {}
        return cand
    if n == 4:
        a, b, c, d = uvv.uvverts_set
        ab = quad_get_opposite_corner(uvv, a, b)
        bc = quad_get_opposite_corner(uvv, b, c)
        cd = quad_get_opposite_corner(uvv, c, d)
        da = quad_get_opposite_corner(uvv, d, a)
        ac = quad_get_opposite_corner(uvv, a, c)
        bd = quad_get_opposite_corner(uvv, b, d)
        cand = {
            ab: {a, b},
            bc: {b, c},
            cd: {c, d},
            da: {d, a},
            ac: {a, c},
            bd: {b, d}
        }
        cand = {k: v for k, v in cand.items() if k is not None}
        if len(cand) not in (2, 3, 4):
            return {}
        return cand








def rect_grid_bfs_dist(start):
    distances = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nxt in cur.uvverts_set:
            if nxt not in distances:
                distances[nxt] = distances[cur] + 1
                q.append(nxt)
    return distances





def rearrange_quad_verts(uvi):
    visited_uvqs = set()
    first_uvq = next(iter(uvi.uvquads_set))
    stack = [first_uvq]
    tl, tr, br, bl = first_uvq.uvverts
    while stack:

























def is_quad_grid(uvi):
    if has_triangle(uvi):
        return False
    if uvi.degree not in (2, 3, 4):
        return False
    for uvv in uvi.uvverts_set:
        l = len(uvv.uvverts_set)
        c = len(quad_get_opposite_corners(uvv))
        if l <= 1 or l >= 5:
            return False
        elif not c:
            return False
        elif l == 2:
            if c != 1:
                return False
        elif l == 3:
            if c != 2:
                return False
        elif l == 4:
            if c not in (2, 3, 4):
                return False
    return True


def is_knot_grid(uvi):
    assert uvi.is_quad_grid, "Must first evaluate if is quad grid"
    star4 = [uvv for uvv in uvi.uvverts_set if len(uvv.uvverts_set) == 4]
    for uvv in star4:
        if len(quad_get_opposite_corners(uvv)) == 2:
            return True
    return False



def grid_size(uvi):
    uvvs = uvi.uvverts_set
    V, E = len(uvvs), len(uvi.uvedges_set)

    border = {v for v in uvvs if len(v.uvverts_set) in (2, 3)}
    corners = [v for v in border if len(v.uvverts_set) == 2]
    interns = [v for v in uvvs if len(v.uvverts_set) == 4]
    if len(corners) != 4 or len(border) + len(interns) != V:
        return None

    v1, v2, v3, v4 = [Vector(uvv.uv) for uvv in corners]
    center = (v1 + v2 + v3 + v4) / 4
    visually_sorted_corners = sorted(corners, key=lambda uvv: -angle(center, uvv.uv))

    A = visually_sorted_corners[0]
    walk = [A]
    cur = A
    while True:
        nexts = [uvv for uvv in cur.uvverts_set if uvv in border and uvv not in walk]
        if not nexts:
            break
        if len(nexts) > 1 and cur is not A:
            return None
        cur = nexts[0]
        walk.append(cur)

    if len(walk) != len(border) or A not in cur.uvverts_set:
        return None

    ordered_corners = [(uvv, idx) for idx, uvv in enumerate(walk) if len(uvv.uvverts_set) == 2]
    (A, a), (X, x), (B, b), (Y, y) = ordered_corners
    m = x - a + 1
    n = b - x + 1
    m_ = y - b + 1
    n_ = len(walk) - y + 1
    if m != m_ or n != n_:
        return None
    if m * n != V or E != m * (n - 1) + n * (m - 1):
        return None
    if len(interns) != (m - 2) * (n - 2):
        return None
    flip = ordered_corners[1] == visually_sorted_corners[1]
    if flip:
        return m, n, A, X, B, Y
    else:
        return n, m, A, Y, B, X


def is_rect_grid(uvi):
    return grid_size(uvi) is not None


















#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========

def reverse_path(uvi):
    if uvi.is_path:
        n = len(uvi.sorted_uvverts)
        for i, uvv in enumerate(uvi.sorted_uvverts):
            uvv.depth = n - 1 - i
        uvi.head, uvi.tail = (uvi.tail, uvi.head)

def reverse_paths(uvmesh):
    for uvi in uvmesh.uvislands_list:
        reverse_path(uvi)










def straighten_path(uvi, keep_paths_length, even_point_distribution, center_mode):
    if uvi.is_path:
        uv_head = Vector(uvi.head.uv)
        uv_tail = Vector(uvi.tail.uv)
        htcenter = (uv_head + uv_tail) / 2
        target_center = get_center(uvi, center_mode)
        offset = target_center - htcenter
        htdist = (uv_head - uv_tail).length
        if keep_paths_length:
            ratio = uvi.get_length() / htdist
            uv_head = htcenter + ratio * (uv_head - htcenter)
            uv_tail = htcenter + ratio * (uv_tail - htcenter)
        uv_head += offset
        uv_tail += offset

        # === length distribution example ===
        # uvedge idx (3)         0      1        2
        # path (1)           o-------o-----o------------o
        # uvvert idx (4)     0       1     2            3
        # distribution (4)   0       0.3   0.5          1.0  (normalized)
        uvv_count = len(uvi.uvverts_set)
        uve_count = uvv_count - 1
        distribution = [0.0] * uvv_count # init only size
        if even_point_distribution:
            for i in range(uvv_count):
                distribution[i] = i / (uvv_count - 1)
        else:
            acc = 0.0
            for i in range(uve_count):
                acc += uvi.sorted_uvedges[i].get_length()
                distribution[i + 1] = acc / uvi.get_length()

        for i, uvv in enumerate(uvi.sorted_uvverts):
            uv = lerp(uv_head, uv_tail, distribution[i])
            uvv.move(uv)

def straighten_paths(uvmesh, keep_paths_length, even_point_distribution, center_mode):
    for uvi in uvmesh.uvislands_list:
        straighten_path(uvi, keep_paths_length, even_point_distribution, center_mode)










def align_paths(uvmesh):
    # Assert paths are straight
    paths = [uvi for uvi in uvmesh.uvislands_list if uvi.is_path]
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
    paths = [uvi for uvi in uvmesh.uvislands_list if uvi.is_path]
    if len(paths) <= 1:
        utils.alert(f"Need at least 2 paths, found {len(paths)}")
        return

    uvvs = []
    for p in paths:
        uvvs.extend(p.uvverts_set)

    [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
    width = Mu - mu
    height = Mv - mv
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









def align_grid(uvi):
    grid_res = grid_size(uvi)
    if grid_res:
        m, n, A, X, B, Y = grid_res
        tl, tr, br, bl = A.uv.copy(), X.uv.copy(), B.uv.copy(), Y.uv.copy()
        for uvv in uvi.uvverts_set:
            wx = uvv.x / (m - 1)
            wy = 1 - uvv.y / (n - 1)
            uv = bilinear(tl, tr, br, bl, wx, wy)
            tmp = Vector((uvv.x, uvv.y)) / 10
            uvv.move(uv)

def align_grids(uvmesh):
    for uvi in uvmesh.uvislands_list:
        align_grid(uvi)










#=========#=========#=========#=========#=========#=========#=========#=========
# PRINT
#=========#=========#=========#=========#=========#=========#=========#=========

def print_uvmesh(uvmesh):
    lines = []
    from datetime import datetime

    for uvi in uvmesh.uvislands_list:
        line = ""
        if uvi.is_path: line += "path, "
        if uvi.is_ring: line += "ring, "
        if uvi.is_quad_grid: line += "quad "
        if uvi.is_knot_grid: line += "knot "
        if uvi.is_rect_grid: line += "rectangle "
        if any([uvi.is_quad_grid, uvi.is_knot_grid,uvi.is_rect_grid]): line += "grid, "
        if line == "": line += "other, "
        line += "|"
        line += f"{len(uvi.uvverts_set)} uvvs, "
        line += f"{len(uvi.uvedges_set)} uves, "
        line += f"{len(uvi.uvquads_set)} uvqs, "
        line += f"{uvi.get_length():.3f} length"
        lines.append("• " + line)


    print("\n".join(lines))
    return lines

# · • – — ← → ↑ ↓ ○ ● □ ■ △ ◇ ± × ÷ ≠ ≤ ≥ ≈ ° Ø × ✓
