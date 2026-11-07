# Guia de imagens do README

Os arquivos `screenshot-*.png` e `demo-*.gif` desta pasta são **molduras provisórias**. Grave os reais com **o mesmo nome** e o README já passa a mostrá-los. O banner, os ícones, o divisor e o pipeline estão prontos (SVG próprio, gerados por `tools/gen_readme_assets.py`).

## Pontos de imagem

| # | Onde no README | Arquivo | Formato | O que mostrar |
|---|---|---|---|---|
| 1 | Topo | `banner-dark/light.svg` | pronto | Identidade (animado) |
| 2 | Logo abaixo do banner | `demo-visao-geral.gif` | GIF, 1280×720 (exibido a 860), 8–12 s, < 4 MB | Dossiê → Teams → Multimídia, em sequência |
| 3 | Galeria | `screenshot-dossie.png` | PNG 1280×800 | Dossiê de um Ressonador com habilidades |
| 4 | Galeria | `screenshot-teams.png` | PNG 1280×800 | Equipe completa com sinergias e Sonatas |
| 5 | Galeria | `screenshot-simulador.png` | PNG 1280×800 | Rotação calculada com o resultado |
| 6 | Galeria | `screenshot-multimidia.png` | PNG 1280×800 | Gráfico de dano com o vídeo ao lado |
| 7 | Análise de vídeo | `demo-analise-video.gif` | GIF 960×600, 8–10 s | Iniciar a análise e o gráfico se formando |
| 8 | Análise de vídeo | `demo-revisao.gif` | GIF 960×600, 8–10 s | Janela de revisão: digitar `785 + 2518`, `A`, `D` |
| 9 | Ajustes do repositório | `social-preview.png` (pronto) | PNG 1280×640 | GitHub → Settings → Social preview |

Ícones (`icon-*.svg`) já estão em Módulos; o `pipeline-*.svg` em Análise de vídeo; o `divider.svg` separa as seções.

## Regras para ficar profissional

- **Mesma janela, mesmo tamanho e mesmo tema** em todas as capturas. Use o mesmo Ressonador nas quatro da galeria.
- Esconda caminhos de pasta pessoais, nomes de usuário e a barra de tarefas.
- **Direitos:** o repositório é público. Prefira não incluir gameplay oficial nem arte oficial dos personagens. Para Multimídia e Revisão, use o **vídeo sintético** (números gerados por você sobre fundo próprio). Nas telas de dossiê, evite retratos oficiais ou use um espaço em branco com a moldura.
- Dois GIFs pesados deixam a página lenta. Mantenha cada um abaixo de 4 MB.

## Roteiros dos GIFs

**demo-visao-geral (10 s)**: abrir o Dossiê e digitar um ID (2 s) → ir a Teams e escolher o DPS principal (3 s) → ir a Multimídia e iniciar a análise (4 s) → parar no gráfico (1 s).

**demo-analise-video (9 s)**: carregar o vídeo sintético, preencher o início, clicar em iniciar, deixar o gráfico crescer, mostrar DPS e total no final.

**demo-revisao (9 s)**: abrir a revisão, mostrar o recorte, digitar `785 + 2518`, `Enter`, depois `D` em um item que não é dano e **Concluir revisão**.

## Converter gravação de tela em GIF leve

```bash
ffmpeg -i gravacao.mp4 -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=4" -loop 0 demo-revisao.gif
```

Reduza `fps` para 12 ou a largura para 800 se passar de 4 MB. Para trocar o GIF por WebP: `ffmpeg -i gravacao.mp4 -vf "fps=15,scale=960:-1" -loop 0 -q:v 70 demo.webp` (o GitHub exibe, mas GIF é mais compatível).

## Ajustar o estilo

`python tools/gen_readme_assets.py docs/media` regenera banner, ícones, divisor e pipeline. As cores ficam no dicionário `THEMES` (escuro e claro) no topo do script.
