"""Camadas de marca: logo com reveal, cartelas de intro/outro e legendas em chip."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from .core import ease, ease_out, font, tracked, text_width


class Brand:
    def __init__(self, cfg, size, root):
        self.W, self.H = size
        self.primary = tuple(cfg["primary"])
        self.secondary = tuple(cfg["secondary"])
        self.font_dir = f"{root}/{cfg.get('font_dir', 'assets/fonts')}"
        self.mark = Image.open(f"{root}/{cfg['mark']}")
        self.word = Image.open(f"{root}/{cfg['word']}")

    def f(self, weight, size):
        return font(self.font_dir, weight, size)

    def logo_layer(self, color, mark_w, reveal=1.0, word_op=1.0, word_track=0.0):
        """Símbolo revelado de baixo pra cima (wipe suave) + assinatura com tracking animado."""
        W, H = self.W, self.H
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        mh = int(self.mark.height * mark_w / self.mark.width)
        m = np.asarray(self.mark.resize((mark_w, mh), Image.LANCZOS)).astype(float) / 255
        edge = 60
        y = np.arange(mh)[:, None]
        g = np.clip((y - (mh - (mh + edge) * reveal)) / edge, 0, 1)
        mk = Image.new("RGBA", (mark_w, mh), color + (0,))
        mk.putalpha(Image.fromarray((m * g * 255).astype("uint8")))
        top = int(H * 0.40 - mh / 2) - 60
        lay.alpha_composite(mk, ((W - mark_w) // 2, top))
        ww = int(mark_w * 1.05 * (1 + word_track))
        wh = int(self.word.height * ww / self.word.width)
        wm = self.word.resize((ww, wh), Image.LANCZOS).point(lambda v: int(v * word_op))
        wl = Image.new("RGBA", (ww, wh), color + (0,)); wl.putalpha(wm)
        lay.alpha_composite(wl, ((W - ww) // 2, top + mh + 70))
        return lay, top + mh + 70 + wh

    def _card(self, t, bg, fg, mark_w, delay, lines, line_font, line_gap, first_gap, track):
        img = Image.new("RGBA", (self.W, self.H), bg + (255,))
        lay, yb = self.logo_layer(fg, mark_w,
                                  reveal=ease_out((t - delay) / 0.9),
                                  word_op=ease((t - delay - 0.55) / 0.5),
                                  word_track=0.25 * (1 - ease_out((t - delay - 0.55) / 0.9)))
        img.alpha_composite(lay)
        tl = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0)); d = ImageDraw.Draw(tl)
        op = ease((t - delay - 0.95) / 0.45)
        for i, line in enumerate(lines):
            tracked(d, (self.W / 2, yb + first_gap + i * line_gap), line, line_font,
                    fg + (int(220 * op),), track)
        img.alpha_composite(tl)
        return img

    def intro_card(self, t, label="UNBOXING"):
        """Fundo claro (secundária) com logo na cor primária."""
        return self._card(t, self.secondary, self.primary, 520, 0.15,
                          [label] if label else [], self.f("Medium", 30), 0, 90, 14)

    def outro_card(self, t, lines):
        """Fundo escuro (primária) com logo na cor secundária."""
        return self._card(t, self.primary, self.secondary, 440, 0.2,
                          lines, self.f("Light", 40), 55, 110, 3)

    def caption(self, num, total, text, y0=1290):
        """Legenda em chip arredondado, legível sobre qualquer foto."""
        W, H = self.W, self.H
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        fb, fs = self.f("Medium", 56), self.f("SemiBold", 24)
        cw = int(max(text_width(d, text, fb, 3), 180) + 120); ch = 170; x0 = (W - cw) // 2
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + 12, x0 + cw, y0 + ch + 12], radius=34, fill=(0, 0, 0, 110))
        lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
        d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], radius=34, fill=self.secondary + (246,))
        tracked(d, (W / 2, y0 + 30), f"{num}  /  {total}", fs, self.primary + (150,), 9)
        tracked(d, (W / 2, y0 + 66), text, fb, self.primary + (255,), 3)
        return lay
