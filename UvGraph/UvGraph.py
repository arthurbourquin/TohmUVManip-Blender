from math import sin, cos, atan2, pi
from mathutils import Vector

from .UvVert import UvVert
from .UvEdge import UvEdge
from .UvConnectedGraph import UvConnectedGraph
from .utils import lerp, dist, get_angle, get_bounding_box, get_center


class UvGraph:
    def __init__(self, obj, mesh, bm, uvmap):
        self.obj = obj
        self.mesh = mesh
        self.bm = bm
        self.uvmap = uvmap

        self.uvverts = {}    # all uverts, selected or not
        self.uvedges = set() # all, selected or not
        self.graphs = []
        self.precision = 9
        self.epsilon = 10 ** -self.precision
 
        self.init()

    # INITIALISATION

    def init(self):
        self.init_uvverts()
        self.init_uvedges()
        self.init_links()
        self.init_graphs()

    def create_key(self, uv):
        ku = round(uv.x, self.precision)
        kv = round(uv.y, self.precision)
        return tuple((ku, kv))

    def create_key_from_loop(self, loop):
        uv = loop[self.uvmap].uv
        return self.create_key(uv)


    def init_uvverts(self):
        index = 0
        for f in self.bm.faces:
            for l in f.loops:
                key = self.create_key_from_loop(l)
                if key not in self.uvverts:
                    uvv = UvVert(self.uvmap)
                    uvv.set_uv(key)
                    uvv.index = index
                    index += 1
                    self.uvverts[key] = uvv
                self.uvverts[key].add_loop(l)
        for uvv in self.uvverts.values():
            uvv.update_select()

    def init_uvedges(self):
        for f in self.bm.faces:
            for l in f.loops:
                key1 = self.create_key_from_loop(l)
                key2 = self.create_key_from_loop(l.link_loop_next)
                # as we collected all uvverts, keys must exist
                uvv1 = self.uvverts[key1]
                uvv2 = self.uvverts[key2]
                uve = UvEdge(uvv1, uvv2)
                self.uvedges.add(uve)

    # link uvverts by edge selection, way better for path manipulation
    def init_links(self):
        for uvv in self.uvverts.values():
            for l in uvv.loops:
                # BY EDGE SELECTION
                # assert prev and next exists and are not the same (BMLoop)
                # understand topology:
                # [prev]  --(prev.edge)-->  [cur]  --(cur.edge)-->  [next]
                # - prev.edge selected -> add prev
                # - cur.edge selected  -> add next
                keys = set()
                if l.link_loop_prev.uv_select_edge:
                    keys.add(self.create_key_from_loop(l.link_loop_prev))                    
                if l.uv_select_edge:
                    keys.add(self.create_key_from_loop(l.link_loop_next))                    
                # BY VERT SELECTION
                if l.uv_select_vert == True:
                    keys.add(self.create_key_from_loop(l))
                # SET
                for key in keys:
                    if key not in uvv.neighbors and key != self.create_key(uvv.uv):
                        uvv.neighbors[key] = self.uvverts[key]

    def init_graphs(self):
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
                key = self.create_key(cur.uv)
                graph.uvverts[key] = cur
                to_visit.discard(cur)
                nexts = [uvv for uvv in cur.neighbors.values() if uvv != prev]
                for nxt in reversed(nexts):
                    stack.append((cur, nxt, depth + 1))

        index = 0
        while to_visit:
            graph = UvConnectedGraph()
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
            g.update()


    #=========#=========#=========#=========#=========#=========#=========#=========
    # SELECTIONS
    #=========#=========#=========#=========#=========#=========#=========#=========

    def angle_match(self, a1, a2, tolerance):
        a1 %= (2 * pi)
        a2 %= (2 * pi)
        diff = abs((a1 - a2 + pi) % (2 * pi) - pi)
        return diff <= tolerance

    def select_by_angle(self, target_angle, tolerance):
        for f in self.bm:
            for l in f.loops:
                co1 = Vector(self.create_key_from_loop(l))
                co2 = Vector(self.create_key_from_loop(l.link_loop_next))
                vec_dir = co2 - co1
                loop_angle = atan2(vec_dir.y, vec_dir.x)
                match = self.angle_match(target_angle, loop_angle, tolerance)


            






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
            p.rotate(delta)


    def align_paths_on_grid(self):
        print("align paths on grid")
        # get overall bounding box (befor straightening)
        uvvs = []
        for g in self.graphs:
            if g.ispath:
                uvvs.extend(g.uvverts.values())
        [[mu, mv], [Mu, Mv]] = get_bounding_box(uvvs)
        width = Mu - mu
        height = Mv - mv

        print(f"bbox: min u: {mu}, min v: {mv}, max u: {Mu}, max v: {Mv}, width: {width}, height: {height}")
        if width == 0 and height == 0: # can't align...
            return

        # straighten all paths
        self.straighten_paths(False, True, "HEADTAIL")

        # define layout (vertical or horzontal)
        vertical_count = 0
        horizontal_count = 0
        paths = [g for g in self.graphs if g.ispath]
        if not paths:
            return
        for p in paths:
            u1, v1 = p.head.uv
            u2, v2 = p.tail.uv
            if abs(u1 - u2) > abs(v1 - v2):
                horizontal_count += 1
            else:
                vertical_count += 1
        horizontal_paths_piled_vertically = horizontal_count > vertical_count

        # sort paths by center coordinates
        if horizontal_paths_piled_vertically:
            spaths = sorted(paths, key=lambda path: get_center(path, "HEADTAIL").y)
        else:
            spaths = sorted(paths, key=lambda path: get_center(path, "HEADTAIL").x)

        # modifiy coordinates
        # - single path case
        if len(spaths) == 1:
            print("single path")
            p = spaths[0]
            if width > height:
                countX = len(p.uvverts)
                v = (Mv + mv) / 2
                for x, uvv in enumerate(p.sorted_uvverts):
                    wx = x / (countX - 1)
                    u = lerp(mu, Mu, wx)
                    uvv.set_uv([u, v])
            else:
                countY = len(p.uvverts)
                u = (Mu + Mv) / 2
                for y, uvv in enumerate(p.sorted_uvverts):
                    wy = y / (countY - 1)
                    v = lerp(mv, Mv, wy)
                    uvv.set_uv([u, v])
        # - several paths case
        else:
            print(f"path count: {len(spaths)}")
            if horizontal_paths_piled_vertically:
                countY = len(spaths)
                for y, p in enumerate(spaths):
                    countX = len(p.uvverts)
                    reverse = p.head.uv[0] > p.tail.uv[0]
                    for x, uvv in enumerate(p.sorted_uvverts):
                        wx = (x / (countX - 1))                     # no div 0, path has min 2 uvv
                        wy = 1 if countY == 1 else y / (countY - 1) # if div 0, single path
                        if reverse:
                            wx = 1 - wx
                        u = lerp(mu, Mu, wx)
                        v = lerp(mv, Mv, wy)
                        uvv.set_uv([u, v])
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
                        uvv.set_uv([u, v])



    #=========#=========#=========#=========#=========#=========#=========#=========
    # TEST
    #=========#=========#=========#=========#=========#=========#=========#=========

    def put_path_en_bas(self):
        for g in self.graphs:
            if g.ispath:
                for i, uvv in enumerate(g.sorted_uvverts):
                    pos = i / (len(g.uvverts) - 1)
                    uvv.set_uv([pos, 0])


    #=========#=========#=========#=========#=========#=========#=========#=========
    # PRINT
    #=========#=========#=========#=========#=========#=========#=========#=========

    def print_self(self):
        from datetime import datetime

        # helpers, decoration

        print("")
        print(f"=== UvGraph Diagnostic === {datetime.now().strftime("%H:%M:%S")}")
        print(f"UvGraph: {self}")
        print(f"total uvverts: {len(self.uvverts)}")
        print(f"total uvedges: {len(self.uvedges)}")
        print("")


        print(f"| {len(self.graphs)} connected graphs:")
        print("| idx | uvv | uve | degree | length | type       ")
        print("|-----|-----|-----|--------|--------|-------- - -")
        def print_graph(graph):
            flag_values = [g.issingleton, g.ispath, g.isring, g.istree, g.ispartialmesh, g.iscyclic]
            flag_labels = ["singleton ", "path ", "ring ", "tree ", "partial-mesh ", "cyclic "]
            flags = "".join(flag_labels[i] if flag else "" for i,flag in enumerate(flag_values))
            line  = f"| {g.index: >3} | {len(g.uvverts): >3} | {len(g.uvedges): >3} "
            line += f"| {g.degree: >6} | {g.length: <6.4f} "
            line += f"| {flags}"
            print(line)
        for g in sorted(self.graphs, key=lambda g: g.index):
            print_graph(g)


        def print_uvv_header():
            print("| uv           | depth | type      | idx-adj     ")
            print("|--------------|-------|-----------|--------- - -")
        def print_uvv(uvv):
            i = uvv.index
            d = uvv.depth
            adj = [uvv.index for uvv in uvv.neighbors.values()]
            flag_values = [uvv.isroot, uvv.isleaf]
            flag_labels = ["root ", "leaf "]
            flags = "".join(flag_labels[i] if flag else ".... " for i,flag in enumerate(flag_values))
            print(f"| {uvv.u:>5.3f}, {uvv.v:>5.3f} | {d:>2}    | {flags}| {i:>2}-{adj}")
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
            print("")
            print(f"| graph {g.index:>2} {types}")
            print_uvv_header()
            for uvv in sorted(g.uvverts.values(), key=lambda uvv: uvv.depth):
                print_uvv(uvv)
            print("")


        print(f"| unrelated")
        print_uvv_header()
        i = 0
        max = 10 # lines
        for uvv in self.uvverts.values():
            if i > max:
                print("| ...")
                break
            if not uvv.select:
                print_uvv(uvv)
            i += 1

        print("==========================")
