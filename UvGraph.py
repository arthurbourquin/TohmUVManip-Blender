# python
from __future__ import annotations
from math import sqrt, sin, cos, atan2, pi
from collections import deque

# Blender
import bmesh
from mathutils import Vector, Matrix
from mathutils.kdtree import KDTree

# Tohm UV Manip
from . import utils








#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - CLASSES
#=========#=========#=========#=========#=========#=========#=========#=========






# MARK: - UvVert

class UvVert:
    def __init__(self, uvmap):
        self.uvmap = uvmap
        self.uv: tuple[float, float]
        self.index: int
        self.select = None
        self.depth = -1 # for bfs and paths indexing
        self.isvisited = False

        # for grid
        self.i = None
        self.j = None

        self.loops = []
        self.uvverts: set["UvVert"] = set()
        self.uvedges: set["UvEdge"] = set()

    @property
    def u(self): return self.uv[0]
    @property
    def v(self): return self.uv[1]




# MARK: - UvEdge

class UvEdge:
    def __init__(self, uvv1, uvv2):
        self.index = None
        self.uvv1: UvVert
        self.uvv2: UvVert
        self.select = None
        self.uvedges: set["UvEdge"] = set()

        self.uvv1, self.uvv2 = order_pair(uvv1, uvv2)

    def __hash__(self):
        return hash((self.uvv1, self.uvv2))

    def __eq__(self, other):
        return (
            isinstance(other, UvEdge)
            and self.uvv1 is other.uvv1
            and self.uvv2 is other.uvv2
    )




# MARK: - UvQuad

class UvQuad:
    def __init__(self, uvvs):
        self.uvverts: list["UvVert"]
        self.uvedges: list["UvEdge"]
        self.i = None
        self.j = None
        self.key = frozenset(uvvs)

        assert len(uvvs) == 4
        a = next(iter(uvvs))
        d = [uvv for uvv in uvvs if uvv is not a and uvv not in a.uvverts][0]
        b, c = [uvv for uvv in uvvs if uvv is not a and uvv is not d]
        assert b in a.uvverts
        assert d in b.uvverts
        assert c in d.uvverts
        assert a in c.uvverts

        # a - b    we only ensure opposites
        # |   |    a opposite of d
        # c - d    d opposite if c
        self.uvverts = [a, b, d, c]
        self.uvedges = [
            UvEdge(a, b),
            UvEdge(b, d),
            UvEdge(d, c),
            UvEdge(c, a)
        ]

    def __hash__(self):
        return hash(self.key)

    def __eq__(self, other):
        return isinstance(other, UvQuad) and other.key == self.key





# MARK: - UvIsland

