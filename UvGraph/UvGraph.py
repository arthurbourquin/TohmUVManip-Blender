from math import sin, cos, atan2, pi
from mathutils import Vector

from .UvVert import UvVert, UvVerts
from .UvEdge import UvEdge
from .UvConnectedGraph import UvConnectedGraph
from .utils import lerp, dist, get_angle, get_bounding_box, get_center, alert










class UvGraph:
    def __init__(self, obj, mesh, bm, uvmap):
        self.obj   = obj
        self.mesh  = mesh
        self.bm    = bm
        self.uvmap = uvmap

        self.uvverts = UvVerts(uvmap) # all uvverts, selected or not
        self.uvedges = set() # all uvedges, selected or not
        self.graphs = []
        self.precision = 6
        self.epsilon = 10 ** -self.precision
 
        # Get all uvverts
        for f in self.bm.faces:
            for l in f.loops:
                uvkey = self.create_uvvert_key_from_loop(l)
                self.uvverts.get_or_create(uvkey).add_loop(l)
        for i, uvv in enumerate(self.uvverts.values()):
            uvv.index = i

        # Get all uvedges
        for f in self.bm.faces:
            for l in f.loops:
                uvkey1 = self.create_uvvert_key_from_loop(l)
                uvkey2 = self.create_uvvert_key_from_loop(l.link_loop_next)
                # as we collected all uvverts, keys must exist
                uvv1 = self.uvverts[uvkey1]
                uvv2 = self.uvverts[uvkey2]
                uve = UvEdge(uvv1, uvv2, self.uvmap)
                if uve not in self.uvedges:
                    self.uvedges.add(uve)

        # Set selected neighbors for uvverts
        # (Link uvverts by edge selection, better for path manipulation)
        for uvv in self.uvverts.values():
            for l in uvv.loops:
                #    prev    cur     next   (loops)
                #  o------>o------>o------>
                uvkeys = set()
                if l.link_loop_prev.uv_select_edge:
                    uvkeys.add(self.create_uvvert_key_from_loop(l.link_loop_prev))
                if l.uv_select_edge:
                    uvkeys.add(self.create_uvvert_key_from_loop(l.link_loop_next))
                for uvkey in uvkeys:
                    if uvkey not in uvv.neighbors:
                        uvv.neighbors[uvkey] = self.uvverts[uvkey]

        # Initialize graphs
        to_visit = {uvv for uvv in self.uvverts.values() if uvv.select}
        for uvv in to_visit:
            uvv.depth = -1
        def walk(first, graph):
            stack = [(None, first, 0)]
            while stack:
                prev, cur, depth = stack.pop()
                if cur.depth != -1:
                    continue
                cur.depth = depth
                uvkey = self.create_uvvert_key(cur.uv)
                graph.uvverts[uvkey] = cur
                to_visit.discard(cur)
                nexts = [uvv for uvv in cur.neighbors.values() if uvv != prev]
                for nxt in reversed(nexts):
                    stack.append((cur, nxt, depth + 1))
        index = 0
        while to_visit:
            graph = UvConnectedGraph(self.uvmap)
            graph.index = index
            index += 1
            leaves = sorted(
                (uvv for uvv in to_visit if uvv.isleaf),
                key=lambda uvv: uvv.index
            )
            first = leaves[0] if leaves else min(to_visit, key=lambda uvv: uvv.index)
            graph.root = first
            walk(first, graph)
            self.graphs.append(graph)
        for g in self.graphs:
            g.init()

    def create_uvvert_key(self, uv):
        ku = round(uv[0], self.precision)
        kv = round(uv[1], self.precision)
        return tuple((ku, kv))

    def create_uvvert_key_from_loop(self, loop):
        return self.create_uvvert_key(loop[self.uvmap].uv)










    #=========#=========#=========#=========#=========#=========#=========#=========
    # MODIFICATIONS
    #=========#=========#=========#=========#=========#=========#=========#=========

    def reverse_paths(self):
        paths = [g for g in self.graphs if g.ispath]
        for p in paths:
            p.reverse_path()


    def straighten_paths(self, keep_paths_length, even_point_distribution, center_mode):
        paths = [g for g in self.graphs if g.ispath]
        for p in paths:
            p.straighten_path(keep_paths_length, even_point_distribution, center_mode)


    def align_paths(self):
        # Assert paths are straight
        paths = [g for g in self.graphs if g.ispath]
        angles = [get_angle(p.head, p.tail) for p in paths]
        # Mean undirected angle
        c = sum(cos(2 * a) for a in angles)
        s = sum(sin(2 * a) for a in angles)
        mean = (0.5 * atan2(s, c)) % pi
        # Minimal rotation to mean
        for p, a in zip(paths, angles):
            delta = (mean - a + pi / 2) % pi - pi / 2
            center = get_center(p, "HEADTAIL")
            p.rotate(delta, center)


    def align_paths_on_grid(self):
        paths = [g for g in self.graphs if g.ispath]
        if len(paths) <= 1:
            alert(f"Need at least 2 paths, found {len(paths)}")
            return

        uvvs = []
        for p in paths:
            uvvs.extend(p.uvverts.values())

        [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
        width = Mu - mu
        height = Mv - mv
        print(Mv, mv, height)
        if width <= self.epsilon or height <= self.epsilon:
            alert(f"Unable to guess grid layout, bbox is flat: width: {width}, height:{height}")
            return

        self.straighten_paths(False, True, "HEADTAIL")

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
                    uvv.move((u, v))
                p.update_keys()
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
                    uvv.move((u, v))
                p.update_keys()










    #=========#=========#=========#=========#=========#=========#=========#=========
    # PRINT
    #=========#=========#=========#=========#=========#=========#=========#=========

    def print_self(self):
        lines = []
        from datetime import datetime

        # helpers, decoration

        lines.append("")
        lines.append(f"=== UvGraph Diagnostic === {datetime.now().strftime("%H:%M:%S")}")
        lines.append(f"UvGraph: {self}")
        lines.append(f"total uvverts: {len(self.uvverts)}")
        lines.append(f"total uvedges: {len(self.uvedges)}")
        lines.append("")


        lines.append(f"| {len(self.graphs)} connected graphs:")
        lines.append("| idx | uvv | uve | degree | length | type       ")
        lines.append("|-----|-----|-----|--------|--------|-------- - -")
        def print_graph(graph):
            flag_values = [g.issingleton, g.ispath, g.isring, g.istree, g.ispartialmesh, g.iscyclic]
            flag_labels = ["singleton ", "path ", "ring ", "tree ", "partial-mesh ", "cyclic "]
            flags = "".join(flag_labels[i] if flag else "" for i,flag in enumerate(flag_values))
            line  = f"| {g.index: >3} | {len(g.uvverts): >3} | {len(g.uvedges): >3} "
            line += f"| {g.degree: >6} | {g.length: <6.4f} "
            line += f"| {flags}"
            lines.append(line)
        for g in sorted(self.graphs, key=lambda g: g.index):
            print_graph(g)


        def print_uvv_header():
            lines.append("| uv           | depth | type      | idx-adj     ")
            lines.append("|--------------|-------|-----------|--------- - -")
        def print_uvv(uvv):
            i = uvv.index
            d = uvv.depth
            adj = [uvv.index for uvv in uvv.neighbors.values()]
            flag_values = [uvv.isroot, uvv.isleaf]
            flag_labels = ["root ", "leaf "]
            flags = "".join(flag_labels[i] if flag else ".... " for i,flag in enumerate(flag_values))
            lines.append(f"| {uvv.u:>5.3f}, {uvv.v:>5.3f} | {d:>2}    | {flags}| {i:>2}-{adj}")
        def get_graph_types_string(graph):
            str = ""
            if graph.issingleton: str += "singleton "
            if graph.ispath: str += "path "
            if graph.isring: str += "ring "
            if graph.istree: str += "tree "
            if graph.ispartialmesh: str += "mesh "
            if graph.iscyclic: str += "cyclic "
            return str
        for g in sorted(self.graphs, key=lambda g: g.index):
            types = get_graph_types_string(g)
            lines.append("")
            lines.append(f"| graph {g.index:>2} {types}")
            print_uvv_header()
            for uvv in sorted(g.uvverts.values(), key=lambda uvv: uvv.depth):
                print_uvv(uvv)
            lines.append("")


        lines.append(f"| unrelated")
        print_uvv_header()
        i = 0
        max = 10 # lines
        for uvv in self.uvverts.values():
            if i > max:
                lines.append("| ...")
                break
            if not uvv.select:
                print_uvv(uvv)
            i += 1

        lines.append("==========================")
        print("\n".join(lines))
        return lines
