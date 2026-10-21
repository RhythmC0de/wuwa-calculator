"""Regras de arquitetura, verificadas lendo os imports (sem executar nada).

Camadas (cada uma só enxerga as de baixo):
    domain  <  infrastructure/services/storage/utils  <  ui  <  app

  * domain: Python puro. Nada de Qt, rede, disco ou outras camadas.
  * infrastructure/services/storage/utils: sem Qt e sem ui/app.
  * ui: pode usar Qt e as camadas de baixo; não importa `app`.
  * app: só o ponto de entrada (main.py).
Também garante que todo import interno aponta para um módulo que existe.
"""

import ast
from pathlib import Path

PACKAGE = "wuwa_calculator"
ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = next(p for p in (ROOT / "src" / PACKAGE, ROOT / PACKAGE) if p.is_dir())

QT = ("PySide6", "PyQt5", "PyQt6", "pyqtgraph")
LOWER = ("infrastructure", "services", "storage", "utils")

FORBIDDEN = {
    "domain": LOWER + ("ui", "app"),
    "infrastructure": ("ui", "app"),
    "services": ("ui", "app"),
    "storage": ("ui", "app"),
    "utils": ("ui", "app"),
    "ui": ("app",),
}
NO_QT = {"domain", "infrastructure", "services", "storage", "utils"}
APP_ALLOWED = {"__init__.py", "main.py"}

# Violações que já existiam antes da reorganização. A lista só pode diminuir:
# se corrigir uma, remova daqui; novas violações fazem o teste falhar.
KNOWN_DEBT: set[tuple[str, str]] = {
    # Bloco `if __name__ == "__main__"` (CLI de depuração) que abre um seletor Qt.
    ("services/ocr/service.py", "PySide6"),
}


def _modules():
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        if "__pycache__" not in path.parts:
            yield path


def _layer(path: Path) -> str:
    return path.relative_to(PACKAGE_DIR).parts[0]


def _package_of(path: Path) -> list[str]:
    parts = list(path.relative_to(PACKAGE_DIR).with_suffix("").parts)
    return parts if path.name == "__init__.py" and parts[-1] == "__init__" and parts.pop() else parts[:-1]


def _imports(path: Path):
    """(módulo absoluto dentro do pacote | None, nome externo | None, linha)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = _package_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield from _classify(alias.name.split("."), node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                if node.level - 1 > len(package):
                    continue
                base = package[: len(package) - (node.level - 1)]
                module = base + (node.module.split(".") if node.module else [])
                yield ("internal", module, node.lineno, [a.name for a in node.names])
            elif node.module:
                yield from _classify(node.module.split("."), node.lineno,
                                     [a.name for a in node.names])


def _classify(parts, line, names=()):
    if parts[0] == "src" and len(parts) > 1 and parts[1] == PACKAGE:
        parts = parts[1:]
    if parts[0] == PACKAGE:
        yield ("internal", parts[1:], line, list(names))
    else:
        yield ("external", parts, line, list(names))


def _exists(module: list[str]) -> bool:
    target = PACKAGE_DIR.joinpath(*module) if module else PACKAGE_DIR
    return target.with_suffix(".py").is_file() or (target / "__init__.py").is_file() or target.is_dir()


def test_layers_do_not_import_forbidden_layers():
    problems = []
    for path in _modules():
        layer = _layer(path)
        for kind, module, line, _names in _imports(path):
            if kind == "internal" and module and module[0] in FORBIDDEN.get(layer, ()):
                key = (str(path.relative_to(PACKAGE_DIR)), ".".join(module))
                if key not in KNOWN_DEBT:
                    problems.append(f"{key[0]}:{line} ({layer}) importa {key[1]}")
            if kind == "external" and layer in NO_QT and module[0] in QT:
                key = (str(path.relative_to(PACKAGE_DIR)), module[0])
                if key not in KNOWN_DEBT:
                    problems.append(f"{key[0]}:{line} ({layer}) importa {module[0]}")
    assert not problems, "\n".join(problems)


def test_app_only_has_entry_point():
    extra = sorted(p.name for p in (PACKAGE_DIR / "app").glob("*.py") if p.name not in APP_ALLOWED)
    assert not extra, f"app/ deve conter só o ponto de entrada; mova: {extra}"


def test_internal_imports_resolve():
    broken = []
    for path in _modules():
        for kind, module, line, names in _imports(path):
            if kind != "internal":
                continue
            if _exists(module):
                continue
            broken.append(f"{path.relative_to(PACKAGE_DIR)}:{line} -> {'.'.join(module)}")
    assert not broken, "\n".join(broken)
