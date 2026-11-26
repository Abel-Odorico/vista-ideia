# Ritmo humano: regras para qualquer IA que faça ou revise vídeo

Este arquivo vale para qualquer modelo (Claude, Grok, Gemini, GPT, Codex, Cursor) e para pessoas. Ele é texto
simples de propósito: cole inteiro no prompt de qualquer IA que for escrever roteiro, montar cena, editar ou
revisar vídeo. As ferramentas leem o bloco **Limites** no fim, então um número muda aqui e muda em todo lugar.

**Fonte canônica:** `Abel-Odorico/grokbot-video-playbook`, arquivo `regras/RITMO-HUMANO.md`. Os outros
repositórios (movie-code-motion, peep-videos, transcribe-peep, vista-ideia) guardam uma cópia idêntica.
Mudou uma regra? Mude na fonte, copie para os outros e suba a `versao` do bloco Limites.
`python3 regras/conferir_regras.py` confere se a cópia está bem formada; com `--contra <outra cópia>`, se é igual.

**Como uma regra entra aqui:** toda crítica (do Abel, de quem assiste, de um juiz do revisor cego) que apontar
um erro de verdade vira uma linha, com **data**, **origem** (quem disse e onde, com as palavras de quem disse)
e, quando der, **como medir**. Regra que não se mede fica marcada `[olho]`; regra que um script confere,
`[auto]`. Nada é apagado: regra substituída fica riscada com a data e a regra que a substituiu.

## Por que estas regras existem

A máquina processa rápido; quem assiste, não. O erro que estas regras corrigem é editar no ritmo da máquina:
trocar a tela a cada sílaba, mostrar um número que some antes de ser lido, falar de algo que ainda não está
na tela. O cérebro precisa de um tempo para transformar o que viu em algo que entendeu (tempo de assimilação).
A edição é o motorista e o olho de quem assiste é o passageiro: arrancar e frear o tempo todo cansa;
velocidade de cruzeiro deixa entender.

## Regras de ritmo humano (RH)

### RH-01 · O movimento segue a ideia, não a sílaba `[auto]`
- **Regra:** a tela muda quando a ideia muda. Nada de cada palavra falada disparar uma entrada, um zoom ou um
  corte. Poucas arrancadas por minuto e muito tempo em velocidade de cruzeiro.
- **Limite:** arrancadas por minuto até 22 (meta); acima de 30 reprova. Pelo menos 80% do tempo em cruzeiro
  (meio segundo sem nenhum arranque conta como cruzeiro).
- **Como medir:** `ritmo_humano.py video.mp4` (conta as arrancadas: cada vez que a tela sai do quase parado
  ou acelera de repente, inclusive corte duro).
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "eles não podem acompanhar a velocidade da fala, troca do a todo momento".
  Vídeo "Inteligência artificial ajusta vídeos após críticas do público" (Maestros da IA) [04:18 a 04:50]:
  35 arrancadas por minuto nos vídeos com queixa contra 22 no mais visto, que passava 8 vezes mais tempo em
  velocidade de cruzeiro; "agora o movimento segue a ideia, não a sílaba". Os números só comparam vídeos
  medidos pela mesma ferramenta.

### RH-02 · Dado e texto ficam parados tempo suficiente para ler `[auto]`
- **Regra:** todo número, dado ou frase da tela já está lá quando é falado e fica parado e legível pelo menos
  1,5 s; texto mais longo fica 0,5 s mais 0,3 s por palavra, quando isso der mais que 1,5 s (6 palavras = 2,3 s).
  Depois que a tela assenta, ela segura antes da próxima arrancada.
- **Limite:** no máximo 25% dos intervalos entre arrancadas abaixo de 1,5 s.
- **Como medir:** `ritmo_humano.py` (intervalos curtos, com o segundo de cada um); com `--tempo tempo.json`,
  também confere a antecedência de cada cena em relação à fala (RH-04).
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "Precisamos aumentar a duração das informações na tela, as animações para que
  os humanos que assistem consigam entender, compreender e processar". Vídeo [04:52]: "o dado fica parado.
  Todo número já está na tela quando eu falo dele e fica pelo menos 1 segundo e meio"; espectador que pediu
  para dobrar o tempo de cada informação [00:57].

### RH-03 · Um herói por vez: holofote no que está sendo falado `[olho]`, `[auto]` no motor
- **Regra:** o elemento da tela que está em sintonia com a fala ganha a cor de destaque da paleta do vídeo
  (na ADL, terracota `#B85C4E` ou dourado `#C9A961`; no Workflow, o laranja do tema); o resto fica a meia luz
  (opacidade perto de 0,4), legível mas recuado. Só um elemento aceso por vez. O destaque passa para o próximo
  com uma troca suave (cerca de 0,3 s), sem arrancada.
