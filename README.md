# Tethys System 1.4

O Tethys System é o terminal central de Black Shores, conhecido como a Mesa de Areia da Civilização. Na lore de **Wuthering Waves**, ele observa o Lamento, emite alertas e usa cálculos para compreender seus eventos. Os dados do Lamento são visualizados como estrelas dentro do sistema, enquanto informações descartadas seguem para a Necroestrela.

Este projeto adapta esse conceito para uma ferramenta local de análise de personagens, equipes, rotações e dano. O aplicativo organiza dados e simulações para apoiar a leitura de combates e o estudo de diferentes composições.

## Recursos

- Consulta de personagens por ID.
- Atributos, armas, habilidades e imagens.
- Cálculo de dano e rotações.
- Gerenciamento completo de equipes.
- Seleção de personagens por slot.
- Configuração de Echos e resumo de sinergia.
- Histórico de rotações e comparações.
- Importação e exportação de histórico em JSON.
- Player local de vídeos de referência.
- Análise de DPS com OpenCV e RapidOCR.
- Gráfico de dano por tempo, picos e menores danos.
- Wallpaper padrão ou personalizado.
- Configurações persistentes.

## Requisitos

- Windows 10 ou superior; suporte Linux planejado.
- Python 3.11 ou superior.
- Dependências do arquivo `requirements.txt`.

### Requisitos futuros para Linux

A versão Linux deverá ser preparada e validada em distribuições atuais, como Ubuntu 22.04+, Debian 12+ ou Fedora equivalente, com:

- Python 3.11 ou superior;
- `python3-venv` e `python3-pip`;
- Qt6 e bibliotecas gráficas do sistema;
- Mesa/OpenGL e EGL;
- X11 ou Wayland;
- FFmpeg e codecs necessários para reprodução de vídeo;
- bibliotecas de áudio compatíveis com Qt Multimedia;
- dependências Python de `requirements.txt`.

Os nomes dos pacotes podem variar entre distribuições. A compatibilidade Linux será considerada concluída somente após testes de janela, áudio, vídeo, OCR e aceleração gráfica.

## Instalação

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

No Linux, a instalação deverá usar o gerenciador de pacotes da distribuição para os componentes de sistema e um ambiente virtual Python para as dependências do projeto.

## Execução

```powershell
python main.py
```

A aplicação pode ser executada diretamente pelo VS Code ou pelo script de inicialização disponível no projeto.

## Uso rápido

### Personagens

1. Informe o ID do personagem no campo superior.
2. Clique em **Carregar Personagem / ID**.
3. Consulte atributos, habilidades, armas e cálculos.

### Teams

1. Abra a aba **Teams**.
2. Crie uma equipe ou selecione uma existente.
3. Escolha os personagens nos slots Main DPS, Suporte 1 e Suporte 2.
4. Configure os Echos de cada personagem.
5. Confira a sinergia elemental e as Sonatas.
6. Salve a equipe.

As equipes são armazenadas localmente em `data/teams.json`.

### Histórico

1. Abra a aba **Histórico**.
2. Escolha uma equipe e informe o nome da rotação.
3. Salve o resultado do cálculo.
4. Selecione registros para consultar comparações e auditorias.
5. Use os botões de importação e exportação para trabalhar com arquivos JSON.

O histórico é armazenado localmente em `data/rotation_history.json`.

### Multimídia

1. Abra a aba **Multimídia**.
2. Selecione um vídeo local.
3. Use os controles de reprodução, volume, progresso e legendas.
4. Informe o horário de **Ignorar vinheta** no formato `mm:ss`.
5. Informe o horário de **Início da análise** no formato `mm:ss`.
6. Inicie a análise para reconhecer números de dano reais no vídeo.

A análise começa no maior dos dois horários definidos. O gráfico mostra DPS, dano acumulado, fórmula, picos e menores danos.

## Banner da Home

A Home consulta o banner atual pela variável `TETHYS_BANNER_API_URL`. Caso a fonte externa esteja indisponível, o programa continua funcionando em modo offline.

Exemplo:

```powershell
$env:TETHYS_BANNER_API_URL = "https://gist.githubusercontent.com/yloove7/b1440f18d4c1152f9f3914fbdb2b7b14/raw/gistfile1.txt"
python main.py
```

## Wallpaper

O wallpaper padrão fica em `Assets/app_background_reference.png`.

Wallpapers personalizados devem preferencialmente usar proporção `16:10` e resolução de até `1440 x 900` pixels.

## Desempenho

O Tethys carrega as abas conforme o uso, mantém a rede em segundo plano e adia bibliotecas pesadas de análise até a utilização da Multimídia.

## Estrutura essencial

- `main.py`: inicialização do programa.
- `app/`: interface e funcionalidades principais.
- `data/`: catálogos locais.
- `storage/`: equipes e histórico salvos.
- `Assets/`: imagens da interface.
- `requirements.txt`: dependências Python.

## Privacidade

Equipes, histórico e preferências são armazenados localmente. Recursos de banner, imagens e análise podem acessar fontes externas quando utilizados.

## Licença

Este projeto é distribuído sob a licença MIT. Consulte `LICENSE` para o texto completo.
