print("### UvEdge.py RELOADED ###")

from math import sqrt, atan2

class UvEdge:
    def __init__(self, uvv_a, uvv_b):
        self.uvv1 = None
        self.uvv2 = None
        self.length = None
        self.angle = None

        if uvv_a.uv[0] < uvv_b.uv[0]:
            self.uvv1 = uvv_a
            self.uvv2 = uvv_b
        elif uvv_a.uv[0] > uvv_b.uv[0]:
            self.uvv1 = uvv_b
            self.uvv2 = uvv_a
        else:
            if uvv_a.uv[1] < uvv_b.uv[1]:
                self.uvv1 = uvv_a
                self.uvv2 = uvv_b
            elif uvv_a.uv[1] > uvv_b.uv[1]:
                self.uvv1 = uvv_b
                self.uvv2 = uvv_a
            else:
                self.uvv1 = uvv_a
                self.uvv2 = uvv_b
                print('UvEdge made of identical UvVert!')
        du = self.uvv1.uv[0] - self.uvv2.uv[0]
        dv = self.uvv1.uv[1] - self.uvv2.uv[1]
        self.length = sqrt(du*du + dv*dv)
        self.angle = atan2(dv, du)

    def __eq__(self, other):
        if not isinstance(other, UvEdge):
            return NotImplemented
        return (
            self.uvv1 is other.uvv1
            and self.uvv2 is other.uvv2
        )

    def __hash__(self):
        return hash((self.uvv1, self.uvv2))