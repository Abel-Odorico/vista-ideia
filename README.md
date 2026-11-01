# Vista Ideia — Reels de Unboxing + vitools

Vídeo vertical (1080×1920, 30fps, ~19s) mostrando a evolução do pedido: da caixa fechada à peça vestida,
e o **vitools**, kit em Python que gera esse tipo de vídeo a partir de fotos, logo e um arquivo JSON.

![preview](output/preview_unboxing.jpg)

## 🎬 Roteiro
| Tempo | Cena | Legenda |
|---|---|---|
| 0–2s | Intro creme com reveal do símbolo **Vi** | UNBOXING |
| 2–6s | Caixa no escuro → flash → caixa na luz | 01 · A chegada |
| 6–8,5s | Caixa aberta, pan do cartão à tag | 02 · O cuidado |
| 8,5–10,5s | Close no rolinho | 03 · Os detalhes |
| 10,5–13s | Camiseta | 04 · A peça |
| 13–16s | Cliente usando a peça | 05 · Vestida de verdade |
| 16–19s | Outro navy com logo | Obrigado por escolher a Vista Ideia. |

**Identidade:** Navy `#0C1B36` · Creme `#F4EFE4` · Montserrat

---

## 🧰 vitools

### Instalação
Requer Python 3.10+ e **ffmpeg**.
```bash
pip install -r requirements.txt
./scripts/setup_fonts.sh
```

### Renderizar
```bash
python3 render.py projects/unboxing.json            # gera o MP4 + capa
python3 render.py projects/unboxing.json --preview  # + folha de contato com quadros-chave
```

### Ferramentas
| Comando | O que faz |
|---|---|
| `render.py <projeto.json>` | Renderiza o vídeo a partir do JSON |
| `tools/extract_logo.py <arte> --box x0 y0 x1 y1` | Recorta a logo de uma arte e gera as máscaras `mark.png` (símbolo) e `word.png` (assinatura), recoloríveis |
| `tools/contact_sheet.py <video.mp4> -n 8` | Gera uma folha de contato para revisar qualquer vídeo |

### Recursos do motor
- **Ken Burns** com zoom e pan em subpixel, sem nunca mostrar borda vazia
- **Crossfade** entre fotos e **flash** quente em pontos escolhidos
- **Intro e outro** com reveal do símbolo (wipe de baixo pra cima) e assinatura com tracking animado, entrando em cortina
- **Legendas em chip** com contador `01 / 05`, posição configurável por legenda
- **Acabamento:** grão de filme, vinheta e gradiente inferior
- **Capa** exportada automaticamente no instante configurado

### Criar um vídeo novo
1. Coloque as fotos em `assets/fotos/`
2. Duplique `projects/unboxing.json` e edite:

| Campo | Para que serve |
|---|---|
| `brand.primary` / `secondary` | Cores da marca (RGB) |
| `intro.label` / `outro.lines` | Textos das cartelas |
| `shots[]` | `image`, `start`/`end` (s), `zoom` [início, fim], `center` [[x,y] início, [x,y] fim] em pixels da foto original |
| `captions[]` | `num`, `text`, `start`/`end` e `y` opcional (padrão 1290; use ~330 para o topo) |
| `flashes[]` | `at` (s), `width`, `strength` |
| `fx` | Intensidade de `grain`, `vignette` e `bottom_gradient` |

> 💡 Shots consecutivos se sobrepõem ~0,3s; é nessa sobreposição que o crossfade acontece.

Para outra marca, rode `tools/extract_logo.py` na arte dela e aponte `brand.mark`/`brand.word` para os PNGs gerados.

## 📁 Estrutura
```
render.py            CLI principal
vitools/             motor (core, shot, brand, fx, engine)
tools/               extract_logo.py, contact_sheet.py
projects/            projetos de vídeo em JSON
assets/fotos/        fotos do pedido
assets/logo/         brand board + máscaras da logo
scripts/             setup_fonts.sh
output/              vídeo, capa e preview
```

## Observações
- O vídeo é exportado **sem áudio**; a música entra direto no Instagram.
- O repositório é público e contém foto de cliente usada com autorização de imagem.
