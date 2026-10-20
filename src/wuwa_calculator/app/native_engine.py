"""Localização e carregamento da engine C++ ``damage_analyzer``.

Único ponto do aplicativo que sabe onde a extensão compilada fica, em
Windows e Linux. Os workers de análise só chamam :func:`load_engine`.

A engine é procurada, nesta ordem, em:

1. a variável de ambiente ``DAMAGE_ANALYZER_DIR``;
2. ``native/damage_analyzer/build`` (e subpastas ``Release``/``Debug``…)
   subindo a partir deste arquivo;
3. o ``sys.path`` normal do Python.

``DAMAGE_ANALYZER_DIR`` só é considerada com ``TETHYS_DEBUG=1``.
"""

from __future__ import annotations

import importlib
import importlib.machinery
import importlib.util
import os
import sys
import threading
from pathlib import Path
from types import ModuleType

# Versão mínima da API nativa (campo ``API_LEVEL`` do módulo). O nível 2 traz
# AnalyzerConfig, CancelToken e as estatísticas do pipeline.
REQUIRED_API_LEVEL = 2

_MODULE_NAME = "damage_analyzer"
_BUILD_SUBDIRS = ("build", "build/Release", "build/RelWithDebInfo", "build/Debug", "")
_NATIVE_BASES = (
    Path("native") / "damage_analyzer",
    Path("wuwa_calculator") / "native" / "damage_analyzer",
    Path("src") / "wuwa_calculator" / "native" / "damage_analyzer",
)

_engine: ModuleType | None = None
_load_lock = threading.Lock()
_dll_directories: list[object] = []


def _candidate_directories() -> list[Path]:
    directories: list[Path] = []

    # Carregar .so/.pyd de uma pasta arbitrária equivale a executar código:
    # o override por ambiente só vale em modo debug.
    configured = os.environ.get("DAMAGE_ANALYZER_DIR") if os.environ.get("TETHYS_DEBUG") == "1" else None
    if configured:
        directories.append(Path(configured))

    for parent in Path(__file__).resolve().parents:
        for base in _NATIVE_BASES:
            for sub in _BUILD_SUBDIRS:
                directories.append(parent / base / sub if sub else parent / base)

    unique: list[Path] = []
    for directory in directories:
        if directory not in unique:
            unique.append(directory)
    return unique


def _module_files(directory: Path) -> list[Path]:
    """Binários ``damage_analyzer*`` presentes na pasta (qualquer versão do Python)."""
    if not directory.is_dir():
        return []
    return [
        item for item in directory.iterdir()
        if item.is_file()
        and item.name.startswith(_MODULE_NAME)
        and item.suffix in {".so", ".pyd"}
    ]


def _matches_this_python(path: Path) -> bool:
    return any(path.name == _MODULE_NAME + suffix for suffix in importlib.machinery.EXTENSION_SUFFIXES)


def _register_directory(directory: Path) -> None:
    text = str(directory.resolve())
    # Python 3.8+ no Windows não usa o PATH para achar DLLs de dependência.
    if os.name == "nt" and hasattr(os, "add_dll_directory"):
        try:
            _dll_directories.append(os.add_dll_directory(text))
        except OSError:
            pass


def load_engine() -> ModuleType:
    """Importa (uma única vez) e devolve o módulo ``damage_analyzer``."""
    with _load_lock:
        return _load_engine_locked()


def _load_engine_locked() -> ModuleType:
    global _engine
    if _engine is not None:
        return _engine

    searched: list[str] = []
    wrong_python: list[Path] = []
    chosen: Path | None = None

    for directory in _candidate_directories():
        files = _module_files(directory)
        if not files:
            continue
        searched.append(str(directory))
        match = next((item for item in files if _matches_this_python(item)), None)
        if match is not None:
            _register_directory(directory)
            chosen = match
            break
        wrong_python.extend(files)

    try:
        if chosen is not None:
            # Carrega exatamente o binário encontrado, sem alterar o sys.path.
            spec = importlib.util.spec_from_file_location(_MODULE_NAME, chosen)
            if spec is None or spec.loader is None:
                raise ImportError(f"spec inválido para {chosen}")
            module = importlib.util.module_from_spec(spec)
            sys.modules[_MODULE_NAME] = module
            spec.loader.exec_module(module)
        else:
            module = importlib.import_module(_MODULE_NAME)
    except ImportError as error:
        sys.modules.pop(_MODULE_NAME, None)
        lines = [
            "Não foi possível carregar a engine C++ 'damage_analyzer'.",
            f"Python em uso: {sys.version_info.major}.{sys.version_info.minor} "
            f"({importlib.machinery.EXTENSION_SUFFIXES[0]}).",
        ]
        if wrong_python:
            lines.append(
                "Foi encontrada uma build para outra versão do Python: "
                + ", ".join(item.name for item in wrong_python)
                + ". Recompile com -DPython_EXECUTABLE=<este python>."
            )
        elif not searched:
            lines.append(
                "Nenhum binário damage_analyzer*.so/.pyd foi encontrado. "
                "Compile em native/damage_analyzer/build (veja o README) "
                "ou defina DAMAGE_ANALYZER_DIR."
            )
        lines.append(f"Erro original: {error}")
        raise ImportError("\n".join(lines)) from error

    if getattr(module, "API_LEVEL", 0) < REQUIRED_API_LEVEL:
        sys.modules.pop(_MODULE_NAME, None)
        raise ImportError(
            "A engine em "
            f"{getattr(module, '__file__', '?')} é de uma build antiga "
            f"(API_LEVEL {getattr(module, 'API_LEVEL', 0)}, necessário "
            f"{REQUIRED_API_LEVEL}). Recompile native/damage_analyzer."
        )

    _engine = module
    return module