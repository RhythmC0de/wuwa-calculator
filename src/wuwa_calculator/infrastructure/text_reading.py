"""Read image text with the native engine in a fresh process, without Qt.

Same isolation used by ``video_analysis``: the engine's native libraries
(ONNX Runtime, OpenCV) never share a process with Qt or the other Python
packages the interface loads.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DEFAULT_TIMEOUT_SECONDS = 90.0


class EngineUnavailableError(RuntimeError):
    """The native engine or its text model is not usable in this setup."""


def read_lines_isolated(
    image: str | Path,
    *,
    enhance: bool = False,
    boxes: list[list[int]] | None = None,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> list[dict]:
    """Return ``[{text, confidence, x, y, width, height}, ...]``.

    ``boxes`` (``[x, y, width, height]`` each) skips the detector and only
    recognizes the text inside them.

    Raises ``EngineUnavailableError`` when the engine, its ``read_text`` or
    the detection model is missing, and ``RuntimeError`` for other failures.
    """
    with tempfile.TemporaryDirectory(prefix="tethys-ocr-") as directory:
        output = Path(directory) / "lines.json"
        env = os.environ.copy()
        source = str(Path(__file__).resolve().parents[2])
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, (source, env.get("PYTHONPATH")))
        )
        command = [
            sys.executable,
            "-m",
            "wuwa_calculator.infrastructure.text_reading",
            str(Path(image).resolve()),
            "1" if enhance else "0",
            json.dumps(boxes or []),
            str(output),
        ]
        try:
            completed = subprocess.run(
                command,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError(
                f"Leitura de texto excedeu {timeout:.0f}s"
            ) from error

        message = completed.stderr.decode("utf-8", "replace")[-4000:]
        if completed.returncode == EXIT_UNAVAILABLE:
            raise EngineUnavailableError(message.strip())
        if completed.returncode != 0:
            raise RuntimeError(
                f"Processo de leitura encerrou com código "
                f"{completed.returncode}: {message}"
            )
        return json.loads(output.read_text(encoding="utf-8"))


EXIT_UNAVAILABLE = 3
REQUIRED_API_LEVEL = 4


def main() -> None:
    """Run the text-reading command-line entry point."""
    # Load the engine only in this process.
    # pylint: disable-next=import-outside-toplevel
    from wuwa_calculator.infrastructure.native_engine import load_engine

    image, enhance, boxes, output = sys.argv[1:]
    try:
        engine = load_engine()
    except ImportError as error:
        print(f"engine indisponível: {error}", file=sys.stderr)
        sys.exit(EXIT_UNAVAILABLE)
    if getattr(engine, "API_LEVEL", 0) < REQUIRED_API_LEVEL or not hasattr(
        engine, "read_text"
    ):
        print(
            "engine sem read_text (API_LEVEL >= 4); recompile "
            "native/damage_analyzer",
            file=sys.stderr,
        )
        sys.exit(EXIT_UNAVAILABLE)

    try:
        lines = engine.read_text(
            image,
            boxes=[list(map(int, box)) for box in json.loads(boxes)],
            enhance=enhance == "1",
        )
    except RuntimeError as error:
        # Modelo de detecção ausente ou imagem ilegível.
        print(str(error), file=sys.stderr)
        sys.exit(EXIT_UNAVAILABLE if "model not found" in str(error) else 1)

    data = [
        {
            "text": line.text,
            "confidence": float(line.confidence),
            "x": float(line.x),
            "y": float(line.y),
            "width": float(line.width),
            "height": float(line.height),
        }
        for line in lines
    ]
    Path(output).write_text(
        json.dumps(data, allow_nan=False), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
