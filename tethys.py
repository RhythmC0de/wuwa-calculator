"""Launcher: puts ``src`` on sys.path explicitly, then starts the app."""

import sys
from importlib import import_module
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

main = import_module("wuwa_calculator.app.main").main

if __name__ == "__main__":
    raise SystemExit(main())
