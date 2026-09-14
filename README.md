# Tethys

Aplicativo desktop local para análise de dano, personagens, equipes e rotações
de **Wuthering Waves**, construído com Python e PySide6.

## Recursos

- Carregamento de personagens por ID.
- Visualização de dados, atributos, armas e habilidades.
- Imagens de personagens e armas do catálogo, com hosts HTTPS revisados.
- Cálculo e ajuste manual de multiplicadores e estatísticas.
- Gerenciamento de equipes.
- Histórico de rotações salvas e comparações de dano.
- Aba Multimídia com player de vídeo local para referência de rotações.
- Wallpaper padrão e wallpaper personalizado.
- Configurações persistentes em um pop-up dedicado.
- Diálogo Sobre com README e diagnóstico copiável.

## Requisitos

- Windows 10 ou superior recomendado.
- Python 3.11 ou superior.
- Dependências listadas em `requirements.txt`.

## Instalação

No PowerShell, dentro da pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Execução

Com o ambiente virtual ativado:

```powershell
python main.py
```

Também é possível usar o script `iniciar.bat` ou executar a tarefa
`Executar Wuwa Calculator` configurada no VS Code.

## Banner atual

A aba **Home** consulta um endpoint JSON configurado pela variável
`TETHYS_BANNER_API_URL`, baixa a arte do banner ativo diretamente para a
memória e atualiza o contador. Nenhuma imagem ou resposta é salva em disco.
Se a conexão falhar, a Home exibe o estado offline sem interromper o programa.

Exemplo no PowerShell:

```powershell
$env:TETHYS_BANNER_API_URL = "https://gist.githubusercontent.com/yloove7/b1440f18d4c1152f9f3914fbdb2b7b14/raw/gistfile1.txt"
python main.py
```

O JSON deve conter uma lista `banners` (ou ser uma lista diretamente), com
campos equivalentes a `name`, `image` e `endTime`. Datas ISO 8601 e timestamps
Unix em segundos ou milissegundos são aceitos.

## Como usar

1. Na tela inicial, informe o ID de um personagem, como por exemplo `suisui`.
2. Clique em **Carregar Personagem / ID** ou aperte Enter.
3. Navegue pelas abas do personagem para consultar dados e ajustar valores.
4. Use **Teams** para criar e organizar equipes:
	 - Clique em **Nova equipe** para iniciar uma equipe.
	 - Informe o nome da equipe.
	 - Digite os personagens separados por vírgula no campo de personagens.
	 - Revise o status e clique em **Salvar equipe** para guardar as alterações locais.
	 - Selecione uma equipe existente para editar seus dados e salve novamente.
5. Use **Histórico** para salvar e consultar rotações:
	 - Escolha a equipe no formulário **Teste de rotação salvo**.
	 - Informe um nome para a rotação.
	 - Execute o cálculo e clique em **Salvar cálculo** para registrar o resultado.
	 - Use a tabela **Comparação salva** para selecionar e consultar registros anteriores.
	 - Clique em **Importar JSON** para carregar um histórico existente.
	 - Clique em **Exportar JSON** para salvar o histórico em outro arquivo.
