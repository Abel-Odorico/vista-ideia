#!/usr/bin/env python3
"""Revisor cego: 2 juízes de IA comparam a versão anterior e a nova de um vídeo sem saber qual é qual (RH-08).

Cada juiz vê as duas versões rotuladas só como X e Y, nas DUAS ordens (anterior como X e depois como Y), então são
4 pareceres para 2 juízes. Cada parecer dá nota por critério, diz qual versão prefere e lista os erros graves com o
segundo. Só depois de todos os pareceres o revisor desfaz o sorteio e decide:
  - veredito: a versão nova vence se ganhar pelo menos 3 dos 4 pareceres; a anterior vence com 3 ou mais; senão empate.
  - ajustes: só ERRO GRAVE da versão nova vira pedido de ajuste (lista em regras/RITMO-HUMANO.md, RH-08). Um erro grave
    entra quando 2 pareceres apontam a mesma regra; apontado por 1 só fica "a conferir" (olho humano). As medidas também
    pedem ajuste sozinhas: ritmo humano reprovado na nova, ou cor/nitidez abaixo do mínimo contra a anterior.
O que cada juiz recebe: folhas de quadros de cada versão (cada quadro no tamanho de uma tela de celular: se não dá para
ler ali, é texto miúdo), as medidas de ritmo humano (ritmo_humano.py) e de imagem, a fala com tempo quando houver
(--tempo-anterior/--tempo-novo, tempo.json do movie-code-motion, ou --falas-* .vtt/.srt) e as regras inteiras.

Juízes (--juiz, duas vezes; padrão: "revisor.juizes" do bloco Limites de regras/RITMO-HUMANO.md, ou REVISOR_JUIZES):
  openrouter:<modelo>   OPENROUTER_API_KEY (ex.: openrouter:anthropic/claude-sonnet-4.5, openrouter:google/gemini-2.5-pro)
  anthropic:<modelo>    ANTHROPIC_API_KEY
  openai:<modelo>       OPENAI_API_KEY (OPENAI_BASE_URL troca o endereço: serve para qualquer API no formato OpenAI)
  xai:<modelo>          XAI_API_KEY (Grok)
  gemini:<modelo>       GEMINI_API_KEY (endpoint compatível com OpenAI do Google)
  manual                não chama ninguém: grava em <saida>/pacote/ o prompt e as imagens de cada parecer para colar em
                        qualquer IA (ou pessoa); as respostas voltam com --pareceres <pasta com parecer-1.json ...>
  medidas               juiz sem IA, só pelas medidas (serve para testar o fluxo; não conta como juiz de IA)
As chaves vêm do ambiente ou do .env mais próximo. Nenhuma chave é impressa.

Uso:
  revisor_cego.py --anterior v1.mp4 --novo v2.mp4
  revisor_cego.py --anterior prontos/.../007.mp4 --novo episodios/007-x/007-x-final.mp4 --tempo-novo episodios/007-x/tempo.json
  revisor_cego.py --anterior a.mp4 --novo b.mp4 --juiz manual            # gera o pacote
  revisor_cego.py --anterior a.mp4 --novo b.mp4 --pareceres revisao-cega/pacote   # lê as respostas e decide
Saída: <saida>/relatorio.json e <saida>/RELATORIO.md (padrão: revisao-cega/ ao lado do vídeo novo).
Código de saída: 0 sem ajuste pedido, 1 ajustes pedidos (ou a anterior venceu), 2 erro de uso ou de juiz.

Cópia idêntica em: grokbot-video-playbook/ferramentas (fonte), movie-code-motion/qa, peep-videos/scripts/motion-qa,
transcribe-peep/ferramentas e vista-ideia/tools. Precisa do ritmo_humano.py na mesma pasta.
"""
import argparse
import base64
import json
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ritmo_humano as rh  # noqa: E402

