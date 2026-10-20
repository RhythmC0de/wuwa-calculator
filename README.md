TETHYS SYSTEM 1.4
==================

O Tethys System é o terminal central de Black Shores, também conhecido como a Mesa de Areia da Civilização.

Na lore de Wuthering Waves, o sistema existe antes do Lamento e é usado para observar eventos, emitir alertas e resolver questões relacionadas ao Lamento. Ele armazena uma quantidade quase infinita de dados e utiliza as emoções provenientes do Lamento para alimentar seus cálculos.

Dentro do sistema, os dados do Lamento são visualizados como estrelas. Os dados descartados são enviados para a Necroestrela. Apenas o Sistema Tethys compreende a verdadeira natureza do Lamento.

Este projeto adapta esse conceito para uma ferramenta local de análise de personagens, equipes, rotações e dano em Wuthering Waves.

RECURSOS PRINCIPAIS
-------------------

- Consulta de personagens por ID.
- Atributos, armas, habilidades e imagens.
- Cálculo de dano e rotações.
- Gerenciamento de equipes, personagens e Echos.
- Sinergia elemental e resumo de Sonatas.
- Histórico de rotações e comparações.
- Importação e exportação de histórico em JSON.
- Player local de vídeos de referência.
- Análise de DPS com reconhecimento de números de dano.
- Gráfico de dano por tempo, picos e menores danos.
- Wallpaper padrão ou personalizado.

REQUISITOS
----------

- Windows 10 ou superior; suporte Linux planejado.
- Python 3.11 ou superior.
- Dependências listadas em requirements.txt.

REQUISITOS FUTUROS PARA LINUX
-----------------------------

A versão Linux deverá ser preparada e validada em distribuições atuais, como Ubuntu 22.04+, Debian 12+ ou Fedora equivalente, com:

- Python 3.11 ou superior.
- python3-venv e python3-pip.
- Qt6 e bibliotecas gráficas do sistema.
- Mesa/OpenGL e EGL.
- X11 ou Wayland.
- FFmpeg e codecs necessários para reprodução de vídeo.
- Bibliotecas de áudio compatíveis com Qt Multimedia.
- Dependências Python de requirements.txt.

Os nomes dos pacotes podem variar entre distribuições. A compatibilidade Linux só deverá ser considerada concluída após testes de janela, áudio, vídeo, OCR e aceleração gráfica.

INSTALAÇÃO
----------

No PowerShell, dentro da pasta do projeto:

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

No Linux, os componentes de sistema deverão ser instalados pelo gerenciador de pacotes da distribuição e as dependências Python em um ambiente virtual.

EXECUÇÃO
--------

python main.py

TEAMS
-----

Abra a aba Teams para criar equipes, selecionar Main DPS e suportes, configurar Echos, consultar sinergias e salvar as composições.

As equipes são armazenadas localmente em src\wuwa_calculator\storage\user_data\teams.json.

HISTÓRICO
---------

A aba Histórico permite salvar, consultar, importar e exportar rotações e comparações de dano.

O histórico é armazenado localmente em src\wuwa_calculator\storage\user_data\rotation_history.json.

MULTIMÍDIA
----------

Selecione um vídeo local para consultar a rotação e iniciar a análise de dano.

- Ignorar vinheta: tempo inicial que deve ser desconsiderado.
- Início da análise: momento em que a leitura de dano deve começar.
- Os dois campos usam o formato mm:ss.
- A análise efetiva começa no maior dos dois horários.

O gráfico apresenta DPS, dano acumulado, fórmula, picos e menores danos.

BANNER DA HOME
--------------

A Home consulta o banner atual pela variável TETHYS_BANNER_API_URL. Se a fonte externa não estiver disponível, o programa continua funcionando em modo offline.

WALLPAPER
---------

O wallpaper padrão está em Assets\app_background_reference.png. O código resolve esse asset pela raiz do projeto, independentemente do diretório atual do terminal.
Wallpapers personalizados devem preferencialmente usar proporção 16:10 e resolução de até 1440 x 900 pixels.

PRIVACIDADE
-----------

Equipes, histórico e preferências são armazenados localmente. Banner, imagens e recursos de análise podem acessar fontes externas quando utilizados.

LICENÇA
-------

Este projeto é distribuído sob a licença MIT. Consulte LICENSE para o texto completo.
