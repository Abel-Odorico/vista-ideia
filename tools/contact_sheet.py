#!/usr/bin/env python3
"""Folha de contato: monta quadros lado a lado para revisar o vídeo de relance.

    python3 tools/contact_sheet.py output/video.mp4 -n 8 -o output/preview.jpg
"""
import argparse, os, subprocess, tempfile, glob
from PIL import Image


def sheet(images, out, thumb_w=270):
    ims = [im.resize((thumb_w, int(im.height * thumb_w / im.width))) for im in images]
    h = max(im.height for im in ims)
    s = Image.new("RGB", (thumb_w * len(ims), h))
    for i, im in enumerate(ims): s.paste(im, (i * thumb_w, 0))
    s.save(out, quality=88); return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("-n", type=int, default=8)
    ap.add_argument("-o", default="output/preview.jpg")
    a = ap.parse_args()
    dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                         "-of", "csv=p=0", a.video]))
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(a.n):
            t = dur * (k + 0.5) / a.n
            subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", a.video,
                            "-frames:v", "1", f"{tmp}/{k:03d}.jpg"], check=True)
        print("✔", sheet([Image.open(f) for f in sorted(glob.glob(f"{tmp}/*.jpg"))], a.o))