CRITERIOS = {
    "clareza": "dá para entender a ideia de cada cena sem pausar",
    "tempo_de_leitura": "dado e texto ficam parados o bastante para ler (RH-02)",
    "movimento": "o movimento segue a ideia, não a sílaba; pouca arrancada (RH-01)",
    "holofote": "o elemento falado está em destaque e o resto a meia luz (RH-03)",
    "cena_antes_da_fala": "a cena já está montada quando a fala chega nela (RH-04)",
    "legibilidade_celular": "texto grande o bastante para ler no celular (RH-07)",
    "acabamento": "cor, nitidez, marca e paleta corretas, sem corte quebrado",
}
GRAVES = ("texto ou número errado contra o roteiro; informação que some antes de dar para ler; fala sobre algo que não "
          "está na tela; música cobrindo a voz; texto ilegível no celular; corte quebrado, quadro preto ou tela travada; "
          "marca ou paleta errada")


# ---------- chaves ----------
def chave(nome):
    if os.environ.get(nome):
        return os.environ[nome]
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            f = p / ".env"
            if f.exists():
                for linha in f.read_text(encoding="utf-8", errors="replace").splitlines():
                    if linha.startswith(nome + "="):
                        v = linha.split("=", 1)[1].strip().strip('"').strip("'")
                        if v:
                            return v
    return None


# ---------- material para os juízes ----------
def folhas(video, pasta, n, rotulo):
    """n quadros espalhados pelo vídeo em folhas 4x3 (cada quadro com 480 px de largura, o tamanho de um celular)."""
    pasta.mkdir(parents=True, exist_ok=True)
    _, _, dur = rh.info(video)
    tempos = [round(dur * (k + 0.5) / n, 2) for k in range(n)]
    imgs = []
    with tempfile.TemporaryDirectory() as tmp:
        for k, t in enumerate(tempos):
            out = Path(tmp) / f"q{k:03d}.png"
            rh.sh(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1",
                   "-vf", "scale=480:-2", str(out)])
        por_folha = 12
        for f in range(0, n, por_folha):
            lista = Path(tmp) / f"lista{f}.txt"
            nomes = [Path(tmp) / f"q{k:03d}.png" for k in range(f, min(n, f + por_folha))]
            nomes = [x for x in nomes if x.exists()]
            if not nomes:
                continue
            lista.write_text("".join(f"file '{x}'\n" for x in nomes))
            destino = pasta / f"{rotulo}-folha{f // por_folha + 1}.jpg"
            rh.sh(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lista),
                   "-vf", "tile=4x3:padding=8:color=0x202020", "-frames:v", "1", "-q:v", "3", str(destino)])
            if destino.exists():
                imgs.append((destino, tempos[f:f + len(nomes)]))
    return imgs


def qualidade(video, n=3):
    """Saturação média (SATAVG do signalstats) e nitidez (variância do laplaciano em cinza 320x180) em n quadros."""
    _, _, dur = rh.info(video)
    sats, nits = [], []
    for k in range(n):
        t = dur * (k + 1) / (n + 1)
        p = rh.sh(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                   "signalstats,metadata=mode=print:key=lavfi.signalstats.SATAVG:file=-", "-f", "null", "-"], text=True)
        m = re.findall(r"SATAVG=(\S+)", p.stdout)
        if m:
            sats.append(float(m[0]))
        p = rh.sh(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-frames:v", "1", "-vf",
                   "scale=320:180,format=gray", "-f", "rawvideo", "-"])
        px, w, h = p.stdout, 320, 180
        if len(px) >= w * h:
            lap = [4 * px[y * w + x] - px[y * w + x - 1] - px[y * w + x + 1] - px[(y - 1) * w + x] - px[(y + 1) * w + x]
                   for y in range(1, h - 1) for x in range(1, w - 1)]
            nits.append(statistics.pvariance(lap))
    return {"saturacao": round(statistics.mean(sats), 2) if sats else None,
            "nitidez": round(statistics.mean(nits), 1) if nits else None}


def falas_texto(tempo=None, vtt=None):
    linhas = []
    if tempo:
        for i, a in enumerate(json.loads(Path(tempo).read_text(encoding="utf-8")).get("atos", [])):
            f = a.get("fala")
            linhas.append(f"ato {i:02d} tela {a['t0']:.1f}-{a['t1']:.1f}s" + (f" | fala {f['t0']:.1f}-{f['t1']:.1f}s: {f.get('texto', '')}" if f else " | sem fala"))
    elif vtt:
        txt = Path(vtt).read_text(encoding="utf-8", errors="replace")
        for a, b, t in re.findall(r"([\d:.,]+)\s*-->\s*([\d:.,]+)[^\n]*\n(.+?)(?:\n\n|\Z)", txt, re.S):
            linhas.append(f"{rh._seg(a):.1f}-{rh._seg(b):.1f}s: {' '.join(t.split())}")
    return "\n".join(linhas)


