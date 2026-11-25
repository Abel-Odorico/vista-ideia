#!/usr/bin/env python3
"""Confere regras/RITMO-HUMANO.md: cada regra tem data e origem, o bloco Limites é JSON válido com as chaves que as
ferramentas leem, e (com --contra) a cópia é idêntica à de outro repositório.

Uso:
  python3 regras/conferir_regras.py
  python3 regras/conferir_regras.py --contra ../grokbot-video-playbook/regras/RITMO-HUMANO.md
Código de saída: 0 ok, 1 problema.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

CHAVES = ["versao", "arrancadas_por_minuto", "cruzeiro_fracao_min", "dado_fixo_min_s", "intervalos_curtos_max_fracao",
          "antecedencia_cena_s", "respiro_entre_ideias_s", "holofote", "musica_abaixo_da_voz_db",
          "texto_altura_min_fracao", "revisor"]


def conferir(f):
    texto = f.read_text(encoding="utf-8")
    erros = []
    blocos = re.split(r"\n### ", texto)
    ids = []
    for b in blocos[1:]:
        m = re.match(r"(R[HC]-\d\d)", b)
        if not m:
            continue
        ids.append(m.group(1))
        if "**Data:**" not in b:
            erros.append(f"{m.group(1)} sem **Data:**")
        if "**Origem:**" not in b:
            erros.append(f"{m.group(1)} sem **Origem:**")
    for linha in re.findall(r"^\| (RC-\d\d) \|([^|]*)\|([^|]*)\|", texto, re.M):
        ids.append(linha[0])
        if not re.search(r"\d\d/\d\d/\d{4}", linha[1]):
            erros.append(f"{linha[0]} sem data")
        if not linha[2].strip():
            erros.append(f"{linha[0]} sem origem")
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        erros.append(f"ids repetidos: {', '.join(sorted(repetidos))}")
    m = re.search(r"##\s*Limites.*?```json\s*(\{.*?\})\s*```", texto, re.S)
    if not m:
        erros.append("sem o bloco ```json na seção Limites")
    else:
        try:
            lim = json.loads(m.group(1))
            erros += [f"Limites sem a chave {k}" for k in CHAVES if k not in lim]
        except json.JSONDecodeError as e:
            erros.append(f"Limites não é JSON válido: {e}")
    return ids, erros


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivo", nargs="?", default=str(Path(__file__).resolve().parent / "RITMO-HUMANO.md"))
    ap.add_argument("--contra", help="outra cópia que precisa ser idêntica")
    a = ap.parse_args()
    f = Path(a.arquivo)
    ids, erros = conferir(f)
    if a.contra:
        h = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        if h(f) != h(a.contra):
            erros.append(f"diferente de {a.contra}: copie a fonte (grokbot-video-playbook/regras/RITMO-HUMANO.md)")
    print(f"{f}: {len(ids)} regras ({', '.join(ids)})")
    for e in erros:
        print(f"  ERRO {e}")
    print("  ok" if not erros else f"  {len(erros)} problema(s)")
    sys.exit(1 if erros else 0)


if __name__ == "__main__":
    main()
