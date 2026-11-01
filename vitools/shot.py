"""Shot: foto com movimento Ken Burns (zoom + pan) em precisão subpixel."""
from PIL import Image
from .core import ease_in_out


class Shot:
    def __init__(self, path, size, zoom=(1.0, 1.1), center=None):
        self.im = Image.open(path).convert("RGB")
        self.W, self.H = size
        self.k = max(self.W / self.im.width, self.H / self.im.height)
        self.z0, self.z1 = zoom
        mid = (self.im.width / 2, self.im.height / 2)
        self.c0, self.c1 = center if center else (mid, mid)

    def frame(self, t):
        """t de 0 a 1 ao longo da duração do shot."""
        e = ease_in_out(t)
        z = self.z0 + (self.z1 - self.z0) * e
        cx = self.c0[0] + (self.c1[0] - self.c0[0]) * e
        cy = self.c0[1] + (self.c1[1] - self.c0[1]) * e
        sc = 1 / (self.k * z)
        hw, hh = self.W / 2 * sc, self.H / 2 * sc
        cx = min(max(cx, hw), self.im.width - hw)   # nunca mostra borda vazia
        cy = min(max(cy, hh), self.im.height - hh)
        return self.im.transform((self.W, self.H), Image.AFFINE,
                                 (sc, 0, cx - hw, 0, sc, cy - hh), resample=Image.BICUBIC)