def medir_versao(video, tempo, vtt, lim):
    med = rh.medir_video(str(video))
    atos = rh.ler_tempo(tempo) if tempo else None
    fala = rh.conferir_fala(atos, rh.ler_falas(vtt) if vtt else None, lim)
    linhas = rh.avaliar(med, fala, None, None, lim)
    return {"medida": {k: med[k] for k in ("duracao", "largura", "altura", "arrancadas_por_minuto", "cruzeiro_fracao")},
            "arrancadas": med["arrancadas"], "linhas": linhas, "qualidade": qualidade(video),
            "falas": falas_texto(tempo, vtt)}


def bloco_medidas(rot, m):
    ls = [f"Versão {rot}: {m['medida']['duracao']} s, {m['medida']['largura']}x{m['medida']['altura']}"]
    for l in m["linhas"]:
        ls.append(f"  {l['regra']} {l['item']}: {l['valor']} (meta {l['meta']}) {l['estado']}" + (f" [{l['detalhe']}]" if l["detalhe"] and l["estado"] != "PASSA" else ""))
    q = m["qualidade"]
    ls.append(f"  imagem: saturação média {q['saturacao']}, nitidez {q['nitidez']}")
    ls.append(f"  segundos das arrancadas: {', '.join(f'{t:.1f}' for t in m['arrancadas'][:80])}")
    if m["falas"]:
        ls.append("  fala com tempo:\n" + "\n".join("    " + x for x in m["falas"].splitlines()))
    return "\n".join(ls)


def montar_prompt(regras_txt, ordem, med, imgs):
    """ordem = [("X", "anterior"|"novo"), ("Y", ...)]: o papel nunca entra no texto, só o rótulo."""
    partes = [
        "Você é juiz numa prova cega de edição de vídeo. Há duas versões do mesmo vídeo, X e Y. Você não sabe qual é a "
        "antiga e qual é a nova, e isso não importa: julgue só o que vê e as medidas. O público é humano e assiste no "
        "celular; o vídeo precisa dar tempo para entender (as regras abaixo explicam por quê).",
        "## Regras (arquivo regras/RITMO-HUMANO.md)\n" + regras_txt,
        "## Medidas feitas no arquivo final de cada versão (por código, confie nelas)",
    ]
    for rot, papel in ordem:
        partes.append(bloco_medidas(rot, med[papel]))
    partes.append("## Quadros\nAs imagens a seguir vêm em ordem: primeiro todas as folhas da versão X, depois as da Y. Cada "
                  "folha tem até 12 quadros, da esquerda para a direita e de cima para baixo, nos segundos indicados. Cada "
                  "quadro tem a largura de uma tela de celular: texto que você não consegue ler aqui é texto miúdo.")
    for rot, papel in ordem:
        for k, (_, ts) in enumerate(imgs[papel]):
            partes.append(f"Versão {rot}, folha {k + 1}: quadros em {', '.join(f'{t:.1f}s' for t in ts)}")
    partes.append(
        "## O que responder\nResponda SÓ com um objeto JSON, sem texto antes ou depois, neste formato:\n"
        '{"notas": {"X": {' + ", ".join(f'"{c}": 1-10' for c in CRITERIOS) + '}, "Y": {...mesmos critérios}},\n'
        ' "preferida": "X" ou "Y" ou "empate",\n'
        ' "erros_graves": [{"versao": "X" ou "Y", "segundo": número, "regra": "RH-0n ou RC-0n", "descricao": "o que está errado e o conserto"}],\n'
        ' "comentario": "até 3 frases: por que preferiu"}\n'
        "Critérios: " + "; ".join(f"{c} = {d}" for c, d in CRITERIOS.items()) + ".\n"
        f"Erro grave é só isto: {GRAVES}. Preferência de gosto NÃO é erro grave. Se não houver erro grave, mande a lista vazia.")
    return "\n\n".join(partes)


