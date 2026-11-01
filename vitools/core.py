"""Utilidades base: easing, fontes, texto com espaçamento e opacidade."""
from PIL import ImageFont


def clamp(t):
    return max(0.0, min(1.0, t))


def ease(t):          # smoothstep
    t = clamp(t); return t * t * (3 - 2 * t)


def ease_in_out(t):   # cubic in-out
    t = clamp(t); return 4 * t ** 3 if t < .5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out(t):      # cubic out
    t = clamp(t); return 1 - (1 - t) ** 3


_FONTS = {}
def font(font_dir, weight, size, family="Montserrat"):
    key = (font_dir, family, weight, size)
    if key not in _FONTS:
        _FONTS[key] = ImageFont.truetype(f"{font_dir}/{family}-{weight}.ttf", size)
    return _FONTS[key]


def text_width(draw, txt, fnt, track):
    return sum(draw.textlength(c, font=fnt) for c in txt) + track * (len(txt) - 1)


def tracked(draw, xy, txt, fnt, fill, track=0, center=True):
    """Desenha texto com letter-spacing. Retorna a largura total."""
    total = text_width(draw, txt, fnt, track)
    x = xy[0] - total / 2 if center else xy[0]
    for c in txt:
        draw.text((x, xy[1]), c, font=fnt, fill=fill)
        x += draw.textlength(c, font=fnt) + track
    return total


def with_opacity(rgba, op):
    out = rgba.copy()
    out.putalpha(rgba.getchannel("A").point(lambda v: int(v * op)))
    return out
