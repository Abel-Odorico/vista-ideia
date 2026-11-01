#!/usr/bin/env python3
"""Renderiza um projeto de vídeo.

    python3 render.py projects/unboxing.json
    python3 render.py projects/unboxing.json --preview   # também gera folha de contato
"""
import argparse, os, sys
from vitools import load_project, render_project

ap = argparse.ArgumentParser()
ap.add_argument("project", help="arquivo JSON do projeto")
ap.add_argument("--preview", action="store_true", help="salva output/preview_<projeto>.jpg com quadros-chave")
a = ap.parse_args()

root = os.path.dirname(os.path.abspath(__file__))
cfg = load_project(a.project)
if not os.path.isdir(os.path.join(root, cfg["brand"].get("font_dir", "assets/fonts"))):
    sys.exit("Fontes não encontradas. Rode antes: ./scripts/setup_fonts.sh")

frames = None
if a.preview:
    fps = cfg.get("fps", 30)
    marks = [cfg["shots"][0]["start"] / 2] + [(s["start"] + s["end"]) / 2 for s in cfg["shots"]] + [cfg["duration"] - 0.3]
    frames = {int(m * fps): None for m in marks}

render_project(cfg, root, preview_frames=frames)

if frames:
    from tools.contact_sheet import sheet
    name = os.path.splitext(os.path.basename(a.project))[0]
    out = os.path.join(root, "output", f"preview_{name}.jpg")
    sheet([f for _, f in sorted(frames.items()) if f is not None], out)
    print(f"✔ {out}")
