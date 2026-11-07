#!/usr/bin/env python3
"""Move os arquivos de `app/` para a camada certa e corrige os imports.

Uso (a partir da raiz do projeto):
    python tools/reorganize_project.py            # só mostra o plano (nada muda)
    python tools/reorganize_project.py --apply    # aplica

O que faz:
  * move cada arquivo da tabela MOVES (com `git mv` quando o projeto é git);
  * reescreve imports absolutos (`wuwa_calculator.app.X` e
    `src.wuwa_calculator.app.X`, mantendo o prefixo que cada arquivo usa) e
    imports relativos (recalculados a partir do novo local);
  * cria `__init__.py` nas pastas de destino que não tiverem;
  * lista referências que ele não conseguiu corrigir sozinho (scripts de
    build, .spec, docs, `from ..app import X`).

É idempotente: rodar de novo depois de aplicar não altera nada.
Só usa a biblioteca padrão.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

# origem -> destino, relativos à pasta do pacote (…/wuwa_calculator)
MOVES: dict[str, str] = {
    "app/security_policy.py": "infrastructure/security_policy.py",
    "app/banner_service.py": "infrastructure/banner_service.py",
    "app/native_engine.py": "infrastructure/native_engine.py",
    "app/dps_simulation_panel.py": "ui/panels/dps_simulation_panel.py",
    "app/history_video_player.py": "ui/panels/history_video_player.py",
    "app/pity_tracker.py": "ui/panels/pity_tracker.py",
    "app/review_support.py": "ui/review_support.py",
}

SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "build", "dist", "node_modules", ".mypy_cache"}
RELATIVE_IMPORT = re.compile(r"^(?P<indent>\s*)from\s+(?P<dots>\.+)(?P<module>[\w.]*)\s+import\s+(?P<rest>.*)$")


def dotted(path: str) -> str:
    return path[:-3].replace("/", ".")


MOVED = {dotted(old): dotted(new) for old, new in MOVES.items()}


def find_package(root: Path) -> Path:
    for candidate in (root / "src" / "wuwa_calculator", root / "wuwa_calculator"):
        if candidate.is_dir():
            return candidate
    raise SystemExit("Não achei a pasta wuwa_calculator (rode na raiz do projeto).")


def project_files(root: Path, suffixes: set[str]) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in suffixes and not (SKIP_DIRS & set(path.relative_to(root).parts)):
            files.append(path)
    return sorted(files)


def relative_to_package(path: Path, package: Path) -> list[str] | None:
    try:
        parts = list(path.relative_to(package).with_suffix("").parts)
    except ValueError:
        return None
    return parts


APP_PACKAGE_IMPORT = re.compile(
    r"^(?P<indent>\s*)from\s+(?P<mod>\.+app|\.+|(?:src\.)?wuwa_calculator\.app|(?:src\.)?wuwa_calculator)"
    r"\s+import\s+(?P<names>[^()#\n]+?)\s*$"
)


_DONE = ""


def _relative(new_pkg: list[str], target: list[str]) -> str:
    common = 0
    for a, b in zip(new_pkg, target):
        if a != b:
            break
        common += 1
    return "." * (len(new_pkg) - common + 1) + ".".join(target[common:])


def fix_package_imports(text: str, old_pkg: list[str] | None, new_pkg: list[str] | None) -> tuple[str, int]:
    """`from . import native_engine`, `from ...app import native_engine` e
    `from wuwa_calculator.app import native_engine`: o pacote não mudou, mas o
    NOME importado foi para outro pacote. Divide a linha, uma por destino."""
    changes = 0
    out = []
    for line in text.split("\n"):
        match = APP_PACKAGE_IMPORT.match(line)
        if not match:
            out.append(line)
            continue
        mod = match.group("mod")
        # pacote de onde os nomes são importados, em partes absolutas dentro do pacote
        if mod.startswith("."):
            dots = len(mod) - 3 if mod.endswith("app") else len(mod)
            if old_pkg is None or dots - 1 > len(old_pkg):
                out.append(line)
                continue
            base = old_pkg[: len(old_pkg) - (dots - 1)]
            package = base + (["app"] if mod.endswith("app") else [])
            style = "relative"
            prefix = ""
        else:
            prefix = mod[: -len(".app")] if mod.endswith(".app") else mod
            package = ["app"] if mod.endswith(".app") else []
            style = "absolute"
        if package != ["app"]:
            out.append(line)
            continue

        keep, moved = [], {}
        for item in (part.strip() for part in match.group("names").split(",")):
            name = item.split(" as ")[0].strip()
            target = MOVED.get(f"app.{name}")
            if target is None:
                keep.append(item)
                continue
            moved.setdefault(".".join(target.split(".")[:-1]), []).append(item)
        if not moved:
            out.append(line)
            continue

        indent = match.group("indent")
        if keep:
            # O que ficou em app/ continua em app/, mas o ARQUIVO pode ter mudado de pasta.
            if style == "relative" and new_pkg is not None:
                keep_from = _relative(new_pkg, ["app"])
            else:
                keep_from = mod
            out.append(f"{indent}from {keep_from} import {', '.join(keep)}{_DONE}")
        for package_path, items in moved.items():
            parts = package_path.split(".")
            if style == "relative" and new_pkg is not None:
                where = _relative(new_pkg, parts)
            elif style == "relative":
                where = "." + package_path
            else:
                where = f"{prefix}.{package_path}"
            out.append(f"{indent}from {where} import {', '.join(items)}{_DONE}")
        changes += 1
    return "\n".join(out), changes


def fix_text(text: str, old_parts: list[str] | None, new_parts: list[str] | None) -> tuple[str, int]:
    """Reescreve imports de um arquivo. `old_parts`/`new_parts`: caminho do
    módulo dentro do pacote antes/depois da mudança (None se fora do pacote)."""
    changes = 0

    def absolute(match: re.Match) -> str:
        nonlocal changes
        old = match.group("mod")
        if old not in MOVED:
            return match.group(0)
        changes += 1
        return f"{match.group('prefix')}.{MOVED[old]}"

    pattern = "|".join(re.escape(name) for name in sorted(MOVED, key=len, reverse=True))
    text = re.sub(rf"(?P<prefix>(?:src\.)?wuwa_calculator)\.(?P<mod>{pattern})\b", absolute, text)

    text, extra = fix_package_imports(
        text,
        old_parts[:-1] if old_parts is not None else None,
        new_parts[:-1] if new_parts is not None else None,
    )
    changes += extra

    if old_parts is None or new_parts is None:
        return text.replace(_DONE, ""), changes

    old_pkg, new_pkg = old_parts[:-1], new_parts[:-1]
    out = []
    for line in text.split("\n"):
        match = RELATIVE_IMPORT.match(line)
        if not match or line.endswith(_DONE):
            out.append(line)
            continue
        dots = len(match.group("dots"))
        if dots - 1 > len(old_pkg):
            out.append(line)
            continue
        base = old_pkg[: len(old_pkg) - (dots - 1)]
        module = match.group("module")
        target = base + (module.split(".") if module else [])
        mapped = MOVED.get(".".join(target))
        target_new = mapped.split(".") if mapped else target

        if target_new == target and old_pkg == new_pkg:
            out.append(line)
            continue

        common = 0
        for a, b in zip(new_pkg, target_new):
            if a != b:
                break
            common += 1
        new_dots = len(new_pkg) - common + 1
        rest = ".".join(target_new[common:])
        new_line = f"{match.group('indent')}from {'.' * new_dots}{rest} import {match.group('rest')}"
        if new_line != line:
            changes += 1
        out.append(new_line)
    return "\n".join(out).replace(_DONE, ""), changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    root = args.root.resolve()
    package = find_package(root)
    use_git = (root / ".git").exists() and shutil.which("git") is not None

    plan: list[tuple[Path, Path]] = []
    for old, new in MOVES.items():
        source, target = package / old, package / new
        if source.exists() and target.exists():
            raise SystemExit(f"Destino já existe: {target}")
        if source.exists():
            plan.append((source, target))
        elif not target.exists():
            print(f"  (ignorado, não existe) {old}")

    print("Movimentos:" if plan else "Nada a mover.")
    for source, target in plan:
        print(f"  {source.relative_to(package)}  ->  {target.relative_to(package)}")

    new_location = {source: target for source, target in plan}
    total_changes = 0
    rewrites: list[tuple[Path, str, int]] = []

    for path in project_files(root, {".py"}):
        old_parts = relative_to_package(path, package)
        target_path = new_location.get(path, path)
        new_parts = relative_to_package(target_path, package)
        original = path.read_text(encoding="utf-8")
        fixed, changes = fix_text(original, old_parts, new_parts)
        if changes or fixed != original:
            rewrites.append((path, fixed, changes))
            total_changes += changes

    print(f"\nImports a reescrever: {total_changes} em {len(rewrites)} arquivo(s)")
    for path, _, changes in rewrites:
        print(f"  {path.relative_to(root)}: {changes}")

    if not args.apply:
        print("\n(Simulação) Rode com --apply para executar.")
        return 0

    for path, fixed, _ in rewrites:
        path.write_text(fixed, encoding="utf-8")

    for source, target in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        init = target.parent / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
        done = False
        if use_git:
            done = subprocess.run(["git", "mv", str(source), str(target)], cwd=root,
                                  capture_output=True).returncode == 0
        if not done:
            shutil.move(str(source), str(target))

    # Referências que sobraram (fora dos .py ou em formas que não tratamos).
    leftovers = []
    names = [name.split(".")[-1] for name in MOVED]
    old_ref = re.compile(r"\bapp[./\\](?:" + "|".join(names) + r")\b|from\s+\.+app\s+import")
    for path in project_files(root, {".py", ".spec", ".toml", ".cfg", ".ini", ".txt", ".md", ".yml", ".yaml", ".json"}):
        if path.name == "reorganize_project.py":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if old_ref.search(line) and not re.search(r"app\s+import\s+main\b", line):
                leftovers.append(f"  {path.relative_to(root)}:{number}: {line.strip()}")
    if leftovers:
        print("\nConfira manualmente (referências ao local antigo):")
        print("\n".join(leftovers))
    else:
        print("\nSem referências antigas restantes.")
    print("\nPronto. Regenere o TETHYS_SHA256.txt e rode os testes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
