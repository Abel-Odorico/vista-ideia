#!/usr/bin/env python3
"""Ritmo humano: mede no ARQUIVO FINAL se o vídeo dá tempo para uma pessoa entender (regras/RITMO-HUMANO.md).

O que mede (só ffmpeg/ffprobe + biblioteca padrão; os limites vêm do bloco "Limites" de regras/RITMO-HUMANO.md):
  RH-01  arrancadas por minuto: cada vez que a tela sai do quase parado ou acelera de repente (corte duro conta),
         e a fração do tempo em velocidade de cruzeiro (movimento constante ou parado, sem arranco).
  RH-02  intervalos entre arrancadas abaixo de 1,5 s (a tela não assentou o bastante para ler), com o segundo.
  RH-04  com --tempo tempo.json (movie-code-motion): a fala de cada ato começa pelo menos 0,6 s depois da troca.
  RH-05  com --tempo ou --falas legenda.vtt/.srt: pausa entre ideias de pelo menos 0,8 s.
  RH-06  com --voz e --musica (trilhas separadas, antes da soma): música pelo menos 12 dB abaixo da voz na fala.
  RH-07  com --ocr e tesseract instalado: altura das letras lidas contra 4% / 3% do lado menor do quadro.

Uso:
  ritmo_humano.py final.mp4
  ritmo_humano.py final.mp4 --tempo episodios/007-x/tempo.json --voz audio/narracao.wav --musica audio/trilha-mixada.wav
  ritmo_humano.py final.mp4 --falas final.vtt --json ritmo.json
  ritmo_humano.py final.mp4 --regras ../outro-repo/regras/RITMO-HUMANO.md

Código de saída: 0 aprovado, 1 reprovado (algum FALHA), 2 erro de uso. AVISO não reprova.
Escala da medida de movimento: cinza 64x36 a 15 quadros por segundo (mede movimento, não detalhe). Os números só
comparam vídeos medidos por esta mesma ferramenta.

Cópia idêntica em: grokbot-video-playbook/ferramentas, movie-code-motion/qa, peep-videos/scripts/motion-qa,
transcribe-peep/ferramentas e vista-ideia/tools. Mude na fonte (grokbot-video-playbook) e copie.
"""
import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

W, H, FPS = 96, 54, 15
GX, GY = 12, 9      # grade de blocos (8x6 px cada): o olho vai atrás de qualquer coisa que comece a se mexer, mesmo pequena
CORTE = 24.0        # diferença média (0-255) do quadro inteiro que conta como corte duro
MOVE = 4.0          # bloco "se mexendo": diferença média do bloco acima disto
QUIETO = 1.5        # bloco "parado": nos 0,25 s anteriores nunca passou disto
JANELA_QUIETA = 0.25  # s de bloco parado antes do arranque (pisca-pisca a cada meio segundo conta cada vez)
REFRATARIO = 0.4    # s: arranques mais próximos que isto são uma arrancada só (entrada agrupada da mesma ideia)

PADRAO = {  # usado só se regras/RITMO-HUMANO.md não for achado
    "versao": "embutido", "arrancadas_por_minuto": {"meta": 22, "maximo": 30}, "cruzeiro_fracao_min": 0.8,
    "dado_fixo_min_s": 1.5, "intervalos_curtos_max_fracao": 0.25, "antecedencia_cena_s": {"min": 0.6, "padrao": 1.0},
    "respiro_entre_ideias_s": {"min": 0.8, "padrao": 1.0}, "musica_abaixo_da_voz_db": {"min": 12, "meta": 15},
    "texto_altura_min_fracao": {"corpo": 0.04, "rotulo": 0.03},
}


# ---------- regras ----------
def achar_regras(explicito=None):
    if explicito:
        return Path(explicito)
    for base in (Path(__file__).resolve().parent, Path.cwd()):
        for p in (base, *base.parents):
            f = p / "regras" / "RITMO-HUMANO.md"
            if f.exists():
                return f
    return None


def carregar_limites(explicito=None):
    """Lê o bloco ```json da seção "Limites" de regras/RITMO-HUMANO.md. Devolve (limites, caminho ou None)."""
    f = achar_regras(explicito)
    if not f or not f.exists():
        if explicito:
            sys.exit(f"regras não encontradas: {explicito}")
        return dict(PADRAO), None
    texto = f.read_text(encoding="utf-8")
    m = re.search(r"##\s*Limites.*?```json\s*(\{.*?\})\s*```", texto, re.S)
    if not m:
        sys.exit(f"{f}: sem o bloco ```json na seção Limites")
    lim = dict(PADRAO)
    lim.update(json.loads(m.group(1)))
    return lim, f