- **Limite:** 1 elemento aceso por vez; meia luz entre 0,35 e 0,5.
- **Como medir:** no motor (movie-code-motion: `"ritmo": "humano"` no roteiro, que já é o padrão para episódio
  novo; peep-videos: componente `Holofote`); no vídeo, olho na folha de quadros.
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "Precisamos que o elemento da tela que estiver em sintonia com o que está sendo
  falado tenha destaque, tipo uma cor de destaque para indicar visualmente onde estamos". Vídeo [05:03]:
  "um herói por vez. Quando uma coisa fala, o resto da tela fica a meia luz. Como um holofote".

### RH-04 · A cena é montada antes da fala `[auto]`
- **Regra:** a cena entra e assenta antes da primeira palavra sobre ela. Os elementos que a fala vai citar já
  estão na tela (a meia luz) quando a fala começa; a fala acende, não faz aparecer.
- **Limite:** a fala do ato começa pelo menos 0,6 s depois da troca de cena (padrão 1,0 s, que cobre a
  entrada calma da ADL, de 0,9 s).
- **Como medir:** `ritmo_humano.py video.mp4 --tempo tempo.json` (troca de cena contra início da fala, ato a
  ato). No movie-code-motion o `narrar.py` usa a antecedência padrão deste arquivo.
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "O que está na tela precisa ser assimilado, logo monte as cenas antes do áudio
  para que ambos sejam conectados". Vídeo [03:29]: espectador que sugeriu "montar a cena antes de eu falar dela".

### RH-05 · Respiro entre ideias `[auto]`
- **Regra:** entre uma ideia e a próxima, uma pausa na fala para o cérebro guardar o que ouviu. A tela também
  respira: nada de nova entrada nesse intervalo.
- **Limite:** pausa de pelo menos 0,8 s entre falas de atos diferentes (padrão 1,0 s).
- **Como medir:** `ritmo_humano.py --tempo tempo.json` (ou `--falas legenda.vtt`/`.srt`).
- **Data:** 25/11/2026.
- **Origem:** vídeo [05:14]: "eu respiro. Uma pausa entre as ideias para o seu cérebro guardar o que ouviu".
  Pedido do Abel de 25/11/2026 de levar as regras do vídeo para os repositórios.

### RH-06 · Música abaixo da voz `[auto]`
- **Regra:** enquanto alguém fala, a música fica bem abaixo da voz e nunca disputa a palavra.
- **Limite:** música pelo menos 12 dB abaixo da voz durante a fala (meta 15 dB), medido em loudness momentânea.
  O arquivo final continua em -16 LUFS e pico real até -1,5 dBTP.
