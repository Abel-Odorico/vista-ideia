"""Os 10 tipos de slide do padrão editorial, no grid fixo da revista.

Grid igual em todos: margem de 86 px; fio no topo com chapéu à esquerda e fólio à
direita; fio no rodapé com o @ à esquerda e o símbolo Vi à direita. O kraft é o
destaque e aparece em no máximo um elemento por slide.
"""
from html import escape
from .pagina import FORMATOS

M = 86  # margem (~8% de 1080)


def e(s):
    return escape(str(s or ""))


def _css(m, w, h):
    return f"""
<style>
.s{{position:relative;width:{w}px;height:{h}px;background:{m.creme};color:{m.navy};
  font-family:'Montserrat',sans-serif;font-weight:300;overflow:hidden}}
.s.inv{{background:{m.navy};color:{m.creme}}}
.topo{{position:absolute;left:{M}px;right:{M}px;top:{M - 20}px;height:46px;border-bottom:1.5px solid currentColor;
  display:flex;justify-content:space-between;align-items:flex-start;font-size:20px;font-weight:500;
  letter-spacing:.3em;text-transform:uppercase}}
.topo .folio{{letter-spacing:.12em;font-weight:400}}
.rodape{{position:absolute;left:{M}px;right:{M}px;bottom:{M - 20}px;height:62px;border-top:1.5px solid currentColor;
  display:flex;justify-content:space-between;align-items:flex-end;font-size:21px;font-weight:400;letter-spacing:.06em}}
.rodape img{{height:36px;display:block}}
.corpo{{position:absolute;left:{M}px;right:{M}px;top:{M + 62}px;bottom:{M + 70}px;overflow:hidden;
  display:flex;flex-direction:column}}
.kraft{{color:{m.kraft}}}
.fio-k{{width:72px;height:4px;background:{m.kraft}}}
.foto{{display:block;width:100%;object-fit:cover;min-height:0}}
.t{{overflow-wrap:break-word}}
.mancha{{font-weight:500;letter-spacing:-.015em;line-height:1.06}}
.apoio{{font-size:27px;line-height:1.45;font-weight:300}}
.rot{{font-size:21px;font-weight:500;letter-spacing:.28em;text-transform:uppercase}}
</style>"""


def _foto(m, s, estilo=""):
    fx, fy = s.get("foco", [50, 50])
    return (f'<img class="foto" alt="" src="{m.foto(s["foto"])}" '
            f'style="object-position:{fx}% {fy}%;{estilo}">')


# ---------- tipos ----------

def capa(m, s):
    return f"""
<h1 class="t mancha" data-nome="titulo" style="font-size:{s.get('tamanho', 82)}px;margin-top:22px">{e(s['titulo'])}</h1>
<div style="display:flex;align-items:center;gap:22px;margin:30px 0 34px">
  <div class="fio-k"></div><p class="t apoio" data-nome="apoio" style="font-size:26px">{e(s.get('apoio'))}</p></div>
{_foto(m, s, 'flex:1 1 0;min-height:320px')}"""


def abertura(m, s):
    return f"""
<h1 class="t mancha" data-nome="titulo" style="font-size:60px;margin:40px 0 56px;max-width:860px">{e(s['titulo'])}</h1>
<p class="t abertura" data-nome="texto" style="column-count:2;column-gap:56px;font-size:31px;line-height:1.55">{e(s['texto'])}</p>
{_foto(m, s, 'flex:1 1 0;min-height:260px;margin-top:56px') if s.get('foto') else ''}
<style>.abertura::first-letter{{float:left;font-size:142px;line-height:.82;font-weight:500;
  color:{m.kraft};margin:6px 16px 0 0}}</style>"""


def dado(m, s):
    return f"""
<div style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <div class="t kraft" data-nome="numero" style="font-size:{s.get('tamanho', 380)}px;line-height:.9;font-weight:300;letter-spacing:-.04em">{e(s['numero'])}</div>
  <h2 class="t mancha" data-nome="legenda" style="font-size:52px;margin:34px 0 26px;max-width:800px">{e(s['legenda'])}</h2>
  <p class="t apoio" data-nome="apoio" style="max-width:760px">{e(s.get('apoio'))}</p>
</div>"""


def contexto(m, s):
    return f"""
<div style="flex:1;display:flex;gap:48px;min-height:0">
  <div style="flex:0 0 58%;display:flex">{_foto(m, s, 'height:100%')}</div>
  <div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:8px">
    <div class="fio-k" style="margin-bottom:30px"></div>
    <h2 class="t mancha" data-nome="titulo" style="font-size:44px;margin-bottom:24px">{e(s['titulo'])}</h2>
    <p class="t apoio" data-nome="apoio" style="font-size:24px">{e(s.get('apoio'))}</p>
  </div>
</div>"""


