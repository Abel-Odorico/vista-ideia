#!/usr/bin/env python3
"""Gera um carrossel editorial do Instagram a partir de um JSON.

    python3 carrossel.py projects/carrossel-unboxing.json            # confere, gera PNGs e a grade
    python3 carrossel.py projects/carrossel-unboxing.json --zonas    # + mapa das áreas que o Instagram cobre
    python3 carrossel.py projects/carrossel-unboxing.json --conferir # só confere o texto, sem renderizar
    python3 carrossel.py projects/carrossel-unboxing.json --html     # só o HTML (abre no navegador)

Padrão visual em docs/carrossel-editorial.md. Ideia de arquitetura do Open Carrusel (MIT).
"""
import argparse, json, os, sys
from vitools.carrossel import conferir, exportar_carrossel

ap = argparse.ArgumentParser()
ap.add_argument("projeto", help="arquivo JSON do carrossel")
ap.add_argument("--conferir", action="store_true", help="só confere as regras de texto")
ap.add_argument("--html", action="store_true", help="gera só o HTML de cada slide")
ap.add_argument("--zonas", action="store_true", help="salva <saida>/zonas/ com as áreas cobertas pelo app")
ap.add_argument("--forcar", action="store_true", help="renderiza mesmo com erro de regra")
a = ap.parse_args()

raiz = os.path.dirname(os.path.abspath(__file__))
with open(a.projeto, encoding="utf-8") as f:
    proj = json.load(f)

probs = conferir(proj, raiz)
for p in probs:
    print(p)
graves = [p for p in probs if p.grave]
if not probs:
    print(f"✔ regras ok ({len(proj['slides'])} slides)")
if a.conferir:
    sys.exit(1 if graves else 0)
if graves and not a.forcar:
    sys.exit(f"✖ {len(graves)} erro(s) de regra. Corrija o JSON ou use --forcar.")

nome = os.path.splitext(os.path.basename(a.projeto))[0]
saida = os.path.join(raiz, proj.get("saida", f"output/{nome}"))
print(f"→ {saida}")
transb = exportar_carrossel(proj, raiz, saida, com_zonas=a.zonas, so_html=a.html)
if a.html:
    print(f"✔ HTML em {saida}/html/")
    sys.exit(0)
print(f"✔ {len(proj['slides'])} PNGs + {saida}/grade.jpg")
if transb:
    sys.exit(f"✖ texto passou da caixa em {len(transb)} slide(s): encurte o texto ou use 'tamanho' no slide.")
