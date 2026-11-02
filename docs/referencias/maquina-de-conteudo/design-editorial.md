# Design editorial: o padrão dos carrosséis

O carrossel tem cara de **revista impressa**: muito respiro, tipografia serifada grande, grid rígido, numeração de página e uma imagem forte por slide. Nada de cara de template de Canva (sem degradê, sem emoji, sem caixas arredondadas coloridas, sem ícone genérico).

## Grid e elementos fixos (iguais nos 10 slides)

- Formato 4:5, 1080 x 1350. Margens largas (cerca de 8% em cada lado).
- **Topo:** fio fino horizontal na largura toda; à esquerda o **chapéu** em caixa alta pequena e espaçada; à direita o **fólio** "0N/10".
- **Rodapé:** fio fino; à esquerda o @ do perfil em caixa alta pequena; à direita a palavra "Edição" + a data (ex.: "Edição 31.10").
- **Tipografia:** títulos em serifada de alto contraste, peso forte, estilo jornal (tipo Didone ou Playfair); textos de apoio em sans-serif limpa e pequena; números grandes em serifada.
- **Imagem:** fotografia editorial ou ilustração com textura de papel, recorte assimétrico em retângulo, sem bordas arredondadas.
- **Cor:** fundo de uma cor só, texto em uma cor, **um** destaque (a cor da marca ou da paleta) usado em no máximo um elemento por slide.

## Paletas

| Nome | Fundo | Texto | Destaque |
|---|---|---|---|
| Jornal | off-white papel #F4F1EA | preto tinta #111111 | vermelho #C8102E |
| Revista Noturna | preto #0E0E0E | branco quente #F2EEE6 | verde neon #3EE6A0 |
| Papel e Tinta | creme #EDE6D6 | marinho #1B2433 | mostarda #D4A017 |
| Galeria | branco #FFFFFF | grafite #222222 | azul cobalto #1F4FD8 |

Padrão: **Jornal**, a não ser que o perfil tenha cor de marca (vira o destaque).

## Mapa dos 10 slides

| Slide | Tipo | Layout |
|---|---|---|
| 01 | Capa | Manchete enorme ocupando metade de cima, imagem forte embaixo, linha fina curta |
| 02 | Abertura | Texto em duas colunas estreitas, letra capitular gigante no início do parágrafo |
| 03 | Dado | Um número gigante em serifada (ex.: "38 mil") com legenda curta embaixo |
| 04 | Contexto | Imagem à esquerda (60%), título e apoio à direita |
| 05 | Citação | Citação em itálico grande entre aspas tipográficas, nome e fonte em caixa alta pequena |
| 06 | Comparativo | Duas colunas separadas por fio vertical, "antes x depois" ou "isso x aquilo" |
| 07 | Dado | Mini gráfico de barras simples e plano (2 a 4 barras) com rótulos, ou segundo número gigante |
| 08 | Lista | Lista numerada de 3 itens em serifada, numerais grandes no destaque |
| 09 | Síntese | Fundo na cor do destaque, uma frase de conclusão em serifada grande |
| 10 | Fecho | "Salve para consultar depois" + "Comenta: [pergunta curta]" + @ do perfil, imagem pequena |

Se não houver citação real para o 05, ele vira Dado. Se não houver comparação natural no 06, vira Contexto.

## Bloco de estilo fixo (copie igual nos 10 prompts)

```
Slide de carrossel de Instagram, formato vertical 4:5, 1080x1350. Design editorial de revista impressa premium: margens largas, grid rígido, muito espaço em branco. Topo: fio fino horizontal, à esquerda o chapéu em caixa alta pequena espaçada, à direita o fólio "{NN}/10". Rodapé: fio fino, à esquerda "{@PERFIL}" em caixa alta pequena, à direita "Edição {DD.MM}". Títulos em serifada de alto contraste estilo jornal, textos de apoio em sans-serif pequena. Paleta: fundo {FUNDO}, texto {TEXTO}, um único destaque {DESTAQUE}. Sem degradê, sem emoji, sem cantos arredondados, sem logotipos de marcas, sem rostos de pessoas reais. Todo o texto em português do Brasil, escrito exatamente como entre aspas, com acentos corretos.
```

## Bloco do slide (acrescente depois do estilo)

```
Tipo: {TIPO}. Layout: {LAYOUT do mapa}. Chapéu: "{CHAPÉU}". Título: "{TÍTULO}". Apoio: "{APOIO}". Imagem: {descrição de uma foto editorial ou ilustração com textura de papel ligada ao assunto, sem marca e sem pessoa real}.
```

Na capa use "Manchete" e "Linha fina" no lugar de Título e Apoio.