6. Abra **Configurações** para personalizar o programa:
	 - Ative ou desative **Usar imagem de fundo**.
	 - Escolha a resolução entre `1440 x 900`, `1280 x 800` e `1024 x 720`.
	 - Ative ou desative a confirmação antes de fechar o programa.
	 - Em **Wallpaper personalizado**, clique em **Escolher wallpaper** e selecione uma
		 imagem dentro dos limites informados na seção [Wallpaper](#wallpaper).
	 - Clique em **Usar fundo padrão** para voltar a `app_background_reference.png`.
	 - Use **Limpar personagens carregados** para remover as abas e atalhos da sessão,
		 sem apagar arquivos salvos.
	 - Clique em **Restaurar padrões** para retornar às configurações originais.
7. Abra **Sobre** para consultar esta documentação e copiar um diagnóstico.
8. Abra **Multimídia** para usar o player de referência:
	- Clique em **Procurar vídeo** e selecione um arquivo de vídeo local.
	- Use **Play**, **Stop**, a barra de progresso, o volume e as legendas.
	- O nome do vídeo carregado aparece somente no título principal colorido.
	- O nome do vídeo carregado aparece somente no título principal colorido.

## Como editar os dados

Os comentários marcados com `*`, `!` e `?` usam a extensão Better Comments do VS Code.
Eles indicam, respectivamente, pontos editáveis, regras que não devem ser quebradas e
decisões ou fallbacks importantes.

### Adicionar um personagem

Use o mesmo ID minúsculo em todos os catálogos necessários:

```python
# data/characters_ids.py
KNOWN_CHARACTER_IDS = {"novo_personagem", ...}

# data/characters_elements.py
CHARACTER_ELEMENTS = {"novo_personagem": "Fusion", ...}

# data/characters_stats.py
CHARACTER_STATS_DB = {"novo_personagem": {"Base HP": "10,000", ...}}

# data/characters_kits.py
CHARACTER_KITS_DB = {"novo_personagem": {"skills": [], ...}}

# data/images.py
CHARACTER_IMAGE_FALLBACKS = {
    "novo_personagem": {"char": "https://host-permitido/imagem.webp", "weapon": ""},
}
```

O ID precisa existir em `characters_ids.py` e os dicionários devem usar exatamente a
mesma chave. O arquivo `characters_elements.py` valida IDs desconhecidos ao importar.
Para remover um personagem, remova o ID e os registros relacionados dos catálogos;
depois execute uma validação Python antes de abrir o programa.

### Adicionar ou remover elementos

Os elementos aceitos ficam no `element_box` de `app/resonator_tab.py` e suas cores em
`ELEMENT_GLOW_COLORS` e no QSS de `app/styles.py`. Ao adicionar um elemento, atualize
esses três pontos e inclua o valor no mapa `CHARACTER_ELEMENTS`.

```powershell
python -m py_compile main.py app\main.py app\resonator_tab.py app\styles.py
```

## Wallpaper

O fundo padrão é `Assets/app_background_reference.png`.

Wallpapers personalizados devem ter:

- proporção `16:10`;
- tamanho mínimo de `1024 x 640` pixels;
- tamanho máximo de `1440 x 900` pixels;
- tamanho recomendado de `1440 x 900` pixels.

Esses limites evitam deformação e cortes excessivos na janela principal.

## Estrutura do código-fonte

- `main.py`: lançador do Tethys para desenvolvimento e empacotamento.
- `app/`: código Python ativo do Tethys PySide6.
- `app/main.py`: janela principal e diálogos.
- `app/styles.py`: identidade visual e stylesheet global.
- `app/home_tab.py`: tela inicial.
- `app/resonator_tab.py`: detalhes dos personagens.
- `app/teams_tab.py`: gerenciamento de equipes.
- `app/history_tab.py`: histórico de rotações, cálculos e comparações.
- `app/multimedia_tab.py`: aba dedicada ao player multimídia.
- `app/security_policy.py`: política de segurança do conteúdo remoto.
- `app/wuwa_processing.py`: cálculo de dano sem interface ou rede.
- `storage/`: persistência local de equipes e histórico.
- `data/`: dados locais de personagens, imagens e armas.
- `Assets/`: imagens usadas pela interface.
- `docs/`: relatórios e documentação auxiliar.
- `TETHYS_SHA256.txt`: manifesto de integridade do snapshot atual do projeto.

Essa é a estrutura usada durante o desenvolvimento. Depois da compilação, o
usuário final não precisará acessar esses arquivos individualmente.

## Distribuição como executável

O Tethys será distribuído como um aplicativo Windows usando duas etapas:

1. **PyInstaller** reúne o código Python, dependências e arquivos necessários
   em uma pasta de distribuição.
2. **Inno Setup Compiler** empacota essa distribuição em um instalador `.exe`,
   cria os atalhos e instala o programa no computador do usuário.

Depois da instalação, a estrutura esperada será semelhante a esta:

```text
Tethys/
├── Tethys.exe
└── _internal/
	├── Assets/
	├── data/
	├── PySide6/
	└── demais bibliotecas e recursos compilados
```

O usuário deve iniciar o programa pelo atalho ou pelo arquivo `Tethys.exe`.
Os arquivos `.py`, o ambiente virtual e os scripts de desenvolvimento não
precisam ser distribuídos junto com a versão instalada.

### Build futuro

Antes de gerar o instalador definitivo, atualize os nomes legados dos arquivos
de build (`wuwa.spec`, `WuwaDmgLab.iss`, `WuwaCalculadora.exe`) para `Tethys`,
confira o script de entrada usado pelo PyInstaller e garanta que `Assets/`,
`data/` e os arquivos JSON necessários sejam incluídos no pacote.

O snapshot atual possui um hash agregado SHA-256 registrado no cabeçalho de
`TETHYS_SHA256.txt`. Esse arquivo contém o hash individual de cada arquivo
incluído e explica as exclusões. Qualquer alteração legítima no projeto exige
gerar um novo manifesto e publicar um novo hash junto da versão correspondente.

### Projeto legado isolado

O conteúdo antigo baseado em Tkinter/CustomTkinter foi movido para:
`C:\Users\ApenasSeiso\Downloads\Igreja Porta Mod\Isolada\Projeto Legado`.
Ele não faz parte do snapshot PySide6 do Tethys. O armazenamento de histórico e
equipes foi extraído para `storage/`, e o cálculo foi separado em
`app/wuwa_processing.py`; portanto, `wuwa_calculadora.py` não é mais uma
dependência do programa ativo.

## Código aberto e segurança da distribuição

Quem quiser estudar a estrutura do Tethys deve consultar o **repositório
original oficial** do projeto. O código será open source, e o repositório é a
fonte correta para acompanhar alterações, revisar o código, reproduzir o build
e contribuir com melhorias. Cópias, forks e executáveis recebidos de terceiros
não devem ser tratados como versões oficiais automaticamente.

É importante separar duas coisas:

- O código aberto permite que qualquer pessoa analise e modifique uma cópia.
- A distribuição oficial precisa provar sua autenticidade para que o usuário
  saiba que o instalador não foi adulterado.

Para a versão oficial, use estas proteções no processo de publicação:

1. Publique o código-fonte e os instaladores somente no repositório e nas
	releases oficiais do Tethys.
2. Assine digitalmente `Tethys.exe` e o instalador com um certificado de
	assinatura de código reconhecido pelo Windows.
3. Gere e publique o hash SHA-256 de cada instalador para conferência antes da
	instalação.
4. Mantenha o build do PyInstaller e o script do Inno Setup versionados para
	que o executável possa ser auditado e reproduzido.
5. Não inclua executáveis desconhecidos em `Assets/`, `data/` ou `_internal/`.
	Esses diretórios devem conter somente os recursos e bibliotecas necessários.
6. Não execute arquivos importados pelo usuário, como `.exe`, `.bat`, `.cmd`,
	`.ps1` ou macros. JSON, vídeos e imagens devem ser tratados apenas como
	dados.
7. Ao distribuir uma atualização, publique changelog, versão, hash e assinatura
	junto com o instalador.

No código PySide6 atual, imagens locais e empacotadas continuam permitidas, e
as imagens do catálogo de personagens e armas podem ser carregadas somente por
HTTPS a partir dos hosts revisados `rackoon.com.br`, `wuwalab.com` e
`i.imgur.com`. O conteúdo recebido é convertido em pixels por Qt e qualquer
resposta que não seja uma imagem é descartada. URLs fora da lista, HTTP e
arquivos executáveis são ignorados e usam os fallbacks locais.

A aba **Build Echos** atualmente mantém nome, bônus e passivas como dados
textuais; ela ainda não possui catálogo visual de Echoes nem widgets de imagem.
Por isso, não há imagens de Echoes ativas para carregar nesta versão.

O Tethys não solicita privilégios de administrador nem executa comandos de
kernel. A aplicação deve ser distribuída e executada com privilégios normais do
usuário; qualquer instalador ou atualização que peça elevação inesperada deve
ser tratado como suspeito.

Nenhum programa consegue impedir completamente que alguém modifique uma cópia
local e redistribua esse arquivo com outro conteúdo. A proteção confiável é
permitir que o usuário identifique a versão oficial por meio do repositório,
da assinatura digital e do hash publicado. Caso uma réplica apresente um
instalador sem assinatura, um hash diferente ou solicite executar arquivos
estranhos, não instale nem execute essa versão.

## Dados e privacidade

O aplicativo foi projetado para uso local. Arquivos de histórico, equipes e
preferências ficam na pasta do projeto ou nas preferências locais do usuário.
Ao usar recursos que consultam dados externos, a conexão depende da
disponibilidade das fontes configuradas.

## Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo `LICENSE` para
o texto completo.