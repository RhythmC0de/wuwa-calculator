# Verificação dos scripts Python

Na raiz do projeto:

```bash
.venv/bin/python tools/lint_project.py
.venv/bin/python -m pytest
.venv/bin/python -m black --check src test tools DEMO tethys.py
```

O primeiro comando executa todas as verificações padrão do Pylint nos
scripts da aplicação, testes, ferramentas e demonstração. A descoberta
exclui `.cache`, `.ruff_cache`, `.pytest_cache`, `.mypy_cache`,
`__pycache__`, ambientes virtuais, `build`, `dist` e dependências externas.
Esses diretórios não precisam ser editados para corrigir alertas do projeto.

O limite de linha é 79 caracteres. Pylint e Black leem `pyproject.toml`.
O ambiente deve ter o extra de desenvolvimento instalado:
`python -m pip install -e ".[dev]"`.

## Bibliotecas compiladas

O plugin local `wuwa_calculator.devtools.pylint_qt` acrescenta somente
`connect`, `disconnect` e `emit` aos descritores identificados como sinais
compilados do PySide6. Ele não modifica os widgets em tempo de execução.
Um teste confirma que operações inválidas continuam gerando diagnósticos.
O problema de inferência está registrado no
[projeto Pylint Qt](https://github.com/pylint-dev/pylint-qt/issues/1).

As APIs do OpenCV efetivamente usadas pelo projeto estão listadas
individualmente em `generated-members`. A regra `no-member` permanece ativa
para os demais nomes, conforme o mecanismo de
[membros gerados do Pylint](https://pylint.readthedocs.io/en/latest/user_guide/checkers/features.html).

## Exceções locais

As regras não são desativadas globalmente. As exceções no código têm
comentários e ficam limitadas ao contexto que as exige:

- campos de registros que seguem contratos de dados;
- assinaturas públicas existentes e métodos definidos por bibliotecas;
- construção ordenada de telas Qt e etapas de cálculo/importação auditáveis;
- fronteiras de workers que precisam comunicar qualquer falha por sinais Qt;
- testes que verificam identidade exata de classes ou caminhos privados;
- módulos que contêm grandes catálogos de dados.

As rotinas de construção de widgets reconhecidas como inicializadores estão
listadas em `defining-attr-methods`. Atribuições em outros métodos continuam
sujeitas à verificação normal.
