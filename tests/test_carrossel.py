"""Testes do carrossel: python3 -m pytest tests/  (ou python3 -m unittest)."""
import copy, json, os, re, shutil, tempfile, unittest
from PIL import Image
from vitools.carrossel import conferir, embrulhar, montar_slide, Marca, TIPOS
from vitools.carrossel.exportar import achar_chrome, exportar_carrossel, zonas

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXEMPLO = os.path.join(RAIZ, "projects", "carrossel-unboxing.json")
TEM_FONTES = os.path.isfile(os.path.join(RAIZ, "assets/fonts/Montserrat-Light.ttf"))


def proj():
    with open(EXEMPLO, encoding="utf-8") as f:
        return json.load(f)


def tem_chrome():
    try:
        achar_chrome(); return True
    except FileNotFoundError:
        return False


class Regras(unittest.TestCase):
    def test_exemplo_passa(self):
        self.assertEqual([str(p) for p in conferir(proj(), RAIZ)], [])

    def test_exemplo_usa_os_10_tipos(self):
        self.assertEqual([s["tipo"] for s in proj()["slides"]], list(TIPOS))

    def test_limite_de_palavras(self):
        p = proj(); p["slides"][0]["titulo"] = "um dois três quatro cinco seis sete oito nove dez"
        probs = conferir(p, RAIZ)
        self.assertTrue(any(x.campo == "titulo" and x.grave and "10 palavras" in x.msg for x in probs))

    def test_chapeu_ate_3_palavras(self):
        p = proj(); p["slides"][2]["chapeu"] = "quatro palavras de chapéu"
        self.assertTrue(any(x.campo == "chapeu" for x in conferir(p, RAIZ)))

    def test_emoji_e_erro(self):
        p = proj(); p["slides"][8]["frase"] = "Boas escolhas ✨"
        self.assertTrue(any("emoji" in x.msg for x in conferir(p, RAIZ)))

    def test_citacao_sem_fonte_nao_passa(self):
        p = proj(); del p["slides"][4]["fonte"]
        probs = conferir(p, RAIZ)
        self.assertTrue(any(x.campo == "fonte" and "nunca inventar" in x.msg for x in probs))

    def test_mais_de_10_slides(self):
        p = proj(); p["slides"].append(copy.deepcopy(p["slides"][8]))
        self.assertTrue(any(x.slide == 0 and "até 10" in x.msg for x in conferir(p, RAIZ)))

    def test_foto_inexistente_e_tipo_errado(self):
        p = proj(); p["slides"][0]["foto"] = "assets/fotos/nao-existe.jpg"; p["slides"][1]["tipo"] = "poster"
        campos = {x.campo for x in conferir(p, RAIZ)}
        self.assertTrue({"foto", "tipo"} <= campos)

    def test_ordem_fora_do_padrao_so_avisa(self):
        p = proj(); p["slides"].reverse()
        probs = conferir(p, RAIZ)
        self.assertTrue(probs and not any(x.grave for x in probs))


class Contrato(unittest.TestCase):
    def test_embrulhar_tamanho_exato(self):
        for fmt, (w, h) in {"1:1": (1080, 1080), "4:5": (1080, 1350), "9:16": (1080, 1920)}.items():
            doc = embrulhar("<p>oi</p>", fmt)
            self.assertIn(f"width:{w}px;height:{h}px;overflow:hidden", doc)
            self.assertTrue(doc.startswith("<!DOCTYPE html>"))

    @unittest.skipUnless(TEM_FONTES, "rode ./scripts/setup_fonts.sh")
    def test_slide_autossuficiente_e_escapado(self):
        p = proj(); m = Marca.do_projeto(p, RAIZ)
        s = dict(p["slides"][8], frase='<script>alert(1)</script> & "aspas"')
        corpo = montar_slide(m, s, 9, 10)
        self.assertNotIn("<script>", corpo)
        self.assertIn("&lt;script&gt;", corpo)
        self.assertIn("09/10", corpo)
        doc = embrulhar(corpo, "4:5", m.css_fontes())
        self.assertNotRegex(doc, r'src="(?!data:)')            # nada de arquivo externo
        self.assertNotIn("http", re.sub(r"data:[^)\"]+", "", doc))

    @unittest.skipUnless(TEM_FONTES, "rode ./scripts/setup_fonts.sh")
    def test_sintese_e_invertida(self):
        p = proj(); m = Marca.do_projeto(p, RAIZ)
        self.assertIn('class="s inv"', montar_slide(m, p["slides"][8], 9, 10))
        self.assertIn('class="s"', montar_slide(m, p["slides"][0], 1, 10))


class Zonas(unittest.TestCase):
    def test_capa_4x5_perde_as_laterais(self):
        with tempfile.TemporaryDirectory() as d:
            Image.new("RGB", (1080, 1350), (255, 255, 255)).save(f"{d}/a.png")
            out = Image.open(zonas(f"{d}/a.png", f"{d}/z.jpg", capa=True)).convert("RGB")
            r, g, b = out.getpixel((10, 675))
            self.assertGreater(r, g + 30)              # lateral marcada em vermelho
            self.assertEqual(out.getpixel((540, 675)), (255, 255, 255))


@unittest.skipUnless(TEM_FONTES and tem_chrome(), "precisa das fontes e do Chrome")
class Exportacao(unittest.TestCase):
    def test_png_no_tamanho_exato_e_detecta_transbordo(self):
        p = proj()
        longo = "Uma frase propositalmente comprida " * 12
        p["slides"] = [p["slides"][0], dict(p["slides"][8], frase=longo.strip())]
        with tempfile.TemporaryDirectory() as d:
            transb = exportar_carrossel(p, RAIZ, d, com_zonas=True, log=lambda *_: None)
            for n in (1, 2):
                self.assertEqual(Image.open(f"{d}/slide-{n:02d}.png").size, (1080, 1350))
            self.assertTrue(os.path.isfile(f"{d}/grade.jpg"))
            self.assertTrue(os.path.isfile(f"{d}/zonas/slide-01.jpg"))
            self.assertNotIn(1, transb)
            self.assertIn(2, transb)
            # fundo da síntese é navy de verdade
            self.assertEqual(Image.open(f"{d}/slide-02.png").convert("RGB").getpixel((20, 675)), (12, 27, 54))


if __name__ == "__main__":
    unittest.main()
