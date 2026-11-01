#!/usr/bin/env python3
"""Extrai a logo de uma arte (fundo claro + logo escura) como máscaras recoloríveis.

Gera dois PNGs em tons de cinza (branco = logo): o símbolo e a assinatura,
separados automaticamente pela faixa vazia entre eles.

    python3 tools/extract_logo.py assets/logo/brand-board.png --box 735 430 955 605 -o assets/logo
    # --box = recorte x0 y0 x1 y1 onde está a versão "escura sobre claro" da logo
"""
import argparse, os
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("--box", type=int, nargs=4, required=True)
ap.add_argument("--scale", type=int, default=6, help="upscale antes de gerar a máscara (nitidez)")
ap.add_argument("--light", type=float, default=205, help="luminância considerada fundo")
ap.add_argument("--soft", type=float, default=120, help="largura da transição da borda")
ap.add_argument("-o", "--out", default="assets/logo")
a = ap.parse_args()

im = Image.open(a.image).convert("RGB").crop(tuple(a.box))
im = im.resize((im.width * a.scale, im.height * a.scale), Image.LANCZOS)
px = np.asarray(im).astype(float); L = px.mean(2)
alpha = np.clip((a.light - L) / a.soft, 0, 1)
print("cor da logo (RGB):", tuple(px[L < 60].mean(0).astype(int)) if (L < 60).any() else "n/d")

rows = alpha.sum(1) > 2
ys = np.where(rows)[0]
gaps = [y for y in range(ys.min(), ys.max()) if not rows[y]]
split = (gaps[0] + gaps[-1]) // 2 if gaps else None

def save(sub, name):
    yy, xx = np.where(sub > 0.08)
    crop = sub[yy.min():yy.max() + 1, xx.min():xx.max() + 1]
    path = os.path.join(a.out, name); Image.fromarray((crop * 255).astype("uint8")).save(path)
    print(f"✔ {path} {crop.shape[1]}x{crop.shape[0]}")

os.makedirs(a.out, exist_ok=True)
if split:
    save(alpha[:split], "mark.png"); save(alpha[split:], "word.png")
else:
    save(alpha, "mark.png"); print("aviso: sem faixa vazia — gerado só mark.png")
