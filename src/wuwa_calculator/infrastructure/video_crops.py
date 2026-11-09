"""Extract review images in a fresh process without Qt libraries."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def extract_crops_isolated(
    video: str,
    events: list[dict],
    padding: float = 0.6,
    offsets: list[float] | None = None,
    min_height: int = 96,
) -> list[list[bytes]]:
    """Return PNG crops without loading the native engine into Qt."""
    with tempfile.TemporaryDirectory(prefix="tethys-crops-") as directory:
        request = Path(directory) / "request.json"
        output = Path(directory) / "crops.json"
        request.write_text(
            json.dumps(
                {
                    "video": str(Path(video).resolve()),
                    "events": events,
                    "padding": padding,
                    "offsets": offsets if offsets is not None else [0.0],
                    "min_height": min_height,
                },
                allow_nan=False,
            ),
            encoding="utf-8",
        )
        env = os.environ.copy()
        source = str(Path(__file__).resolve().parents[2])
        env["PYTHONPATH"] = os.pathsep.join(
            filter(None, (source, env.get("PYTHONPATH")))
        )
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "wuwa_calculator.infrastructure.video_crops",
                    str(request),
                    str(output),
                ],
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=90,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise RuntimeError("Extração de recortes excedeu 90s") from error
        if result.returncode:
            message = result.stderr.decode("utf-8", "replace")[-4000:]
            raise RuntimeError(f"Falha na extração de recortes: {message}")
        return [
            [base64.b64decode(image) for image in images]
            for images in json.loads(output.read_text(encoding="utf-8"))
        ]


def main() -> None:
    """Run crop extraction in the isolated native process."""
    # The native engine must load before any Qt multimedia library.
    # pylint: disable-next=import-outside-toplevel
    from wuwa_calculator.infrastructure.native_engine import load_engine

    request, output = sys.argv[1:]
    data = json.loads(Path(request).read_text(encoding="utf-8"))
    engine = load_engine()
    crops = engine.extract_event_crops(
        data["video"],
        data["events"],
        data["padding"],
        data["offsets"],
        data["min_height"],
    )
    encoded = [
        [base64.b64encode(image).decode("ascii") for image in images]
        for images in crops
    ]
    Path(output).write_text(json.dumps(encoded), encoding="utf-8")


if __name__ == "__main__":
    main()
