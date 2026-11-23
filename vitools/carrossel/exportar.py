"""Exporta o carrossel: HTML de cada slide, conferência de transbordo, PNG e folha.

O PNG sai do Chrome sem tela (o mesmo que o Open Carrusel faz com Puppeteer),
chamado pela linha de comando: não precisa de Node nem de biblioteca nova.
"""
import os, platform, re, shutil, subprocess, tempfile
from PIL import Image, ImageDraw
from .pagina import FORMATOS, Marca, embrulhar
from .layouts import montar_slide

# Roda só na conferência (nunca vai para o PNG): marca no <body> os blocos de
# texto que passaram da caixa.
CHECAGEM = """<script>
document.fonts.ready.then(function(){
  var ruins=[];
  var corpo=document.querySelector('.corpo');
  if(corpo.scrollHeight>corpo.clientHeight+2) ruins.push('corpo (texto demais para a altura)');
  document.querySelectorAll('.t').forEach(function(el){
    if(el.scrollWidth>el.clientWidth+2) ruins.push((el.dataset.nome||'texto')+' (palavra larga demais)');
  });
  var c=corpo.getBoundingClientRect();
  document.querySelectorAll('.corpo .t').forEach(function(el){
    var r=el.getBoundingClientRect();
    if(r.width&&(r.bottom>c.bottom+1||r.right>c.right+1)) ruins.push((el.dataset.nome||'texto')+' fora do corpo');
  });
  document.body.setAttribute('data-transbordo',ruins.join(','));
});
</script>"""


def achar_chrome():
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    for nome in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        p = shutil.which(nome)
        if p:
            return p
    candidatos = {
        "Darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Chromium.app/Contents/MacOS/Chromium"],
        "Windows": [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"],
    }.get(platform.system(), []) + ["/opt/pw-browsers/chromium"]
    for p in candidatos:
        if os.path.isfile(p):
            return p
    raise FileNotFoundError("Chrome não encontrado. Instale o Google Chrome ou defina CHROME_PATH.")


def _chrome(chrome, w, h, *extra, tmp):
    return [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=1", "--default-background-color=00000000",
            f"--user-data-dir={tmp}/perfil", f"--window-size={w},{h}",
            "--virtual-time-budget=4000", *extra]


def foto_do_html(chrome, html_path, png_path, w, h, tmp):
    subprocess.run(_chrome(chrome, w, h, f"--screenshot={png_path}", "file://" + os.path.abspath(html_path), tmp=tmp),
                   check=True, capture_output=True, timeout=90)
    im = Image.open(png_path)
    if im.size != (w, h):  # versões antigas do Chrome somam a barra; corta no tamanho certo
        im.crop((0, 0, w, h)).save(png_path)
    return png_path


def transbordo(chrome, html_path, w, h, tmp):
    r = subprocess.run(_chrome(chrome, w, h, "--dump-dom", "file://" + os.path.abspath(html_path), tmp=tmp),
                       capture_output=True, text=True, timeout=90)
    m = re.search(r'data-transbordo="([^"]*)"', r.stdout)
    if m is None:
        return ["não deu para conferir (o Chrome não devolveu o DOM)"]
    return [x for x in m.group(1).split(",") if x]


def zonas(png_path, saida, capa=False):
    """Mapa aproximado do que o app esconde. Na capa: o recorte 3:4 da grade do
    perfil (vermelho). Em 9:16: as faixas de cima e de baixo dos stories (azul).
    O verde é a margem do grid (86 px): texto importante fica dentro dele."""
    im = Image.open(png_path).convert("RGBA")
    w, h = im.size
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    vermelho, azul = (230, 40, 40, 80), (40, 110, 255, 70)
    if capa:
        if w / h > 3 / 4:   # 1:1 e 4:5 perdem as laterais
            f = round((w - h * 3 / 4) / 2)
            d.rectangle([0, 0, f, h], fill=vermelho); d.rectangle([w - f, 0, w, h], fill=vermelho)
        elif w / h < 3 / 4:  # 9:16 perde em cima e embaixo
            f = round((h - w * 4 / 3) / 2)
            d.rectangle([0, 0, w, f], fill=vermelho); d.rectangle([0, h - f, w, h], fill=vermelho)
    if h / w > 1.6:
        d.rectangle([0, 0, w, int(h * .14)], fill=azul)
        d.rectangle([0, int(h * .80), w, h], fill=azul)
    d.rectangle([86, 86, w - 86, h - 86], outline=(30, 170, 80, 230), width=3)
    Image.alpha_composite(im, lay).convert("RGB").save(saida, quality=90)
    return saida


def grade(pngs, saida, colunas=5, largura=360):
    ims = [Image.open(p).convert("RGB") for p in pngs]
    a = int(ims[0].height * largura / ims[0].width)
    linhas = -(-len(ims) // colunas)
    esp = 16
    g = Image.new("RGB", (colunas * (largura + esp) + esp, linhas * (a + esp) + esp), (205, 200, 190))
    for i, im in enumerate(ims):
        g.paste(im.resize((largura, a), Image.LANCZOS),
                (esp + (i % colunas) * (largura + esp), esp + (i // colunas) * (a + esp)))
    g.save(saida, quality=88)
    return saida


def exportar_carrossel(proj, raiz, saida, com_zonas=False, so_html=False, log=print):
    """Gera saida/html/slide-NN.html, saida/slide-NN.png e saida/grade.jpg.
    Devolve {numero_do_slide: [blocos que transbordaram]}."""
    formato = proj.get("formato", "4:5")
    w, h = FORMATOS[formato]
    marca = Marca.do_projeto(proj, raiz)
    css = marca.css_fontes()
    slides = proj["slides"]
    os.makedirs(f"{saida}/html", exist_ok=True)
    htmls = []
    for n, s in enumerate(slides, 1):
        corpo = montar_slide(marca, s, n, len(slides), formato)
        p = f"{saida}/html/slide-{n:02d}.html"
        with open(p, "w", encoding="utf-8") as f:
            f.write(embrulhar(corpo, formato, css))
        htmls.append((p, corpo))
    if so_html:
        return {}
    chrome = achar_chrome()
    problemas, pngs = {}, []
    with tempfile.TemporaryDirectory() as tmp:
        for n, (p, corpo) in enumerate(htmls, 1):
            chk = f"{tmp}/chk-{n:02d}.html"
            with open(chk, "w", encoding="utf-8") as f:
                f.write(embrulhar(corpo, formato, css, extra_head=CHECAGEM))
            ruins = transbordo(chrome, chk, w, h, tmp)
            if ruins:
                problemas[n] = ruins
            png = foto_do_html(chrome, p, f"{saida}/slide-{n:02d}.png", w, h, tmp)
            pngs.append(png)
            log(f"  slide {n:02d} ({slides[n - 1]['tipo']}) ✔" + (f"  ⚠ transbordo: {', '.join(ruins)}" if ruins else ""))
    grade(pngs, f"{saida}/grade.jpg")
    if com_zonas:
        os.makedirs(f"{saida}/zonas", exist_ok=True)
        for n, png in enumerate(pngs, 1):
            zonas(png, f"{saida}/zonas/slide-{n:02d}.jpg", capa=(n == 1))
    return problemas