# ---------- vídeo ----------
def sh(args, **kw):
    return subprocess.run(args, capture_output=True, **kw)


def info(path):
    p = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
            "-of", "json", path], text=True)
    if p.returncode:
        sys.exit(f"ffprobe falhou em {path}: {p.stderr.strip()[-300:]}")
    d = json.loads(p.stdout)
    s = (d.get("streams") or [{}])[0]
    return int(s.get("width", 0)), int(s.get("height", 0)), float(d.get("format", {}).get("duration", 0) or 0)


def quadros(path):
    p = sh(["ffmpeg", "-v", "error", "-i", path, "-an", "-vf", f"fps={FPS},scale={W}:{H},format=gray",
            "-f", "rawvideo", "-"])
    if p.returncode:
        sys.exit(f"ffmpeg falhou em {path}: {p.stderr.decode()[-300:]}")
    n = W * H
    return [p.stdout[i:i + n] for i in range(0, len(p.stdout) - n + 1, n)]


def blocos(q):
    """Para cada par de quadros vizinhos: diferença média do quadro (d) e de cada bloco da grade (lista de GX*GY)."""
    bw, bh = W // GX, H // GY
    d, bl = [], []
    for i in range(1, len(q)):
        a, b = q[i - 1], q[i]
        dif = [abs(x - y) for x, y in zip(a, b)]
        d.append(sum(dif) / len(dif))
        soma = [0] * (GX * GY)
        for r in range(H):
            off, gy = r * W, (r // bh) * GX
            for gx in range(GX):
                soma[gy + gx] += sum(dif[off + gx * bw: off + (gx + 1) * bw])
        bl.append([v / (bw * bh) for v in soma])
    return d, bl


def arrancadas(d, bl):
    """Instantes (s) em que a tela arranca: corte duro, ou um bloco que estava parado (0,25 s) começa a se mexer."""
    jan = max(2, round(JANELA_QUIETA * FPS))
    ts, ultimo = [], -9.0
    nb = GX * GY
    for i in range(len(d)):
        t = (i + 1) / FPS
        evento = d[i] > CORTE
        if not evento and i >= 2:
            ini = max(0, i - jan - 1)
            if i - 1 > ini:
                for k in range(nb):
                    if max(bl[i][k], bl[i - 1][k]) > MOVE and max(bl[j][k] for j in range(ini, i - 1)) < QUIETO:
                        evento = True
                        break
        if evento:
            if t - ultimo >= REFRATARIO:
                ts.append(round(t, 2))
            ultimo = t
    return ts


def cruzeiro(arr, dur):
    """Fração do tempo em cruzeiro: baldes de 0,5 s sem nenhum arranque dentro."""
    n = max(1, int(dur / 0.5))
    com = {int(t / 0.5) for t in arr}
    return 1 - len(com & set(range(n))) / n


def medir_video(path):
    w, h, dur = info(path)
    q = quadros(path)
    if len(q) < 3:
        sys.exit(f"{path}: poucos quadros para medir")
    d, bl = blocos(q)
    arr = arrancadas(d, bl)
    dur = dur or len(q) / FPS
    marcos = [0.0] + arr + [dur]
    intervalos = [(round(a, 2), round(b - a, 2)) for a, b in zip(marcos, marcos[1:]) if b > a]
    return {"arquivo": str(path), "largura": w, "altura": h, "duracao": round(dur, 2), "arrancadas": arr,
            "arrancadas_por_minuto": round(len(arr) / (dur / 60), 1) if dur else 0.0,
            "cruzeiro_fracao": round(cruzeiro(arr, dur), 3), "intervalos": intervalos}


# ---------- fala (tempo.json do movie-code-motion, VTT ou SRT) ----------
def ler_tempo(path):
    t = json.loads(Path(path).read_text(encoding="utf-8"))
    atos = []
    for i, a in enumerate(t.get("atos", [])):
        f = a.get("fala")
        atos.append({"ato": i, "t0": a["t0"], "t1": a["t1"], "fala": (f["t0"], f["t1"]) if f else None})
    return atos


def _seg(s):
    s = s.strip().replace(",", ".")
    p = [float(x) for x in s.split(":")]
    return p[-1] + (p[-2] * 60 if len(p) > 1 else 0) + (p[-3] * 3600 if len(p) > 2 else 0)


def ler_falas(path):
    """Intervalos de fala de um .vtt ou .srt."""
    txt = Path(path).read_text(encoding="utf-8", errors="replace")
    return [(_seg(a), _seg(b)) for a, b in re.findall(r"([\d:.,]+)\s*-->\s*([\d:.,]+)", txt)]


def conferir_fala(atos, falas, lim):
    out = {}
    if atos:
        ante = lim["antecedencia_cena_s"]["min"]
        rows = [{"ato": a["ato"], "antecedencia_s": round(a["fala"][0] - a["t0"], 2)} for a in atos if a["fala"]]
        out["antecedencia"] = rows
        out["antecedencia_curta"] = [r for r in rows if r["antecedencia_s"] < ante - 1e-6]
        falas = [a["fala"] for a in atos if a["fala"]]
    if falas:
        falas = sorted(falas)
        resp = lim["respiro_entre_ideias_s"]["min"]
        pausas = [(round(b0, 2), round(a1 - b0, 2)) for (_, b0), (a1, _) in zip(falas, falas[1:])]
        out["pausas"] = pausas
        out["pausas_curtas"] = [p for p in pausas if p[1] < resp - 1e-6]
    return out


# ---------- música x voz ----------
def momentanea(path):
    """Loudness momentânea (janela de 400 ms, LUFS) a cada 0,1 s, pelo ebur128 do ffmpeg."""
    p = sh(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=-",
            "-f", "null", "-"], text=True)
    if p.returncode:
        sys.exit(f"ffmpeg (loudness) falhou em {path}: {p.stderr.strip()[-300:]}")
    ts = [float(x) for x in re.findall(r"pts_time:(\S+)", p.stdout)]
    ms = [float(x) for x in re.findall(r"lavfi\.r128\.M=(\S+)", p.stdout)]
    return list(zip(ts, ms))


