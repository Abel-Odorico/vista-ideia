"""Motor: lê um projeto JSON e renderiza o vídeo via ffmpeg (stdin rawvideo)."""
import json, os, subprocess
from PIL import Image
from .core import ease, ease_out, ease_in_out, with_opacity
from .shot import Shot
from .brand import Brand
from . import fx


def load_project(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def render_project(cfg, root=".", preview_frames=None, log=print):
    W, H = cfg.get("size", [1080, 1920]); FPS = cfg.get("fps", 30); DUR = cfg["duration"]
    P = lambda p: os.path.join(root, p)
    brand = Brand(cfg["brand"], (W, H), root)
    shots = [(Shot(P(s["image"]), (W, H), tuple(s.get("zoom", (1, 1.1))),
                   [tuple(c) for c in s["center"]] if "center" in s else None),
              s["start"], s["end"]) for s in cfg["shots"]]
    first_start, last_end = shots[0][1], shots[-1][2]
    XF = cfg.get("transition", 0.3)

    caps_cfg = cfg.get("captions", [])
    total = cfg.get("caption_total", f"{len(caps_cfg):02d}")
    caps = [(brand.caption(c["num"], total, c["text"], c.get("y", 1290)), c["start"], c["end"]) for c in caps_cfg]

    fxc = cfg.get("fx", {})
    GRAD = fx.bottom_gradient(W, H, fxc.get("bottom_gradient", 120))
    VIG = fx.vignette(W, H, fxc.get("vignette", 110))
    GRAINS = fx.grain_frames(W, H)
    grain_amt = fxc.get("grain", 0.035)

    intro = cfg.get("intro"); outro = cfg.get("outro")
    flashes = cfg.get("flashes", [])

    def scene_at(t):
        frame = None
        for shot, s, e in shots:
            if s <= t <= e:
                img = shot.frame((t - s) / (e - s)).convert("RGBA")
                a = ease((t - s) / XF) if s > first_start else 1.0
                frame = img if frame is None else Image.blend(frame, img, a)
        return frame

    out = P(cfg["output"]); os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    proc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                             "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                             "-crf", str(cfg.get("crf", 18)), "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                            stdin=subprocess.PIPE)
    cover = cfg.get("cover"); N = int(DUR * FPS)
    for i in range(N):
        t = i / FPS
        if intro and t < first_start:
            fr = brand.intro_card(t, intro.get("label", ""))
        else:
            fr = scene_at(min(max(t, first_start), last_end))
            for fl in flashes:
                amt = max(0, 1 - abs(t - fl["at"]) / fl.get("width", 0.28))
                if amt: fr = fx.flash(fr, fl.get("strength", 0.55) * amt)
            fr.alpha_composite(GRAD); fr.alpha_composite(VIG)
            for lay, cs, ce in caps:
                if cs <= t <= ce:
                    op = min(ease((t - cs) / 0.35), ease((ce - t) / 0.3))
                    dy = int(30 * (1 - ease_out((t - cs) / 0.5)))
                    l = with_opacity(lay, op)
                    if dy: l = l.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -dy))
                    fr.alpha_composite(l)
            if intro:  # cortina: cartela de intro sobe e revela a 1ª foto
                cur = intro.get("curtain", 0.65)
                if t < first_start + cur:
                    off = int(-H * ease_in_out((t - first_start) / cur))
                    fr.alpha_composite(brand.intro_card(first_start + (t - first_start) * 0.3,
                                                        intro.get("label", "")), (0, off))
            if outro and t >= outro["start"]:  # cortina: cartela de outro sobe de baixo
                cur = outro.get("curtain", 0.6)
                off = int(H * (1 - ease_in_out((t - outro["start"]) / cur)))
                fr.alpha_composite(brand.outro_card(max(0, t - outro["start"] - 0.4), outro.get("lines", [])), (0, off))
        fr = Image.blend(fr.convert("RGB"), GRAINS[i % len(GRAINS)], grain_amt)
        proc.stdin.write(fr.tobytes())
        if cover and i == int(cover["at"] * FPS): fr.save(P(cover["path"]), quality=92)
        if preview_frames and i in preview_frames: preview_frames[i] = fr.copy()
        if log and i % (FPS * 2) == 0: log(f"  {t:5.1f}s / {DUR}s")
    proc.stdin.close(); proc.wait()
    if log: log(f"✔ {out}")
    return out
