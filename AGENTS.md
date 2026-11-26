# AGENTS.md: vista-ideia

Entrada para qualquer agente de IA que abrir este repositório (Grok, Claude Code, Codex, Cursor, Gemini CLI, OpenCode).
O repositório gera reels de unboxing (vitools) e guarda o material dos bots de conteúdo da Vista Ideia (`docs/grokbot/`).

## Leia antes de mexer em qualquer vídeo

1. **`regras/RITMO-HUMANO.md`**: os vídeos são feitos para pessoas. Dado e legenda parados pelo menos 1,5 s (texto longo:
   0,5 s + 0,3 s por palavra), movimento que segue a ideia (não a sílaba), destaque só no que está sendo mostrado com o resto
   recuado, respiro entre ideias, música abaixo da voz, nada de texto miúdo (pensando no celular) e revisor cego com 2
   juízes antes de trocar uma versão por outra. Cada regra tem data e origem. Cole o arquivo inteiro no prompt de qualquer
   IA que for escrever roteiro, montar cena ou revisar.
2. **`README.md`**: como o vitools renderiza um projeto JSON.

## Ferramentas

```bash
python3 tools/checar_ritmo.py projects/unboxing.json        # antes de renderizar (o render.py já roda e só avisa)
python3 tools/ritmo_humano.py output/vista_ideia_unboxing.mp4   # depois: mede o MP4 final
python3 tools/revisor_cego.py --anterior v1.mp4 --novo v2.mp4   # 2 juízes cegos; sem chave: --juiz manual
python3 tools/teste_ritmo_humano.py                         # teste das ferramentas
python3 regras/conferir_regras.py --contra ../grokbot-video-playbook/regras/RITMO-HUMANO.md
```

Medido em 25/11/2026: o reel de unboxing de 19 s dava 41 arrancadas por minuto. Em 26/11/2026 o Abel decidiu que a
meta de até 22 vale também para reel: o `projects/unboxing.json` passou a 25 s, com foto em velocidade constante
(`"shot_easing": "linear"`), legenda trocando junto com a foto, sem flash e contador da legenda em 32 px. Mede 19,2
arrancadas por minuto, 84% em cruzeiro. O original fica em `projects/unboxing-19s.json` (renderiza igual ao de antes).

## Como uma regra nova entra

A fonte é `Abel-Odorico/grokbot-video-playbook/regras/RITMO-HUMANO.md`: mude lá, suba a `versao` e copie para cá.
Crítica do Abel, de quem assiste ou de um juiz que apontou erro de verdade vira linha, com data e as palavras de quem
disse. Nunca guarde regra só na memória de um modelo.

## Combinados da casa

Paleta da marca do projeto (aqui, Navy `#0C1B36` e Creme `#F4EFE4`); legibilidade antes de efeito; legenda curta e
grande; no máximo 2 tipos de transição por vídeo; estilo novo só soma, nunca substitui. Geração paga e publicação só com
o OK do Abel.
