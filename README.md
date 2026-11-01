# Vista Ideia — Reels de Unboxing

Vídeo vertical (1080×1920, 30fps, ~19s) mostrando a evolução do pedido: da caixa fechada à peça vestida.

## Roteiro
| Tempo | Cena | Legenda |
|---|---|---|
| 0–2s | Intro creme com reveal do símbolo **Vi** | UNBOXING |
| 2–6s | Caixa no escuro → flash → caixa na luz | 01 · A chegada |
| 6–8,5s | Caixa aberta, pan do cartão à tag | 02 · O cuidado |
| 8,5–10,5s | Close no rolinho | 03 · Os detalhes |
| 10,5–13s | Camiseta | 04 · A peça |
| 13–16s | Cliente usando a peça | 05 · Vestida de verdade |
| 16–19s | Outro navy com logo | Obrigado por escolher a Vista Ideia. |

## Identidade
- Navy `#0C1B36` · Creme `#F4EFE4`
- Tipografia: Montserrat

## Estrutura
```
assets/fotos/   fotos do pedido
assets/logo/    brand board + máscaras do símbolo (mark.png) e assinatura (word.png)
scripts/        render.py (gera o vídeo) e setup_fonts.sh
output/         vídeo final e capa
```

## Como renderizar
Requer Python 3.10+ e ffmpeg.
```bash
pip install -r requirements.txt
./scripts/setup_fonts.sh
python3 scripts/render.py
```
Para ajustar, edite no `render.py`: `TL` (tempos e cenas), `CAPS` (legendas) e `shots` (zoom/enquadramento de cada foto).

## Observações
- O vídeo é exportado **sem áudio**; a música entra direto no Instagram.
- O repositório é público e contém foto de cliente usada com autorização de imagem.