class UvIsland:
    def __init__(self, uvverts=None, uvedges=None):
        uvverts = uvverts if uvverts is not None else set()
        uvedges = uvedges if uvedges is not None else set()

        self.uvverts: set["UvVert"]
        self.uvedges: set["UvEdge"]
        self.uvquads: set["UvQuad"] = set()
        self.sorted_uvverts: list["UvVert"]
        self.sorted_uvedges: list["UvEdge"]

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

        self.uvedges = set(uvedges)
        for uve in self.uvedges:
            self.uvverts.add(uve.uvv1)
            self.uvverts.add(uve.uvv2)

        self.uvverts = set(uvverts)
        for uvv in self.uvverts:
            self.uvedges.update(uvv.uvedges)

        leaves_len = len([uvv for uvv in self.uvverts if len(uvv.uvverts) == 1])
        degree = self.degree
        self.is_path = leaves_len == 2 and degree <= 2
        self.is_ring = leaves_len == 0 and degree == 2

        if self.is_path:
            leaves = [uvv for uvv in self.uvverts if len(uvv.uvverts) == 1]
            self.head, self.tail = sorted(leaves, key=lambda uvv: uvv.depth)

            self.sorted_uvverts = sorted(self.uvverts, key=lambda uvv: uvv.depth)

            self.sorted_uvedges = []
            for i in range(len(self.sorted_uvverts) - 1):
                uvv1, uvv2 = order_pair(self.sorted_uvverts[i], self.sorted_uvverts[i + 1])
                uve = next((uve for uve in self.uvedges if uve.uvv1 == uvv1 and uve.uvv2 == uvv2), None)
                assert uve is not None, "No uvedge found in island"
                self.sorted_uvedges.append(uve)

        grid_res = grid_size(self)
        if grid_res is not None:
            self.is_rect_grid = self.is_quad_grid = True
            # mesh       A-dist     Y-dist     sum        x          y      
            # Y . . B    2 3 4 5    0 1 2 3    2 4 6 8    0 1 2 3    2 2 2 2
            # . . . .    1 2 3 4    1 2 3 4    2 4 6 8    0 1 2 3    1 1 1 1
            # A . . X    0 1 2 3    2 3 4 5    2 4 6 8    0 1 2 3    0 0 0 0
            self.grid_width, self.grid_height, A, X, B, Y = grid_res
            dA = rect_grid_bfs_dist(A)
            dY = rect_grid_bfs_dist(Y)
            for uvv in self.uvverts:
                sum = dA[uvv] + dY[uvv]
                uvv.x = (sum - (self.grid_height - 1)) // 2
                uvv.y = dA[uvv] - uvv.x
            self.sorted_uvverts = sorted(self.uvverts, key=lambda uvv: (uvv.x, uvv.y))

        if self.is_quad_grid is None:
            self.is_quad_grid = is_quad_grid(self)

        if self.is_quad_grid:
            self.is_knot_grid = is_knot_grid(self)

        for uvv in self.uvverts:
            self.uvquads.update(
                UvQuad((uvv, a, o, b))
                for o, (a, b) in quad_get_opposite_corners_plus(uvv).items()
            )

    @property
    def degree(self): return max([len(uvv.uvverts) for uvv in self.uvverts], default=0)






# MARK: - UvMesh