# ---------- juízes ----------
OPENAI_COMPAT = {
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
    "openai": (os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"), "OPENAI_API_KEY"),
    "xai": ("https://api.x.ai/v1", "XAI_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
}


def post(url, corpo, cab, tentativas=2):
    dados = json.dumps(corpo).encode()
    for k in range(tentativas):
        try:
            req = urllib.request.Request(url, data=dados, headers={"Content-Type": "application/json", **cab})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 529) and k + 1 < tentativas:
                time.sleep(8)
                continue
            raise RuntimeError(f"HTTP {e.code}: {msg}")
        except urllib.error.URLError as e:
            if k + 1 < tentativas:
                time.sleep(5)
                continue
            raise RuntimeError(f"sem conexão: {e.reason}")


def b64(p):
    return base64.b64encode(Path(p).read_bytes()).decode()


def chamar_juiz(juiz, prompt, imagens):
    prov, _, modelo = juiz.partition(":")
    if prov == "anthropic":
        k = chave("ANTHROPIC_API_KEY")
        if not k:
            raise RuntimeError("ANTHROPIC_API_KEY ausente")
        conteudo = [{"type": "text", "text": prompt}] + [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64(p)}} for p in imagens]
        r = post("https://api.anthropic.com/v1/messages", {"model": modelo, "max_tokens": 3000,
                 "messages": [{"role": "user", "content": conteudo}]}, {"x-api-key": k, "anthropic-version": "2023-06-01"})
        return "".join(b.get("text", "") for b in r.get("content", []))
    if prov in OPENAI_COMPAT:
        base, nome = OPENAI_COMPAT[prov]
        k = chave(nome)
        if not k:
            raise RuntimeError(f"{nome} ausente")
        conteudo = [{"type": "text", "text": prompt}] + [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64(p)}"}} for p in imagens]
        r = post(f"{base}/chat/completions", {"model": modelo, "max_tokens": 3000, "temperature": 0.2,
                 "messages": [{"role": "user", "content": conteudo}]}, {"Authorization": f"Bearer {k}"})
        return r["choices"][0]["message"]["content"] or ""
    raise RuntimeError(f"juiz desconhecido: {juiz}")


def juiz_medidas(ordem, med):
    """Sem IA: prefere a versão com menos FALHA/AVISO nas medidas e aponta como grave cada FALHA."""
    def custo(m):
        return sum({"FALHA": 3, "AVISO": 1}.get(l["estado"], 0) for l in m["linhas"]) + m["medida"]["arrancadas_por_minuto"] / 30
    rot = {papel: r for r, papel in ordem}
    cx, cy = custo(med[ordem[0][1]]), custo(med[ordem[1][1]])
    graves = []  # as FALHAs das medidas já viram ajuste sozinhas em decidir(); este juiz só compara
    pref = "empate" if abs(cx - cy) < 0.5 else ("X" if cx < cy else "Y")
    nota = lambda c: max(1, min(10, round(10 - c)))
    return json.dumps({"notas": {"X": {c: nota(cx) for c in CRITERIOS}, "Y": {c: nota(cy) for c in CRITERIOS}},
                       "preferida": pref, "erros_graves": graves, "comentario": "juiz por medidas (sem IA)"})


def ler_json(texto):
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        raise ValueError("a resposta não tem JSON")
    d = json.loads(m.group(0))
    if d.get("preferida") not in ("X", "Y", "empate"):
        raise ValueError(f"preferida inválida: {d.get('preferida')}")
    return d