- **Como medir:** `ritmo_humano.py --voz voz.wav --musica musica.wav` (trilhas separadas, antes da soma).
- **Data:** 25/11/2026.
- **Origem:** vídeo [02:31] (música "estourada e competindo com o locutor") e [05:23] ("a música foi para trás,
  bem abaixo da minha voz"). Pedido do Abel de 25/11/2026.

### RH-07 · Nada de texto miúdo `[auto]` com OCR, `[olho]` sem
- **Regra:** quem assiste no celular precisa ler sem pausar. Plaquinha pequena que ninguém lê sai do vídeo.
- **Limite:** tamanho de fonte do texto de leitura de pelo menos 4% do lado menor do quadro (43 px em 1080p,
  vertical ou horizontal); rótulo secundário pelo menos 3% (32 px). Até 6 palavras por bloco de texto.
- **Como medir:** `ritmo_humano.py --ocr` quando houver `tesseract` (a caixa de uma palavra lida mede cerca de
  70% do tamanho da fonte, então o mínimo medido é 70% de 3%); sem ele, olho na folha de quadros do revisor
  cego, em que cada quadro tem a largura de um celular.
- **Data:** 25/11/2026.
- **Origem:** vídeo [05:28]: "tirei as plaquinhas miúdas que ninguém conseguia ler". Abel, 24/11/2026: cards
  com fonte grande, pensando no celular.

### RH-08 · Revisor cego com 2 juízes antes de trocar uma versão por outra `[auto]`
- **Regra:** quando há uma versão anterior (aprovada ou publicada) e uma nova, dois juízes de IA de famílias
  diferentes assistem às duas sem saber qual é qual, cada um nas duas ordens (4 pareceres). O revisor só pede
  ajuste quando acha **erro grave** na versão nova; gosto pessoal não vira pedido.
- **Erro grave é:** texto ou número errado contra o roteiro; informação que some antes de dar para ler; fala
  sobre algo que não está na tela; música cobrindo a voz; texto ilegível no celular; corte quebrado, quadro
  preto ou tela travada; marca ou paleta errada; e a versão nova perder para a anterior nas medidas de
  ritmo humano ou de qualidade de imagem (cor abaixo de 80% ou nitidez abaixo de 70% da anterior).
- **Como medir:** `revisor_cego.py --anterior A.mp4 --novo B.mp4`. Sem chave de IA, `--juiz manual` gera o
  pacote (folhas de quadros, medidas e prompt) para colar em qualquer IA e ler os pareceres de volta.
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "Crie antes um revisor (2 juízes) que assista e compare a versão nova com a
  anterior sem saber qual é qual é solicitar ajustes caso tenha erros graves". Vídeo [05:33 a 05:56]: duas IAs
  juízas, 70 pareceres, a versão nova venceu as quatro disputas finais.

### RH-09 · Crítica vira regra com data e origem `[olho]`
- **Regra:** cada reclamação real vira uma linha neste arquivo (ou no `checks.md` do repositório, apontando
  para cá), com data e as palavras de quem reclamou. Nenhuma regra fica só na memória de um modelo.
- **Data:** 25/11/2026.
- **Origem:** Abel, 25/11/2026: "Ter um local para as regras e que elas sejam consumidas por qualquer modelo de
  ia, não só Claude". Vídeo [03:52 a 04:14]: "cada reclamação de vocês virou uma regra escrita com a data e as
  palavras de quem reclamou".

## Regras da casa já decididas (RC), que qualquer IA também precisa saber

| Id | Data | Origem | Regra |
|---|---|---|---|
| RC-01 | 24/11/2026 | Abel, ao ver o Palco com as cores dos prints | De referência de outro canal leva-se só layout, tipografia e ritmo. A paleta é sempre a nossa: ADL (azul-profundo `#0B1F3B`, petróleo `#0A4D5C`, terracota `#B85C4E`, dourado `#C9A961`, texto `#F2EFEA`; Manrope nos títulos, Inter no texto) ou a do tema do estilo. |
| RC-02 | 24/11/2026 | Abel: "precisa ser bonito e legível" | Legibilidade vem antes de efeito. Cards com fonte grande, pensando no celular (ele também testa em TV). |
| RC-03 | 24/11/2026 | Abel | Legenda queimada desligada por padrão (o YouTube já legenda); só em vídeo didático específico, ligada pelo roteiro. |
| RC-04 | 24/11/2026 | Abel | Repertório grande de transições, mas no máximo 2 tipos por vídeo de até 10 minutos. |
| RC-05 | 24/11/2026 | Abel | Estilo novo entra como repertório a mais; nunca remover nem substituir o que já existe. |
| RC-06 | 25/11/2026 | Abel, sobre o corte com efeitos do transcribe | Antes de entregar, comparar com a versão aprovada: cor e nitidez em 3 quadros (cor de pelo menos 80%, nitidez de pelo menos 70%); gravação HDR do iPhone convertida para BT.709. |

## Ordem de trabalho que estas regras pedem

1. Roteiro: uma ideia por ato, com respiro no fim de cada ideia (RH-05).
2. Cena: montada antes da fala, elementos a meia luz e o holofote preso à palavra (RH-03, RH-04).
3. Cards parados: olhar a folha no tamanho de celular (RH-07, RC-02).
4. Render e medida: `ritmo_humano.py` no arquivo final (RH-01, RH-02, RH-04, RH-05, RH-06).
5. Revisor cego contra a versão anterior (RH-08). Erro grave volta para o passo que o causou.
6. O que a revisão ou o Abel apontar de novo vira regra aqui (RH-09).

## Limites (lidos pelas ferramentas)

```json
{
  "versao": "2026-11-25.1",
  "arrancadas_por_minuto": {"meta": 22, "maximo": 30},
  "cruzeiro_fracao_min": 0.8,
  "dado_fixo_min_s": 1.5,
  "leitura_s_por_palavra": 0.3,
  "leitura_base_s": 0.5,
  "intervalos_curtos_max_fracao": 0.25,
  "antecedencia_cena_s": {"min": 0.6, "padrao": 1.0},
  "respiro_entre_ideias_s": {"min": 0.8, "padrao": 1.0},
  "holofote": {"meia_luz": 0.4, "meia_luz_faixa": [0.35, 0.5], "acesos_por_vez": 1, "troca_s": 0.3},
  "musica_abaixo_da_voz_db": {"min": 12, "meta": 15},
  "texto_altura_min_fracao": {"corpo": 0.04, "rotulo": 0.03},
  "palavras_por_bloco_max": 6,
  "qualidade_contra_anterior": {"cor_min": 0.8, "nitidez_min": 0.7},
  "revisor": {
    "juizes": ["openrouter:anthropic/claude-sonnet-4.5", "openrouter:google/gemini-2.5-pro"],
    "ordens_por_juiz": 2,
    "quadros_por_video": 24
  }
}
```