class UvMesh:
    def __init__(self, obj, mesh, bm, uvmap):
        self.obj   = obj
        self.mesh  = mesh
        self.bm    = bm
        self.uvmap = uvmap

        self.precision = 4
        self.epsilon = 10 ** -self.precision

        self.uvislands: list[UvIsland] = []
        self.loops:     list[BMLoop]   = []

        # GET UVVERTS AND UVEDGES

        clusterization = loop_clustersization(bm, uvmap, self.epsilon)
        if clusterization is None:
            raise RuntimeError("Ambigous UV clusters, clean UVs of shrink threshold")
        assert sorted([l.index for l in clusterization.keys()]) == list(range(len(clusterization)))
        self.loops = clusterization

        uvverts: dict[tuple[float, float], UvVert] = {}
        i = 0
        for l, uvkey in self.loops.items():
            if uvkey not in uvverts:
                uvv = UvVert(uvmap)
                uvv.uv = uvkey
                uvv.index = i; i += 1
                uvv.select = False
                uvverts[uvkey] = uvv
            uvverts[uvkey].loops.append(l)

        uvedges: dict[tuple[UvVert, UvVert], UvEdge] = {}
        i = 0
        for f in bm.faces:
            for l in f.loops:
                uvkeya = self.loops[l]
                uvkeyb = self.loops[l.link_loop_next]
                if uvkeya == uvkeyb:
                    continue
                uvva = uvverts[uvkeya]
                uvvb = uvverts[uvkeyb]
                uvv_pair = order_pair(uvva, uvvb)
                if not uvv_pair in uvedges:
                    uvv1, uvv2 = uvv_pair
                    uve = UvEdge(uvv1, uvv2)
                    uve.index = i; i += 1
                    uve.select = False
                    uvedges[uvv_pair] = uve

        # SET SELECTED
        # set selection based on loops uv_select_edge
        for f in bm.faces:
            for l in f.loops:
                if l.uv_select_edge:
                    uvvkey1 = self.loops[l]
                    uvvkey2 = self.loops[l.link_loop_next]
                    uvv1 = uvverts[uvvkey1]
                    uvv2 = uvverts[uvvkey2]
                    uvekey = order_pair(uvv1, uvv2)
                    uve = uvedges[uvekey]
                    uvv1.select = True
                    uvv2.select = True
                    uve.select = True
        selected_uvedges = {k: uve for k, uve in uvedges.items() if uve.select == True}
        selected_uvverts = {k: uvv for k, uvv in uvverts.items() if uvv.select == True}

        # LINK
        for uve in selected_uvedges.values():
            uve.uvv1.uvverts.add(uve.uvv2)
            uve.uvv2.uvverts.add(uve.uvv1)
            uve.uvv1.uvedges.add(uve)
            uve.uvv2.uvedges.add(uve)
        for uvv in selected_uvverts.values():
            for uvea in uvv.uvedges:
                for uveb in uvv.uvedges:
                    if uvea is not uveb:
                        uvea.uvedges.add(uveb)

        # CREATE ISLANDS

        uvvert_lists = []

        # with leaf islands
        leaves = set([uvv for uvv in selected_uvverts.values() if len(uvv.uvverts) == 1])
        while leaves:
            uvi = set()
            uvvert_lists.append(uvi)
            root = leaves.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                uvi.add(cur_uvv)
                for nxt in cur_uvv.uvverts:
                    stack.append((nxt, depth + 1))
            leaves -= uvi

        # without leaves islands
        uvverts_left = set([uvv for uvv in selected_uvverts.values() if not uvv.isvisited])
        while uvverts_left:
            uvi = set()
            uvvert_lists.append(uvi)
            root = uvverts_left.pop()
            stack = [(root, 0)]
            while stack:
                cur_uvv, depth = stack.pop()
                if cur_uvv.isvisited:
                    continue
                cur_uvv.depth = depth
                cur_uvv.isvisited = True
                uvi.add(cur_uvv)
                for nxt in cur_uvv.uvverts:
                    stack.append((nxt, depth + 1))
            uvverts_left -= uvi

        self.uvislands = [UvIsland(uvverts=uvvs) for uvvs in uvvert_lists]







#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - UTILITY
#=========#=========#=========#=========#=========#=========#=========#=========





def loop_clustersization(bm, uvmap, epsilon):
    loops = {l.index: l for f in bm.faces for l in f.loops}
    kd = KDTree(len(loops))
    for i, l in loops.items():
        u, v = l[uvmap].uv
        pos = (u, v, 0)
        kd.insert(pos, i)
    kd.balance()
    clusterization: dict[BMLoop, tuple[float, float]] = dict() # { loop : uvkey }
    while loops:
        idx0 = next(iter(loops))
        l0 = loops[idx0] # pop below
        u, v = l0[uvmap].uv
        pos0 = (u, v, 0)
        res1 = kd.find_range(pos0, epsilon)
        pos1s = [p for p, _, _ in res1]
        idx1s = [i for _, i, _ in res1]
        for pos1 in pos1s:
            res2 = kd.find_range(pos1, epsilon)
            for pos2, idx2, dst2 in res2:
                if idx2 not in idx1s:
                    return None
        average_pos = sum([Vector(p) for p in pos1s], Vector((0, 0, 0))) / len(pos1s)
        u, v, _ = average_pos
        key_pos = (u, v)
        assert idx0 in idx1s
        for idx in idx1s:
            if idx in loops:
                l = loops.pop(idx) # remove loop from stack
                clusterization[l] = key_pos
    return clusterization
        












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
    uvvs = list(uvi.uvverts)
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

def has_triangle(uvi):
    for uvv1 in uvi.uvverts:
        for uvv2 in uvv1.uvverts:
            if uvv1 is uvv2:
                continue
            if len(uvv1.uvverts & uvv2.uvverts) != 0:
                return True
    return False

def quad_get_opposite_corner(o, a, b):
    try:
        ab = a.uvverts & b.uvverts
        opp = ab - set([o])
        assert len(opp) == 1
        return next(iter(opp))
    except:
        return None