# ---------- decisão ----------
def decidir(pareceres, med, lim):
    votos = {"novo": 0, "anterior": 0, "empate": 0}
    graves = {}
    notas = {"novo": {}, "anterior": {}}
    for p in pareceres:
        mapa = dict(p["ordem"])  # rótulo -> papel
        votos[mapa.get(p["resposta"]["preferida"], "empate")] += 1
        for rot, papel in mapa.items():
            for c, v in (p["resposta"].get("notas", {}).get(rot) or {}).items():
                if isinstance(v, (int, float)):
                    notas[papel].setdefault(c, []).append(v)
        for e in p["resposta"].get("erros_graves") or []:
            if mapa.get(e.get("versao")) != "novo":
                continue
            r = str(e.get("regra") or "?").upper()
            graves.setdefault(r, []).append({"juiz": p["juiz"], "parecer": p["n"], "segundo": e.get("segundo"),
                                             "descricao": e.get("descricao", "")})
    n = len(pareceres)
    veredito = "novo vence" if votos["novo"] >= max(2, round(n * 0.75)) else \
        "anterior vence" if votos["anterior"] >= max(2, round(n * 0.75)) else "empate"
    ajustes, conferir = [], []
    for r, lst in sorted(graves.items()):
        vistos, unicos = set(), []
        for c in lst:  # o mesmo erro descrito igual por pareceres diferentes aparece uma vez só
            chave_c = (str(c.get("segundo")), c["descricao"].strip().lower()[:80])
            if chave_c not in vistos:
                vistos.add(chave_c)
                unicos.append(c)
        (ajustes if len(lst) >= 2 else conferir).append({"regra": r, "origem": "juízes", "apontado_por": len(lst), "casos": unicos})
    for l in med["novo"]["linhas"]:
        if l["estado"] == "FALHA":
            ajustes.append({"regra": l["regra"], "origem": "medida", "casos": [{"descricao": f"{l['item']}: {l['valor']} (meta {l['meta']}) {l['detalhe']}".strip()}]})
    qa, qn, ql = med["anterior"]["qualidade"], med["novo"]["qualidade"], lim.get("qualidade_contra_anterior", {"cor_min": 0.8, "nitidez_min": 0.7})
    razoes = {}
    for k, mn in (("saturacao", ql["cor_min"]), ("nitidez", ql["nitidez_min"])):
        if qa.get(k) and qn.get(k) is not None:
            razoes[k] = round(qn[k] / qa[k], 2)
            if razoes[k] < mn:
                ajustes.append({"regra": "RC-06", "origem": "medida", "casos": [{"descricao": f"{k} da nova = {razoes[k] * 100:.0f}% da anterior (mínimo {mn * 100:.0f}%)"}]})
    media = {papel: {c: round(statistics.mean(v), 1) for c, v in d.items()} for papel, d in notas.items()}
    aprovado = not ajustes and veredito != "anterior vence"
    return {"veredito": veredito, "votos": votos, "aprovado": aprovado, "ajustes": ajustes, "a_conferir": conferir,
            "notas_medias": media, "qualidade_razao_novo_sobre_anterior": razoes}


