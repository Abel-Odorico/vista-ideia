"""Efeitos de acabamento: gradiente inferior, vinheta, grão de filme e flash."""
import numpy as np
from PIL import Image


def bottom_gradient(W, H, strength=120, color=(8, 12, 22)):
    gy = np.linspace(0, 1, H)[:, None]
    a = (np.clip((gy - 0.6) / 0.4, 0, 1) ** 1.6 * strength).astype("uint8")
    g = Image.new("RGBA", (W, H), color + (0,)); g.putalpha(Image.fromarray(np.repeat(a, W, 1)))
    return g


def vignette(W, H, strength=110):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    v = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    v.putalpha(Image.fromarray((np.clip((r - 0.75) / 0.6, 0, 1) * strength).astype("uint8")))
    return v


def grain_frames(W, H, n=6, sigma=30, seed=7):
    rng = np.random.default_rng(seed)
    return [Image.fromarray(np.clip(128 + rng.normal(0, sigma, (H // 2, W // 2)), 0, 255)
                            .astype("uint8")).resize((W, H)).convert("RGB") for _ in range(n)]


def flash(frame, amount, color=(255, 246, 228)):
    return Image.blend(frame, Image.new("RGBA", frame.size, color + (255,)), amount)
