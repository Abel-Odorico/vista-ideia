"""Regras do carrossel editorial (docs/carrossel-editorial.md), conferidas antes de renderizar."""
import os, re
from dataclasses import dataclass

LIMITES = {"chapeu": 3, "titulo": 9, "apoio": 25, "texto": 60, "frase": 25,
           "legenda": 9, "pergunta": 12}
MAX_SLIDES = 10
# Pictogramas, símbolos e bandeiras: o padrão é "sem emoji" no slide.
EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿⬀-⯿️]")
CAMPOS_TEXTO = ("chapeu", "titulo", "apoio", "texto", "frase", "legenda",
                "pergunta", "numero", "fonte")
OBRIGATORIOS = {
    "capa": ["titulo", "foto"], "abertura": ["titulo", "texto"], "dado": ["numero", "legenda"],
    "contexto": ["titulo", "foto"], "citacao": ["frase", "fonte"],
    "comparativo": ["esquerda", "direita"], "detalhe": ["foto", "frase"],
    "lista": ["titulo", "itens"], "sintese": ["frase"], "fecho": ["pergunta"],
}


@dataclass
class Problema:
    slide: int          # 1-based; 0 = carrossel inteiro
    campo: str
    msg: str
    grave: bool = True  # grave impede a renderização (salvo --forcar)

    def __str__(self):
        onde = f"slide {self.slide:02d}" if self.slide else "carrossel"
        nivel = "ERRO" if self.grave else "aviso"
        return f"[{nivel}] {onde} · {self.campo}: {self.msg}"


def palavras(s):
    return len(str(s).split())


def _textos(slide):
    for k in CAMPOS_TEXTO:
        if k in slide:
            yield k, str(slide[k])
    for lado in ("esquerda", "direita"):
        for k, v in (slide.get(lado) or {}).items():
            yield f"{lado}.{k}", str(v)
    for i, it in enumerate(slide.get("itens") or [], 1):
        yield f"itens[{i}]", str(it)


def conferir(proj, raiz="."):
    """Devolve a lista de problemas do projeto (vazia = pode renderizar)."""
    from .layouts import TIPOS
    from .pagina import FORMATOS
    out = []
    slides = proj.get("slides") or []
    if not slides:
        out.append(Problema(0, "slides", "nenhum slide"))
    if len(slides) > MAX_SLIDES:
        out.append(Problema(0, "slides", f"{len(slides)} slides; o Instagram aceita até {MAX_SLIDES}"))
    if proj.get("formato", "4:5") not in FORMATOS:
        out.append(Problema(0, "formato", f"use um de {', '.join(FORMATOS)}"))
    for n, s in enumerate(slides, 1):
        tipo = s.get("tipo")
        if tipo not in TIPOS:
            out.append(Problema(n, "tipo", f"'{tipo}' não existe; use {', '.join(TIPOS)}"))
            continue
        for campo in OBRIGATORIOS[tipo]:
            if not s.get(campo):
                extra = " (nunca inventar: sem fonte real, troque por 'dado')" if campo == "fonte" else ""
                out.append(Problema(n, campo, f"obrigatório em '{tipo}'{extra}"))
        for campo, txt in _textos(s):
            base = campo.split(".")[-1].split("[")[0]
            lim = LIMITES.get(base)
            if campo.startswith("itens"):
                lim = 8
            if lim and palavras(txt) > lim:
                out.append(Problema(n, campo, f"{palavras(txt)} palavras; o limite é {lim}"))
            if EMOJI.search(txt):
                out.append(Problema(n, campo, "sem emoji dentro do slide"))
            if "  " in txt or txt != txt.strip():
                out.append(Problema(n, campo, "espaço sobrando", grave=False))
        if tipo == "lista" and len(s.get("itens") or []) != 3:
            out.append(Problema(n, "itens", "a lista do padrão tem 3 itens", grave=False))
        if s.get("foto") and not os.path.isfile(os.path.join(raiz, s["foto"])):
            out.append(Problema(n, "foto", f"arquivo não encontrado: {s['foto']}"))
    if slides and slides[0].get("tipo") != "capa":
        out.append(Problema(1, "tipo", "o primeiro slide costuma ser a capa", grave=False))
    if slides and slides[-1].get("tipo") != "fecho":
        out.append(Problema(len(slides), "tipo", "o último slide costuma ser o fecho", grave=False))
    return out
