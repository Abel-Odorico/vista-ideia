"""O contrato de renderização: o corpo do slide vira um documento do tamanho exato.

Mesma ideia do wrapSlideHtml() do Open Carrusel (MIT): uma função só embrulha o
slide, e o que se vê no navegador é o que vira PNG. Aqui as fontes e imagens vão
embutidas (data URI), então o HTML abre sozinho, sem servidor e sem internet.
"""
import base64, io, os
from dataclasses import dataclass, field
from PIL import Image, ImageOps

FORMATOS = {"1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}
PESOS = {"Light": 300, "Regular": 400, "Medium": 500, "SemiBold": 600}


def _hex(c):
    if isinstance(c, (list, tuple)):
        return "#%02X%02X%02X" % tuple(c)
    return c


def _rgb(c):
    c = _hex(c).lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def data_uri(dados, mime):
    return f"data:{mime};base64,{base64.b64encode(dados).decode()}"


def foto_uri(caminho, lado_max=1600, qualidade=86):
    """Foto com a orientação do EXIF corrigida, reduzida e embutida em JPEG."""
    im = ImageOps.exif_transpose(Image.open(caminho)).convert("RGB")
    im.thumbnail((lado_max, lado_max), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=qualidade)
    return data_uri(buf.getvalue(), "image/jpeg")


def mascara_uri(caminho, cor):
    """Máscara em tons de cinza (mark.png, word.png) pintada numa cor da marca."""
    m = Image.open(caminho).convert("L")
    im = Image.new("RGBA", m.size, _rgb(cor) + (0,)); im.putalpha(m)
    buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
    return data_uri(buf.getvalue(), "image/png")


@dataclass
class Marca:
    raiz: str = "."
    handle: str = "@vistaideia"
    navy: str = "#0C1B36"
    creme: str = "#F4EFE4"
    kraft: str = "#B8936A"
    mark: str = "assets/logo/mark.png"
    word: str = "assets/logo/word.png"
    fontes: str = "assets/fonts"
    _cache: dict = field(default_factory=dict, repr=False)

    @classmethod
    def do_projeto(cls, proj, raiz="."):
        cfg = {k: (_hex(v) if k in ("navy", "creme", "kraft") else v)
               for k, v in (proj.get("marca") or {}).items()}
        return cls(raiz=raiz, **cfg)

    def _p(self, rel):
        return os.path.join(self.raiz, rel)

    def logo(self, cor, qual="mark"):
        chave = (qual, cor)
        if chave not in self._cache:
            self._cache[chave] = mascara_uri(self._p(getattr(self, qual)), cor)
        return self._cache[chave]

    def foto(self, rel):
        if rel not in self._cache:
            self._cache[rel] = foto_uri(self._p(rel))
        return self._cache[rel]

    def css_fontes(self):
        if "fontes" not in self._cache:
            regras = []
            for nome, peso in PESOS.items():
                arq = self._p(f"{self.fontes}/Montserrat-{nome}.ttf")
                if not os.path.isfile(arq):
                    raise FileNotFoundError(f"{arq} não existe. Rode antes: ./scripts/setup_fonts.sh")
                with open(arq, "rb") as f:
                    uri = data_uri(f.read(), "font/ttf")
                regras.append("@font-face{font-family:'Montserrat';font-weight:%d;"
                              "src:url(%s) format('truetype');}" % (peso, uri))
            self._cache["fontes"] = "\n".join(regras)
        return self._cache["fontes"]


def embrulhar(corpo, formato="4:5", css_fontes="", extra_head=""):
    """Corpo do slide → documento HTML completo em largura x altura exatas."""
    w, h = FORMATOS[formato]
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width={w}, initial-scale=1">
<style>{css_fontes}</style>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
body{{-webkit-font-smoothing:antialiased;text-rendering:geometricPrecision}}
</style>
{extra_head}
</head>
<body>
{corpo}
</body>
</html>"""