def relatorio_md(rel):
    d = rel["decisao"]
    ls = [f"# Revisão cega ({rel['data']})", "",
          f"- Anterior: `{rel['anterior']}`", f"- Nova: `{rel['novo']}`",
          f"- Juízes: {', '.join(rel['juizes'])} ({len(rel['pareceres'])} pareceres, cada juiz nas duas ordens)",
          f"- Regras: versão {rel['versao_regras']}", "",
          f"## Resultado: {d['veredito']}, {'sem ajuste pedido' if d['aprovado'] else 'AJUSTES PEDIDOS'}", "",
          f"Votos: nova {d['votos']['novo']}, anterior {d['votos']['anterior']}, empate {d['votos']['empate']}.", ""]
    if d["ajustes"]:
        ls += ["### Ajustes pedidos (erro grave na versão nova)", ""]
        for a in d["ajustes"]:
            for c in a["casos"]:
                seg = f" em {c['segundo']}s" if c.get("segundo") not in (None, 0, "") else ""
                ls.append(f"- **{a['regra']}** ({a['origem']}{', ' + str(a.get('apontado_por')) + ' pareceres' if a.get('apontado_por') else ''}){seg}: {c['descricao']}")
        ls.append("")
    if d["a_conferir"]:
        ls += ["### A conferir no olho (apontado por um parecer só)", ""]
        for a in d["a_conferir"]:
            for c in a["casos"]:
                ls.append(f"- {a['regra']} em {c.get('segundo')}s ({c['juiz']}): {c['descricao']}")
        ls.append("")
    ls += ["### Notas médias", "", "| critério | anterior | nova |", "|---|---|---|"]
    for c in CRITERIOS:
        ls.append(f"| {c} | {d['notas_medias']['anterior'].get(c, '-')} | {d['notas_medias']['novo'].get(c, '-')} |")
    ls += ["", "### Medidas", ""]
    for papel in ("anterior", "novo"):
        m = rel["medidas"][papel]
        ls.append(f"- {papel}: {m['medida']['duracao']} s, {m['medida']['arrancadas_por_minuto']} arrancadas/min, "
                  f"cruzeiro {m['medida']['cruzeiro_fracao'] * 100:.0f}%, " +
                  ", ".join(f"{l['regra']} {l['estado']}" for l in m["linhas"]))
    ls += ["", "### Pareceres", ""]
    for p in rel["pareceres"]:
        mapa = dict(p["ordem"])
        r = p["resposta"]
        ls.append(f"- {p['n']}. {p['juiz']} (X = {mapa['X']}, Y = {mapa['Y']}): preferiu "
                  f"{mapa.get(r['preferida'], 'empate')}. {r.get('comentario', '')}")
    return "\n".join(ls) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--anterior", required=True)
    ap.add_argument("--novo", required=True)
    ap.add_argument("--tempo-anterior")
    ap.add_argument("--tempo-novo")
    ap.add_argument("--falas-anterior")
    ap.add_argument("--falas-novo")
    ap.add_argument("--juiz", action="append", help="juiz (repita para o segundo); ver a lista acima")
    ap.add_argument("--pareceres", help="pasta com parecer-N.json (respostas do modo manual)")
    ap.add_argument("--saida")
    ap.add_argument("--regras")
    ap.add_argument("--semente", type=int, help="semente do sorteio (para repetir uma prova)")
    a = ap.parse_args()
    for v in (a.anterior, a.novo):
        if not Path(v).exists():
            print(f"vídeo não encontrado: {v}", file=sys.stderr)
            sys.exit(2)
    lim, regras_path = rh.carregar_limites(a.regras)
    regras_txt = Path(regras_path).read_text(encoding="utf-8") if regras_path else "(regras/RITMO-HUMANO.md não achado)"
    juizes = a.juiz or [j for j in os.environ.get("REVISOR_JUIZES", "").split(",") if j] or lim.get("revisor", {}).get("juizes") \
        or ["openrouter:anthropic/claude-sonnet-4.5", "openrouter:google/gemini-2.5-pro"]
    if a.pareceres:
        juizes = ["manual"]
    if len(juizes) == 1 and juizes[0] not in ("manual",):
        juizes = juizes * 2
    saida = Path(a.saida) if a.saida else Path(a.novo).resolve().parent / "revisao-cega"
    saida.mkdir(parents=True, exist_ok=True)
    n_quadros = int(lim.get("revisor", {}).get("quadros_por_video", 24))

    print("  medindo as duas versões...")
    med = {"anterior": medir_versao(a.anterior, a.tempo_anterior, a.falas_anterior, lim),
           "novo": medir_versao(a.novo, a.tempo_novo, a.falas_novo, lim)}
    # folhas com nome neutro: o juiz nunca vê "anterior" ou "novo", nem o nome do arquivo
    if a.semente is None:  # o modo manual roda duas vezes (pacote e respostas): a semente fica guardada no segredo
        seg = saida / "segredo.json"
        a.semente = json.loads(seg.read_text())["semente"] if a.pareceres and seg.exists() else random.SystemRandom().randint(1, 10**6)
    rnd = random.Random(a.semente)
    neutro = {"anterior": f"v{rnd.randint(100, 999)}", "novo": None}
    neutro["novo"] = f"v{rnd.choice([x for x in range(100, 1000) if f'v{x}' != neutro['anterior']])}"
    imgs = {p: folhas(Path(v), saida / "folhas", n_quadros, neutro[p]) for p, v in (("anterior", a.anterior), ("novo", a.novo))}

    # sorteio das ordens: cada juiz vê as duas; a primeira ordem de cada juiz é sorteada
    planos = []
    for j in (juizes if juizes != ["manual"] else ["manual", "manual"]):
        primeiro = rnd.choice(["anterior", "novo"])
        segundo = "novo" if primeiro == "anterior" else "anterior"
        for x in (primeiro, segundo):
            planos.append((j, [("X", x), ("Y", "novo" if x == "anterior" else "anterior")]))

    pareceres, erros = [], []
    pacote = saida / "pacote"
    for n, (juiz, ordem) in enumerate(planos, 1):
        prompt = montar_prompt(regras_txt, ordem, med, imgs)
        imagens = [p for _, papel in ordem for p, _ in imgs[papel]]
        if juiz == "manual":
            d = pacote / f"parecer-{n}"
            d.mkdir(parents=True, exist_ok=True)
            (d / "prompt.md").write_text(prompt, encoding="utf-8")
            for k, img in enumerate(imagens, 1):
                (d / f"imagem-{k:02d}.jpg").write_bytes(Path(img).read_bytes())
            resp_f = Path(a.pareceres) / f"parecer-{n}.json" if a.pareceres else None
            if not resp_f or not resp_f.exists():
                continue
            texto = resp_f.read_text(encoding="utf-8")
        elif juiz == "medidas":
            texto = juiz_medidas(ordem, med)
        else:
            print(f"  parecer {n}: {juiz}")
            try:
                texto = chamar_juiz(juiz, prompt, imagens)
            except RuntimeError as e:
                erros.append(f"parecer {n} ({juiz}): {e}")
                continue
        try:
            pareceres.append({"n": n, "juiz": juiz, "ordem": ordem, "resposta": ler_json(texto)})
        except (ValueError, json.JSONDecodeError) as e:
            erros.append(f"parecer {n} ({juiz}): resposta sem JSON válido ({e})")
            (saida / f"resposta-invalida-{n}.txt").write_text(texto, encoding="utf-8")

    segredo = {neutro[p]: p for p in neutro}
    if juizes == ["manual"] and not pareceres:
        (pacote / "LEIA-ME.md").write_text(
            "# Pacote da revisão cega\n\nCada pasta `parecer-N` tem um `prompt.md` e as imagens na ordem. Cole o prompt e as "
            "imagens numa IA (use duas IAs de famílias diferentes: pareceres 1 e 2 para a primeira, 3 e 4 para a segunda, em "
            "conversas separadas) e salve a resposta JSON como `parecer-N.json` nesta pasta. Depois rode de novo com "
            f"`--pareceres {pacote}` (a semente do sorteio fica em `segredo.json`, fora desta pasta).\n", encoding="utf-8")
        (saida / "segredo.json").write_text(json.dumps({"semente": a.semente, "rotulos": segredo}, indent=1), encoding="utf-8")
        print(f"  pacote para os juízes em {pacote} (4 pareceres). Para decidir: a mesma linha com --pareceres {pacote}")
        sys.exit(0)
    if erros:
        print("  juízes com problema:\n   " + "\n   ".join(erros))
    if len(pareceres) < 2:
        print("  pareceres insuficientes para decidir (mínimo 2).", file=sys.stderr)
        sys.exit(2)

    dec = decidir(pareceres, med, lim)
    rel = {"data": time.strftime("%Y-%m-%d %H:%M"), "anterior": a.anterior, "novo": a.novo, "juizes": sorted(set(juizes)),
           "versao_regras": lim.get("versao"), "rotulos_das_folhas": segredo, "erros_de_juiz": erros,
           "medidas": {p: {k: v for k, v in m.items() if k != "falas"} for p, m in med.items()},
           "pareceres": pareceres, "decisao": dec}
    (saida / "relatorio.json").write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    (saida / "RELATORIO.md").write_text(relatorio_md(rel), encoding="utf-8")
    print(f"\n  REVISÃO CEGA: {dec['veredito']} (nova {dec['votos']['novo']}, anterior {dec['votos']['anterior']}, "
          f"empate {dec['votos']['empate']})")
    for aj in dec["ajustes"]:
        for c in aj["casos"]:
            print(f"  AJUSTE {aj['regra']} ({aj['origem']}): {c['descricao'][:160]}")
    for aj in dec["a_conferir"]:
        print(f"  conferir {aj['regra']}: {aj['casos'][0]['descricao'][:120]}")
    print(f"  {'APROVADO: nenhum ajuste pedido' if dec['aprovado'] else 'AJUSTES PEDIDOS'}  ->  {saida / 'RELATORIO.md'}")
    sys.exit(0 if dec["aprovado"] else 1)


if __name__ == "__main__":
    main()