def musica_abaixo(voz, musica, falas=None):
    v, m = dict((round(t, 1), x) for t, x in momentanea(voz)), dict((round(t, 1), x) for t, x in momentanea(musica))
    difs = []
    for t, lv in v.items():
        if t not in m or lv < -45:  # só onde há voz de fato
            continue
        if falas and not any(a <= t <= b for a, b in falas):
            continue
        difs.append(lv - max(m[t], -70.0))
    if not difs:
        return None
    difs.sort()
    return {"mediana_db": round(statistics.median(difs), 1), "p10_db": round(difs[len(difs) // 10], 1), "amostras": len(difs)}


# ---------- texto (OCR opcional) ----------
def alturas_texto(path, dur, n=8):
    if not shutil.which("tesseract"):
        return None
    hs = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in range(n):
            t = dur * (k + 0.5) / n
            img = Path(tmp) / f"q{k}.png"
            sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", str(img)])
            if not img.exists():
                continue
            p = sh(["tesseract", str(img), "-", "--psm", "11", "tsv"], text=True)
            for linha in p.stdout.splitlines()[1:]:
                c = linha.split("\t")
                if len(c) == 12 and c[11].strip() and len(c[11].strip()) >= 2 and float(c[10]) >= 60:
                    hs.append((round(t, 1), int(c[9]), c[11].strip()))
    return hs


# ---------- relatório ----------
def avaliar(med, fala, mus, ocr, lim):
    linhas = []

    def add(regra, nome, valor, meta, estado, detalhe=""):
        linhas.append({"regra": regra, "item": nome, "valor": valor, "meta": meta, "estado": estado, "detalhe": detalhe})

    apm, alvo = med["arrancadas_por_minuto"], lim["arrancadas_por_minuto"]
    add("RH-01", "arrancadas por minuto", apm, f"<= {alvo['meta']} (reprova > {alvo['maximo']})",
        "FALHA" if apm > alvo["maximo"] else "AVISO" if apm > alvo["meta"] else "PASSA")
    cz = med["cruzeiro_fracao"]
    add("RH-01", "tempo em cruzeiro", f"{cz * 100:.0f}%", f">= {lim['cruzeiro_fracao_min'] * 100:.0f}%",
        "PASSA" if cz >= lim["cruzeiro_fracao_min"] else "AVISO")
    mn = lim["dado_fixo_min_s"]
    curtos = [iv for iv in med["intervalos"] if iv[1] < mn]
    fr = len(curtos) / len(med["intervalos"]) if med["intervalos"] else 0
    add("RH-02", f"intervalos entre arrancadas < {mn} s", f"{len(curtos)} de {len(med['intervalos'])} ({fr * 100:.0f}%)",
        f"<= {lim['intervalos_curtos_max_fracao'] * 100:.0f}%",
        "FALHA" if fr > lim["intervalos_curtos_max_fracao"] else "PASSA",
        ", ".join(f"{a:.1f}s ({b:.1f}s)" for a, b in curtos[:12]) + (" ..." if len(curtos) > 12 else ""))
    if "antecedencia" in fala:
        c = fala["antecedencia_curta"]
        add("RH-04", "cena montada antes da fala", f"{len(fala['antecedencia']) - len(c)} de {len(fala['antecedencia'])} atos",
            f">= {lim['antecedencia_cena_s']['min']} s antes", "FALHA" if c else "PASSA",
            ", ".join(f"ato {r['ato']:02d} ({r['antecedencia_s']:.2f}s)" for r in c))
    if "pausas" in fala:
        c = fala["pausas_curtas"]
        add("RH-05", "respiro entre ideias", f"{len(fala['pausas']) - len(c)} de {len(fala['pausas'])} pausas",
            f">= {lim['respiro_entre_ideias_s']['min']} s", "AVISO" if c else "PASSA",
            ", ".join(f"{a:.1f}s ({b:.2f}s)" for a, b in c[:12]))
    if mus is not None:
        alvo = lim["musica_abaixo_da_voz_db"]
        add("RH-06", "música abaixo da voz (mediana)", f"{mus['mediana_db']} dB", f">= {alvo['min']} dB (meta {alvo['meta']})",
            "FALHA" if mus["mediana_db"] < alvo["min"] else "AVISO" if mus["mediana_db"] < alvo["meta"] else "PASSA",
            f"10% piores trechos: {mus['p10_db']} dB")
    if ocr is not None:
        lado = min(med["largura"], med["altura"]) or 1080
        minimo = 0.7 * lim["texto_altura_min_fracao"]["rotulo"] * lado  # caixa da palavra ~70% do tamanho da fonte
        miudos = [x for x in ocr if x[1] < minimo]
        add("RH-07", "texto miúdo (OCR)", f"{len(miudos)} de {len(ocr)} palavras", f"altura >= {minimo:.0f} px",
            "FALHA" if miudos else "PASSA", ", ".join(f"{t}s '{w}' {h}px" for t, h, w in miudos[:10]))
    return linhas


def imprime(med, linhas, regras):
    print(f"\n  RITMO HUMANO  {med['arquivo']}  ({med['duracao']} s, {med['largura']}x{med['altura']})")
    print(f"  regras: {regras or 'limites embutidos (regras/RITMO-HUMANO.md não achado)'}")
    for l in linhas:
        print(f"  {l['estado']:<6} {l['regra']}  {l['item']:<38} {str(l['valor']):<22} {l['meta']}")
        if l["detalhe"] and l["estado"] != "PASSA":
            print(f"         {l['detalhe']}")
    falhas = [l for l in linhas if l["estado"] == "FALHA"]
    print(f"  {'REPROVADO' if falhas else 'APROVADO'}")
    if falhas:
        print("  Conserto usual: montar a cena inteira na entrada do ato (a meia luz) e acender com a fala, em vez de fazer")
        print("  cada palavra disparar uma entrada; juntar entradas da mesma ideia; segurar a tela pronta 1,5 s ou mais.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--tempo", help="tempo.json do movie-code-motion (atos com troca e fala)")
    ap.add_argument("--falas", help="legenda .vtt ou .srt com os tempos das falas")
    ap.add_argument("--voz", help="trilha só de voz (antes da soma)")
    ap.add_argument("--musica", help="trilha só de música (antes da soma, já no nível da mixagem)")
    ap.add_argument("--ocr", action="store_true", help="lê o texto de 8 quadros com tesseract (RH-07)")
    ap.add_argument("--regras", help="caminho de regras/RITMO-HUMANO.md (padrão: procura subindo as pastas)")
    ap.add_argument("--json", help="grava a medida e o relatório em JSON")
    a = ap.parse_args()
    if not Path(a.video).exists():
        print(f"vídeo não encontrado: {a.video}", file=sys.stderr)
        sys.exit(2)
    lim, regras = carregar_limites(a.regras)
    med = medir_video(a.video)
    atos = ler_tempo(a.tempo) if a.tempo else None
    falas = ler_falas(a.falas) if a.falas else None
    fala = conferir_fala(atos, falas, lim)
    janelas = [x["fala"] for x in atos if x["fala"]] if atos else falas
    mus = musica_abaixo(a.voz, a.musica, janelas) if a.voz and a.musica else None
    ocr = alturas_texto(a.video, med["duracao"]) if a.ocr else None
    if a.ocr and ocr is None:
        print("  aviso: --ocr pedido, mas o tesseract não está instalado (RH-07 fica para o olho)")
    linhas = avaliar(med, fala, mus, ocr, lim)
    imprime(med, linhas, regras)
    if a.json:
        Path(a.json).write_text(json.dumps({"versao_regras": lim.get("versao"), "medida": med, "fala": fala, "musica": mus,
                                            "linhas": linhas}, ensure_ascii=False, indent=1), encoding="utf-8")
    sys.exit(1 if any(l["estado"] == "FALHA" for l in linhas) else 0)


if __name__ == "__main__":
    main()
