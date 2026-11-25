#!/usr/bin/env python3
"""Confere o projeto JSON contra as regras de ritmo humano (regras/RITMO-HUMANO.md) ANTES de renderizar.

    python3 tools/checar_ritmo.py projects/unboxing.json

O que confere (o render.py roda sozinho e só avisa; não bloqueia):
  RH-02  cada legenda fica na tela o tempo de leitura: 1,5 s, ou 0,5 s + 0,3 s por palavra se der mais
  RH-02  cada foto fica pelo menos 1,5 s (a transição não conta)
  RH-05  entre uma legenda e a próxima, um respiro (não encavalam)
  RC-04  no máximo 2 tipos de transição no vídeo (crossfade e flash contam como tipos)
Depois do render, medir o MP4: python3 tools/ritmo_humano.py output/<video>.mp4
Código de saída: 0 ok, 1 há o que ajustar.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ritmo_humano as rh  # noqa: E402


def conferir(cfg, lim):
    probs = []
    minimo, base, por = lim["dado_fixo_min_s"], lim.get("leitura_base_s", 0.5), lim.get("leitura_s_por_palavra", 0.3)
    caps = sorted(cfg.get("captions", []), key=lambda c: c["start"])
    for c in caps:
        n = len(str(c.get("text", "")).split())
        precisa = max(minimo, base + por * n)
        dura = c["end"] - c["start"]
        if dura + 1e-6 < precisa:
            probs.append(f"RH-02 legenda {c.get('num', '')} \"{c.get('text', '')}\": {dura:.2f} s na tela, precisa de {precisa:.2f} s")
        if n > lim.get("palavras_por_bloco_max", 6):
            probs.append(f"RH-07 legenda {c.get('num', '')}: {n} palavras (máximo {lim.get('palavras_por_bloco_max', 6)})")
    for a, b in zip(caps, caps[1:]):
        if b["start"] < a["end"]:
            probs.append(f"RH-05 legendas {a.get('num', '')} e {b.get('num', '')} encavalam ({b['start']:.2f} s < {a['end']:.2f} s)")
    tr = cfg.get("transition", 0)
    for i, s in enumerate(cfg.get("shots", [])):
        util = s["end"] - s["start"] - tr
        if util + 1e-6 < minimo:
            probs.append(f"RH-02 foto {i + 1} ({Path(s.get('image', '')).name}): {util:.2f} s fora da transição, mínimo {minimo} s")
    tipos = {"crossfade"} if tr else set()
    if cfg.get("flashes"):
        tipos.add("flash")
    if len(tipos) > 2:
        probs.append(f"RC-04 {len(tipos)} tipos de transição ({', '.join(sorted(tipos))}); máximo 2")
    return probs


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    lim, regras = rh.carregar_limites()
    probs = conferir(cfg, lim)
    print(f"  ritmo humano (regras {lim.get('versao')}): {sys.argv[1]}")
    for p in probs:
        print(f"  AJUSTAR {p}")
    print("  ok" if not probs else f"  {len(probs)} ponto(s) para ajustar")
    sys.exit(1 if probs else 0)


if __name__ == "__main__":
    main()
