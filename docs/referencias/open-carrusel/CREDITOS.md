# Créditos: Open Carrusel

O gerador de carrossel (`carrossel.py` e `vitools/carrossel/`) se inspira na arquitetura do
**Open Carrusel**, de **Enrique Rocha (@soyenriquerocha)** e colaboradores
([github.com/Hainrixz/open-carrusel](https://github.com/Hainrixz/open-carrusel), [tododeia.com](https://www.tododeia.com)),
publicado sob a licença **MIT**.

## O que veio de lá (ideias, reescritas em Python)
| Open Carrusel | Vista Ideia |
|---|---|
| Slide guardado como HTML de corpo, sem `<html>`/`<head>` | `layouts.montar_slide()` devolve só o corpo |
| `wrapSlideHtml()`: uma função única embrulha o slide no tamanho exato, a mesma para prévia e exportação | `pagina.embrulhar()` |
| Fontes e imagens embutidas (base64) antes da foto, para o PNG não depender de rede | `Marca.css_fontes()`, `Marca.foto()` |
| Puppeteer tira a foto de cada slide em 1080 × 1080, 1350 ou 1920 | Chrome sem tela pela linha de comando (`exportar.foto_do_html`) |
| Sobreposição de zona segura no editor | `--zonas` (recorte 3:4 da grade, faixas dos stories, margem do grid) |
| Máximo de 10 slides, formatos 1:1, 4:5 e 9:16 | `regras.conferir()` |

## O que não veio
O editor em Next.js, o chat com o Claude dentro do app, o banco em JSON, os modelos e a
exportação em ZIP. Aqui o roteiro do carrossel é um JSON escrito à mão (ou pelo bot roteirista
de `docs/grokbot/`), e o visual segue o padrão fixo de `docs/carrossel-editorial.md`.
Nenhum arquivo foi copiado; o código foi reescrito do zero.

## Aviso do projeto original
> open-carrusel — versão de Enrique Rocha (@soyenriquerocha). tododeia.com · github.com/Hainrixz
> Licença: MIT. Se redistribuir, modificar ou publicar uma versão derivada deste projeto,
> conserve este aviso, o aviso de copyright e o crédito visível ao autor original.

## Licença original (MIT)
```
MIT License

Copyright (c) 2026 Enrique Rocha (@soyenriquerocha)
Copyright (c) 2026 Open Carrusel Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
