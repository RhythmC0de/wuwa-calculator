# Convenções de imports

O nome importável é `wuwa_calculator`; `src` é somente o diretório de fontes.
Use imports absolutos entre camadas. Imports relativos explícitos dentro de
um subpacote, como `domain.review`, continuam válidos.

Instale o checkout com `python -m pip install -e ".[dev]"` e execute
`python -m pytest`. A instalação também disponibiliza o comando `tethys`.
Os scripts em `tools/` e `test/validate_data.py` usam o pacote instalado.

Separe biblioteca padrão, dependências externas e imports internos em grupos.
Evite imports com `*`. Não capture exceções amplas apenas para esconder falhas
de importação.

Imports locais têm usos intencionais neste projeto: carregamento opcional de
OCR/VLC, inicialização adiada de telas e carregamento da engine nativa antes
de Qt Multimedia. Essa ordem evita conflito entre bibliotecas FFmpeg.
O catálogo também carrega módulos de dados sob demanda.

O launcher `tethys.py` mantém um bootstrap de `src` para compatibilidade com
checkouts sem instalação. O subprocesso de vídeo propaga o diretório de fontes
para funcionar também nesse modo. Os testes próprios da extensão C++ podem
receber a pasta do binário compilado. Esses casos não devem ser replicados nos
módulos comuns do aplicativo.

Os testes de arquitetura verificam limites entre camadas, módulos internos
existentes, ausência de imports `src.*` e identidade das classes do backend.

Referências oficiais:

- [PEP 8: imports](https://peps.python.org/pep-0008/#imports)
- [PyPA: src layout](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/)


O OCR de screenshots é opcional: `python -m pip install -e ".[ocr]"`. O PaddlePaddle não oferece wheel para o Python 3.14 deste ambiente; para esse recurso, use um ambiente separado com Python compatível (por exemplo, 3.12). A instalação básica e os testes não exigem PaddlePaddle. A engine nativa de vídeo tem sua própria configuração de OCR.
