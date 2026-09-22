print("### UvEdge.py RELOADED ###")

from math import sqrt, atan2

class UvEdge:
    def __init__(self, uvv1, uvv2):
        self.uvv1 = uvv1
        self.uvv2 = uvv2
        self.length = None
        self.angle = None
        self.init()

    def init(self):
        du = self.uvv1.uv[0] - self.uvv2.uv[0]
        dv = self.uvv1.uv[1] - self.uvv2.uv[1]
        self.length = sqrt(du*du + dv*dv)
        self.angle = atan2(dv, du)