# can recieve non quad uvv
# must return [] to signify fail
def quad_get_opposite_corners(uvv):
    n = len(uvv.uvverts)
    if n <= 1 or n >= 5:
        return []
    if n == 2:
        a, b = uvv.uvverts
        c = quad_get_opposite_corner(uvv, a, b)
        return [c] if c is not None else []
    if n == 3:
        a, b, c = uvv.uvverts
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
        a, b, c, d = uvv.uvverts
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
    n = len(uvv.uvverts)
    if n <= 1 or n >= 5:
        return {}
    neigh2 = set().union(*(n.uvverts for n in uvv.uvverts))
    if len(uvv.uvverts & neigh2) != 0:
        return {}
    if n == 2:
        a, b = uvv.uvverts
        c = quad_get_opposite_corner(uvv, a, b)
        if not c:
            return {}
        return {c: {a, b}}
    if n == 3:
        a, b, c = uvv.uvverts
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
        a, b, c, d = uvv.uvverts
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

def rect_grid_bfs_dist(start:UvVert):
    distances = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nxt in cur.uvverts:
            if nxt not in distances:
                distances[nxt] = distances[cur] + 1
                q.append(nxt)
    return distances


def is_quad_grid(uvi:UvIsland):
    if uvi.degree not in (2, 3, 4): return False
    if has_triangle(uvi): return False
    for uvv in uvi.uvverts:
        l = len(uvv.uvverts)
        c = len(quad_get_opposite_corners(uvv))
        match l:
            case 2: # corner
                if c != 1: return False
            case 3: # border
                if c != 2: return False
            case 4: # c=2->checker c=3->neg.corner c=4->intern
                if c not in (2, 3, 4): return False
            case _:
                return False
    return True


def is_knot_grid(uvi:UvIsland):
    assert uvi.is_quad_grid, "Must first evaluate if is quad grid"
    for uvv in uvi.uvverts:
        if len(uvv.uvverts) == 4:
            if len(quad_get_opposite_corners(uvv)) == 2:
                return True
    return False

def grid_size(uvi:UvIsland):
    uvvs = uvi.uvverts
    if len(uvvs) < 4:
        return None

    corners_ = [uvv for uvv in uvvs if len(uvv.uvverts) == 2]
    vecs = [Vector(uvv.uv) for uvv in corners_]
    center = sum(vecs, Vector((0, 0))) / 4
    corners = sorted(corners_, key=lambda uvv: -angle(center, uvv.uv))
    #    6 5 4
    #   7     3
    #    0 1 2

    # Quad case
    if len(uvvs) == 4:
        A = corners[0]
        B_ = uvvs - (A.uvverts | {A})
        if not B_ or len(B_) != 1:
            return None
        B = next(iter(B_))
        X, Y = uvvs - {A, B}
        if X is corners[1]:
            return 2, 2, A, X, B, Y
        else:
            return 2, 2, A, Y, B, X

    V, E = len(uvvs), len(uvi.uvedges)
    borders = [uvv for uvv in uvvs if len(uvv.uvverts) in (2, 3)]
    interns = [uvv for uvv in uvvs if len(uvv.uvverts) == 4]
    if len(corners) != 4 or len(borders) + len(interns) != V:
        return None

    # Ribbon case
    # Y - + + - B
    # |   | |   |
    # A - + + - X
    if len(interns) == 0:
        A = corners[0]
        Y_ = set(corners) & A.uvverts
        if len(Y_) != 1:
            return None
        Y = next(iter(Y_))
        ax = A; yb = Y
        XB = set(corners) - {A, Y}
        m = 1
        security = len(uvvs)
        visited = set()
        while ax not in XB and yb not in XB and security > 0:
            ax_ = ax.uvverts - ({yb} | visited)
            yb_ = yb.uvverts - ({ax} | visited)
            assert len(ax_) == 1, f"not 1: {len(ax_)}"
            assert len(yb_) == 1, f"not 1: {len(yb_)}"
            visited.update((ax, yb))
            ax = next(iter(ax_))
            yb = next(iter(yb_))
            m += 1
            security -= 1
        X = ax; B = yb
        if X is corners[1]:
            return m, 2, A, X, B, Y
        else:
            return 2, m, A, Y, B, X
        

    # Other case
    A = corners[0]
    walk = [A]
    cur = A
    while True:
        print(cur.index)
        nexts = [uvv for uvv in cur.uvverts if uvv in borders and uvv not in walk]
        if not nexts:
            break
        if len(nexts) > 1 and cur is not A:
            return None
        cur = nexts[0]
        walk.append(cur)

    if len(walk) != len(borders) or A not in cur.uvverts:
        return None

    ordered_corners = [(uvv, idx) for idx, uvv in enumerate(walk) if len(uvv.uvverts) == 2]
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
    flip = ordered_corners[1] == corners[1]
    if flip:
        return m, n, A, X, B, Y
    else:
        return n, m, A, Y, B, X

