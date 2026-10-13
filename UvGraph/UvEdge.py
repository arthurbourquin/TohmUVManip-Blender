from math import sqrt, atan2

class UvEdge:
    def __init__(self, uvv_a, uvv_b):
        self.uvv1 = None # UvVert()
        self.uvv2 = None # UvVert()

        if uvv_a.u < uvv_b.u:
            self.uvv1 = uvv_a
            self.uvv2 = uvv_b
        elif uvv_a.u > uvv_b.u:
            self.uvv1 = uvv_b
            self.uvv2 = uvv_a
        else:
            if uvv_a.v < uvv_b.v:
                self.uvv1 = uvv_a
                self.uvv2 = uvv_b
            elif uvv_a.v > uvv_b.v:
                self.uvv1 = uvv_b
                self.uvv2 = uvv_a
            else:
                self.uvv1 = uvv_a
                self.uvv2 = uvv_b
                print('UvEdge made of identical UvVert!')

    @property
    def vecdir(self):
        return self.uvv2.uv - self.uvv1.uv
    @property
    def length(self):
        vec = self.vecdir
        return sqrt(vec.x ** 2 + vec.y ** 2)
    @property
    def angle(self):
        vec = self.vecdir
        return atan2(vec.y, vec.x)

    def __eq__(self, other):
        if not isinstance(other, UvEdge):
            return NotImplemented
        return (
            self.uvv1 is other.uvv1
            and self.uvv2 is other.uvv2
        )

    def __hash__(self):
        return hash((self.uvv1, self.uvv2))