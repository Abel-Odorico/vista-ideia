#!/usr/bin/env python3
"""Teste das ferramentas de ritmo humano com material gerado na hora (nenhum vídeo de terceiros).

  python3 qa/teste_ritmo_humano.py        (precisa de ffmpeg; roda em ~1 min)

Confere: vídeo agitado (um bloco pisca a cada meio segundo) reprova em RH-01/RH-02; vídeo calmo (um bloco novo a cada
3 s, parado entre eles) aprova; música 4 dB abaixo da voz reprova RH-06 e 20 dB abaixo aprova; fala com 0,3 s de
antecedência reprova RH-04; o revisor cego com o juiz por medidas dá a vitória ao calmo nas duas ordens e pede ajuste
quando o agitado é a versão nova; o modo manual gera o pacote de 4 pareceres.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ok = falhas = 0


def confere(desc, esperado, obtido):
    global ok, falhas
    if esperado == obtido:
        print(f"  ok    {desc}")
        ok += 1
    else:
        print(f"  FALHA {desc} (esperado {esperado!r}, obtido {obtido!r})")
        falhas += 1


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


def roda(*args):
    p = subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        base = ["-f", "lavfi", "-i", "color=c=0x0B1F3B:s=640x360:r=30:d=12"]
        ff(*base, "-vf", "drawbox=x=200:y=120:w=240:h=120:color=0xB85C4E:t=fill:enable='lt(mod(t,1),0.5)',format=yuv420p",
           "-c:v", "libx264", str(t / "agitado.mp4"))
        caixas = ",".join(f"drawbox=x={60 + 180 * k}:y=120:w=140:h=120:color=0xC9A961:t=fill:enable='gte(t,{3 * k + 1})'" for k in range(3))
        ff(*base, "-vf", caixas + ",format=yuv420p", "-c:v", "libx264", str(t / "calmo.mp4"))

        print("== ritmo_humano.py")
        c, s = roda(AQUI / "ritmo_humano.py", t / "agitado.mp4")
        confere("agitado reprova", 1, c)
        confere("agitado reprova em RH-01 (arrancadas)", True, "FALHA  RH-01" in s)
        c, s = roda(AQUI / "ritmo_humano.py", t / "calmo.mp4", "--json", t / "calmo.json")
        confere("calmo aprova", 0, c)
        m = json.loads((t / "calmo.json").read_text())["medida"]
        confere("calmo: 3 arrancadas (uma por bloco novo)", 3, len(m["arrancadas"]))

        tempo = {"atos": [{"t0": 0, "t1": 4, "fala": {"t0": 1.0, "t1": 3.0}}, {"t0": 4, "t1": 8, "fala": {"t0": 4.3, "t1": 7.5}},
                          {"t0": 8, "t1": 12, "fala": {"t0": 9.0, "t1": 11.0}}]}
        (t / "tempo.json").write_text(json.dumps(tempo))
        c, s = roda(AQUI / "ritmo_humano.py", t / "calmo.mp4", "--tempo", t / "tempo.json")
        confere("fala 0,3 s depois da troca reprova RH-04", True, "FALHA  RH-04" in s)
        confere("RH-04 aponta o ato 01", True, "ato 01 (0.30s)" in s)

        ff("-f", "lavfi", "-i", "sine=frequency=220:duration=12", "-af", "volume=-12dB", str(t / "voz.wav"))
        ff("-f", "lavfi", "-i", "sine=frequency=660:duration=12", "-af", "volume=-16dB", str(t / "musica_alta.wav"))
        ff("-f", "lavfi", "-i", "sine=frequency=660:duration=12", "-af", "volume=-32dB", str(t / "musica_baixa.wav"))
        c, s = roda(AQUI / "ritmo_humano.py", t / "calmo.mp4", "--voz", t / "voz.wav", "--musica", t / "musica_alta.wav")
        confere("música 4 dB abaixo da voz reprova RH-06", True, "FALHA  RH-06" in s)
        c, s = roda(AQUI / "ritmo_humano.py", t / "calmo.mp4", "--voz", t / "voz.wav", "--musica", t / "musica_baixa.wav")
        confere("música 20 dB abaixo da voz passa RH-06", True, "PASSA  RH-06" in s)

        print("== revisor_cego.py")
        c, s = roda(AQUI / "revisor_cego.py", "--anterior", t / "agitado.mp4", "--novo", t / "calmo.mp4",
                    "--juiz", "medidas", "--juiz", "medidas", "--saida", t / "r1", "--semente", "7")
        confere("nova calma contra anterior agitada: sem ajuste (sai 0)", 0, c)
        rel = json.loads((t / "r1" / "relatorio.json").read_text())
        confere("a nova vence os 4 pareceres", 4, rel["decisao"]["votos"]["novo"])
        confere("juiz nunca vê os papéis: rótulos neutros nas folhas", True,
                all(n.startswith("v") for n in rel["rotulos_das_folhas"]))
        c, s = roda(AQUI / "revisor_cego.py", "--anterior", t / "calmo.mp4", "--novo", t / "agitado.mp4",
                    "--juiz", "medidas", "--juiz", "medidas", "--saida", t / "r2", "--semente", "7")
        confere("nova agitada: ajustes pedidos (sai 1)", 1, c)
        confere("o ajuste cita RH-01", True, "AJUSTE RH-01" in s)
        c, s = roda(AQUI / "revisor_cego.py", "--anterior", t / "agitado.mp4", "--novo", t / "calmo.mp4",
                    "--juiz", "manual", "--saida", t / "r3")
        confere("modo manual gera o pacote (sai 0)", 0, c)
        confere("pacote com 4 pareceres", 4, len(list((t / "r3" / "pacote").glob("parecer-*/prompt.md"))))
        prompt = (t / "r3" / "pacote" / "parecer-1" / "prompt.md").read_text()
        confere("o prompt não revela qual é a nova", False, "anterior" in prompt.split("## Regras")[0] or "calmo" in prompt)
    print(f"\n{ok} ok, {falhas} falha(s)")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