def is_rect_grid(uvi):
    return grid_size(uvi) is not None


















#=========#=========#=========#=========#=========#=========#=========#=========
# MARK: - FUNCTIONS
#=========#=========#=========#=========#=========#=========#=========#=========


def move_uvv(uvv, uv): # need bmesh.update_edit_mesh(mesh) after
    offset = Vector(uv) - Vector(uvv.uv)
    for l in uvv.loops:
        l[uvv.uvmap].uv += offset

def rotate_uvvs(uvvs, angle, center):
    M = Matrix.Rotation(angle, 2)
    center = Vector(center)
    for uvv in uvvs:
        uv = M @ (uvv.uv - center) + center
        for l in uvv.loops:
            l[uvv.uvmap].uv = uv

def get_uvi_length(uvi):
    return sum([get_uve_length(uve) for uve in uvi.uvedges])

def get_uve_length(uve):
    du = uve.uvv2.u - uve.uvv1.u
    dv = uve.uvv2.v - uve.uvv1.v
    return sqrt(du*du + dv*dv)

def reverse_path(uvi):
    if uvi.is_path:
        n = len(uvi.sorted_uvverts)
        for i, uvv in enumerate(uvi.sorted_uvverts):
            uvv.depth = n - 1 - i
        uvi.head, uvi.tail = (uvi.tail, uvi.head)

def reverse_paths(uvmesh):
    for uvi in uvmesh.uvislands:
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
            ratio = get_uvi_length(uvi) / htdist
            uv_head = htcenter + ratio * (uv_head - htcenter)
            uv_tail = htcenter + ratio * (uv_tail - htcenter)
        uv_head += offset
        uv_tail += offset

        # === length distribution example ===
        # uvedge idx (3)         0      1        2
        # path (1)           o-------o-----o------------o
        # uvvert idx (4)     0       1     2            3
        # distribution (4)   0       0.3   0.5          1.0  (normalized)
        uvv_count = len(uvi.uvverts)
        uve_count = uvv_count - 1
        distribution = [0.0] * uvv_count # init only size
        if even_point_distribution:
            for i in range(uvv_count):
                distribution[i] = i / (uvv_count - 1)
        else:
            acc = 0.0
            for i in range(uve_count):
                acc += get_uve_length(uvi.sorted_uvedges[i])
                distribution[i + 1] = acc / get_uvi_length(uvi)

        for i, uvv in enumerate(uvi.sorted_uvverts):
            uv = lerp(uv_head, uv_tail, distribution[i])
            move_uvv(uvv, uv)

def straighten_paths(uvmesh, keep_paths_length, even_point_distribution, center_mode):
    for uvi in uvmesh.uvislands:
        straighten_path(uvi, keep_paths_length, even_point_distribution, center_mode)