def citacao(m, s):
    return f"""
<div style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <div class="kraft" style="font-size:260px;line-height:.6;font-weight:500;height:120px">&ldquo;</div>
  <blockquote class="t" data-nome="frase" style="font-size:{s.get('tamanho', 72)}px;line-height:1.18;font-weight:300;letter-spacing:-.01em;margin:30px 0 44px">{e(s['frase'])}</blockquote>
  <p class="t rot" data-nome="fonte">{e(s['fonte'])}</p>
</div>"""


def comparativo(m, s):
    esq, dir_ = s["esquerda"], s["direita"]
    def col(c, cls=""):
        return (f'<div style="flex:1;display:flex;flex-direction:column;gap:34px">'
                f'<p class="t rot {cls}" data-nome="rotulo">{e(c.get("rotulo"))}</p>'
                f'<p class="t" data-nome="texto" style="font-size:46px;line-height:1.25">{e(c.get("texto"))}</p></div>')
    titulo = (f'<h2 class="t mancha" data-nome="titulo" style="font-size:60px;margin:40px 0 0">{e(s["titulo"])}</h2>'
              if s.get("titulo") else "")
    return f"""{titulo}
<div style="flex:1;display:flex;align-items:center">
  <div style="display:flex;gap:64px;width:100%;align-items:stretch">
    {col(esq)}<div style="width:1.5px;background:currentColor;opacity:.5"></div>{col(dir_, 'kraft')}
  </div>
</div>"""


def detalhe(m, s):
    return f"""
{_foto(m, s, 'flex:1 1 0;min-height:400px;margin-top:8px')}
<div style="display:flex;gap:22px;align-items:baseline;margin-top:34px">
  <div class="fio-k" style="flex:0 0 72px;transform:translateY(-10px)"></div>
  <p class="t" data-nome="frase" style="font-size:36px;line-height:1.3;font-weight:300">{e(s['frase'])}</p>
</div>"""


def lista(m, s):
    itens = "".join(
        f'<li style="display:flex;gap:40px;align-items:center;padding:34px 0;'
        f'border-top:1.5px solid rgba(12,27,54,.25)">'
        f'<span class="kraft" style="flex:0 0 150px;font-size:128px;line-height:.85;font-weight:300">{i:02d}</span>'
        f'<span class="t" data-nome="item" style="font-size:38px;line-height:1.25;font-weight:400">{e(t)}</span></li>'
        for i, t in enumerate(s["itens"], 1))
    return f"""
<h2 class="t mancha" data-nome="titulo" style="font-size:60px;margin:40px 0 50px">{e(s['titulo'])}</h2>
<ol style="list-style:none">{itens}</ol>"""


def sintese(m, s):
    return f"""
<div style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <div class="fio-k" style="margin-bottom:56px"></div>
  <p class="t" data-nome="frase" style="font-size:{s.get('tamanho', 76)}px;line-height:1.14;font-weight:300;letter-spacing:-.01em">{e(s['frase'])}</p>
</div>"""


def fecho(m, s):
    return f"""
<div style="flex:1;display:flex;flex-direction:column;justify-content:center">
  <h2 class="t mancha" data-nome="titulo" style="font-size:84px">{e(s.get('titulo') or 'Salve para lembrar.')}</h2>
  <p class="t" data-nome="pergunta" style="font-size:40px;line-height:1.3;margin:44px 0 0;max-width:840px">
    <span style="font-weight:500">Comenta:</span> {e(s['pergunta'])}</p>
  <p class="t kraft" style="font-size:34px;font-weight:500;letter-spacing:.04em;margin-top:56px">{e(m.handle)}</p>
</div>
<div style="display:flex;flex-direction:column;align-items:center;gap:22px;padding-bottom:10px">
  <img alt="Vi" src="{m.logo(m.navy, 'mark')}" style="height:110px">
  <img alt="Vista Ideia" src="{m.logo(m.navy, 'word')}" style="height:26px">
</div>"""


TIPOS = {f.__name__: f for f in (capa, abertura, dado, contexto, citacao, comparativo,
                                 detalhe, lista, sintese, fecho)}
INVERTIDOS = {"sintese"}


def montar_slide(m, s, n, total, formato="4:5"):
    """Corpo HTML de um slide (sem <html>/<head>), já com o grid da revista."""
    w, h = FORMATOS[formato]
    inv = s.get("invertido", s["tipo"] in INVERTIDOS)
    cor_logo = m.creme if inv else m.navy
    chapeu = s.get("chapeu") or ""
    return f"""{_css(m, w, h)}
<main class="s{' inv' if inv else ''}" data-tipo="{s['tipo']}">
  <header class="topo"><span class="t" data-nome="chapeu">{e(chapeu)}</span><span class="folio">{n:02d}/{total:02d}</span></header>
  <section class="corpo" data-nome="corpo">{TIPOS[s['tipo']](m, s)}</section>
  <footer class="rodape"><span>{e(m.handle)}</span><img alt="Vi" src="{m.logo(cor_logo)}"></footer>
</main>"""
