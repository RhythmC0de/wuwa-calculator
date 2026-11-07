# TETHYS SYSTEM 1.4

**Black Shores · Arquivo de Ressonadores**

```text
[ TETHYS SYSTEM / ARQUIVO DE RESSONADORES ]
Unidade    JARDINEIROS · BLACK SHORES
Sessão     AGUARDANDO ID DO RESSONADOR
```

> *Reuni neste terminal as fichas dos Ressonadores que acompanhamos e os registros de como lutam. Se estiver avaliando um candidato, use os resultados para recomendar uma função. Se o dossiê for de um adversário, estude a rotação e registre o que sua equipe precisa saber antes do próximo encontro.*
>
> — Nota de um Jardineiro das Black Shores

O **Tethys System** é um aplicativo de desktop para consultar Ressonadores, montar equipes, simular rotações e analisar o dano em gravações de combate. O arquivo é apresentado como uma ferramenta interna das Black Shores para estudar candidatos, aliados e adversários. As composições do simulador podem reunir Ressonadores de facções diferentes.

[Avaliação de combate](#avaliação-de-combate) · [Instalação](#instalação) · [Módulos](#módulos) · [Análise de vídeo](#análise-de-vídeo) · [Planos de desenvolvimento](#planos-de-desenvolvimento) · [Configuração](#configuração) · [Licença](#licença)

## Avaliação de combate

1. **Abra o dossiê.** Consulte o Ressonador por ID e revise seus atributos, armas e habilidades.
2. **Defina o cenário.** Em **Teams**, configure os Echos e simule o Ressonador como DPS principal ou suporte. Confira as sinergias elementais e os efeitos de Sonata.
3. **Compare simulação e campo.** Calcule o dano esperado da rotação e use **Multimídia** para analisar uma gravação de combate.
4. **Registre os resultados.** Salve as rotações e comparações no **Histórico**. Para um candidato, os resultados ajudam a recomendar uma função. Para um aliado ou adversário, ajudam a entender como ele luta e interage com a composição.

Na ambientação do projeto, o **Teste de Germinação** é o protocolo aplicado a candidatos ao recrutamento. A consulta de dossiês e a análise de combate servem também para estudar Ressonadores de outras facções.

## Instalação

| Plataforma | Disponibilidade |
| --- | --- |
| Windows 10 ou superior | Instalação a partir do código-fonte |
| Linux | Primeira distribuição planejada em **AppImage** |

### Windows

Você precisa do **Python 3.11 ou superior** e das dependências de [`requirements.txt`](requirements.txt).

Abra o PowerShell na pasta do projeto. Crie o ambiente virtual, instale as dependências e inicie o terminal.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tethys.py
```

### Linux · AppImage planejado

O **AppImage** é o formato previsto para a primeira distribuição no Linux. O pacote está planejado para incluir o runtime Python e as dependências da aplicação, permitindo iniciar o terminal sem configurar um ambiente virtual.

Ubuntu 22.04+, Debian 12+ e Fedora são alvos iniciais de validação. Antes da publicação, a validação vai cobrir abertura da interface em X11 e Wayland, reprodução de áudio e vídeo, reconhecimento de dano por OCR e aceleração gráfica. As distribuições validadas e eventuais requisitos do sistema serão documentados junto ao pacote.

## Módulos

| Módulo do terminal | O que você pode fazer |
| --- | --- |
| **Dossiê de Ressonadores** | Consultar personagens por ID e visualizar atributos, armas, habilidades e imagens. |
| **Simulador de Rotações** | Calcular o dano de habilidades e rotações para comparar cenários. |
| **Teams** | Montar e salvar equipes, definir o Main DPS e os suportes, configurar Echos e consultar sinergias elementais e o resumo de Sonatas. |
| **Histórico** | Salvar e consultar rotações e comparações de dano. Importar e exportar registros em JSON. |
| **Multimídia** | Reproduzir vídeos locais de referência e analisar o dano exibido durante o combate. |

## Análise de vídeo

1. Abra **Multimídia** e selecione uma gravação local de combate.
2. Preencha **Ignorar vinheta** com o tempo inicial a descartar e **Início da análise** com o ponto em que deseja começar a leitura. Os dois campos usam o formato `mm:ss`.
3. Inicie a análise. O terminal usa o maior dos dois horários. Se a vinheta for de `00:05` e o início da análise estiver em `00:12`, a leitura começa em `00:12`.
4. Consulte o gráfico para acompanhar o dano ao longo do tempo, o DPS, o dano acumulado, a fórmula apresentada e os maiores e menores valores detectados.

A simulação calcula o dano a partir dos parâmetros da rotação. A análise de vídeo usa OCR para reconhecer os números exibidos na gravação, de modo que a leitura depende da legibilidade desses números.

## Planos de desenvolvimento

### Expansão do dossiê

O dossiê atual concentra a ficha técnica do Ressonador. A expansão de lore prevê:

- **Histórico de afiliações** com facção, cargo e período conhecido para cada vínculo registrado.
- **Relação com as Black Shores** conforme o contexto do registro, como aliado, candidato, adversário ou vínculo desconhecido.
- **Registros de lore** com indicação da fonte e do capítulo ou versão, quando disponíveis. Revelações da história ficarão recolhidas por padrão.

## Configuração

| Variável | Finalidade |
| --- | --- |
| `TETHYS_HOME` | Define o diretório de dados do usuário. |
| `TETHYS_BANNER_API_URL` | Define a fonte externa consultada para exibir o banner atual na Home. Se a fonte estiver indisponível, o app continua funcionando em modo offline. |

**Wallpaper.** O arquivo padrão fica em `Assets/app_background_reference.png` e é localizado a partir da raiz do projeto. Para imagens personalizadas, use preferencialmente a proporção **16:10**, com resolução de até **1440 × 900 px**.

### Dados locais e conexões externas

Equipes, histórico e preferências são armazenados localmente no diretório de dados do usuário. No Linux, o caminho padrão é `~/.local/share/tethys`. Use a exportação em JSON na aba **Histórico** para guardar ou transferir registros de rotações e comparações.

Banner, imagens e recursos de análise podem consultar fontes externas quando utilizados.

## Referências de lore

No jogo, Paranora descreve como os **Gardeners** reúnem informações sobre candidatos e como o Tethys define um **Germination Test** sob medida para cada um. Tykwer identifica Camellya como avaliadora dos testes de combate. O Arquivo de Ressonadores e a nota do Jardineiro são criações do projeto inspiradas nesse processo. Aqui, **Jardineiros** e **Teste de Germinação** traduzem os termos em inglês.

- [Paranora — diálogo sobre recrutamento e preparação dos testes](https://wutheringwaves.fandom.com/wiki/Paranora)
- [Tykwer — diálogo sobre os testes de combate](https://wutheringwaves.fandom.com/wiki/Tykwer)
- [Camellya — notas de desenvolvimento sobre a seleção de recrutas](https://wutheringwaves.notion.site/Developer-s-Notes-Camellya-14bef7f91e4b81fbab4bc266df913727)

## Licença

O código do Tethys System é distribuído sob a licença MIT. Consulte o arquivo [`LICENSE`](LICENSE).

*Tethys System é um projeto de fãs inspirado em Wuthering Waves, da Kuro Games.*