def align_paths(uvmesh):
    # Assert paths are straight
    paths = [uvi for uvi in uvmesh.uvislands if uvi.is_path]
    angles = [uvvs_angle(p.head, p.tail) for p in paths]
    # Mean undirected angle
    c = sum(cos(2 * a) for a in angles)
    s = sum(sin(2 * a) for a in angles)
    mean = (0.5 * atan2(s, c)) % pi
    # Minimal rotation to mean
    for p, a in zip(paths, angles):
        delta = (mean - a + pi / 2) % pi - pi / 2
        center = get_center(p, "HEADTAIL")
        rotate_uvvs(p.uvverts, delta, center)

def align_paths_on_grid(uvmesh):
    paths = [uvi for uvi in uvmesh.uvislands if uvi.is_path]
    if len(paths) <= 1:
        utils.alert(f"Need at least 2 paths, found {len(paths)}")
        return

    uvvs = []
    for p in paths:
        uvvs.extend(p.uvverts)

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
            countX = len(p.uvverts)
            reverse = p.head.uv[0] > p.tail.uv[0]
            for x, uvv in enumerate(p.sorted_uvverts):
                wx = (x / (countX - 1)) # (no div 0: path has min 2 uvv)
                wy = 1 if countY == 1 else y / (countY - 1) # (no div 0: paths has min 2 path)
                if reverse:
                    wx = 1 - wx
                u = lerp(mu, Mu, wx)
                v = lerp(mv, Mv, wy)
                uv = (u, v)
                move_uvv(uvv, uv)
    else:
        countX = len(spaths)
        for x, p in enumerate(spaths):
            countY = len(p.uvverts)
            reverse = p.head.uv[1] > p.tail.uv[1]
            for y, uvv in enumerate(p.sorted_uvverts):
                wx = x / (countX - 1)
                wy = (y / (countY - 1)) if not reverse else (1 - y / (countY - 1))
                u = lerp(mu, Mu, wx)
                v = lerp(mv, Mv, wy)
                uv = (u, v)
                move_uvv(uvv, uv)

def align_grid(uvi, mode="CORNERS"):
    grid_res = grid_size(uvi)
    if grid_res:
        m, n, A, X, B, Y = grid_res
        if mode == "CORNERS":
            tl, tr, br, bl = A.uv.copy(), X.uv.copy(), B.uv.copy(), Y.uv.copy()
        elif mode == "BBOX":
            [[mu, mv], [Mu, Mv]] = get_bounding_box(uvi.uvverts)
            tl = Vector((mu, Mv))
            tr = Vector((Mu, Mv))
            br = Vector((Mu, mv))
            bl = Vector((mu, mv))
        else:
            raise RuntimeError(f"Unknown mode in align grid: {mode}")
        for uvv in uvi.uvverts:
            wx = uvv.x / (m - 1)
            wy = 1 - uvv.y / (n - 1)
            uv = bilinear(tl, tr, br, bl, wx, wy)
            move_uvv(uvv, uv)

def align_grids(uvmesh, mode="CORNERS"):
    for uvi in uvmesh.uvislands:
        align_grid(uvi, mode)










#=========#=========#=========#=========#=========#=========#=========#=========
# PRINT
#=========#=========#=========#=========#=========#=========#=========#=========

def print_uvmesh(uvmesh):
    lines = []
    for uvi in uvmesh.uvislands:
        line = ""
        if uvi.is_path: line += "path, "
        if uvi.is_ring: line += "ring, "
        if uvi.is_quad_grid: line += "quad "
        if uvi.is_knot_grid: line += "knot "
        if uvi.is_rect_grid: line += "rectangle "
        if any([uvi.is_quad_grid, uvi.is_knot_grid,uvi.is_rect_grid]): line += "grid, "
        if line == "": line += "other, "
        line += "|"
        line += f"{len(uvi.uvverts)} uvvs, "
        line += f"{len(uvi.uvedges)} uves, "
        line += f"{len(uvi.uvquads)} uvqs, "
        line += f"{get_uvi_length(uvi):.3f} length"
        lines.append("• " + line)
    print("\n".join(lines))
    return lines

# · • – — ← → ↑ ↓ ○ ● □ ■ △ ◇ ± × ÷ ≠ ≤ ≥ ≈ ° Ø × ✓
