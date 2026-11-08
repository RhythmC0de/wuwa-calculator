"""Execute native video analysis in a fresh process, without importing Qt."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable

STATS = (
    "frames_read", "frames_analyzed", "candidates_detected",
    "candidates_rejected_hud", "candidates_rejected_geometry",
    "candidates_passed_filters", "ocr_calls", "ocr_no_numeric_result",
    "ocr_rejected_confidence", "ocr_ignored_countdown", "ocr_below_min_damage",
)


def analyze_isolated(video: str, start: float, end: float,
                     cancelled: Callable[[], bool]) -> dict | None:
    """Return native events and totals; cancellation reaps the child process."""
    if cancelled():
        return None
    with tempfile.TemporaryDirectory(prefix="tethys-analysis-") as directory:
        output = Path(directory) / "result.json"
        env = os.environ.copy()
        source = str(Path(__file__).resolve().parents[2])
        env["PYTHONPATH"] = os.pathsep.join(filter(None, (source, env.get("PYTHONPATH"))))
        command = [sys.executable, "-m", "wuwa_calculator.infrastructure.video_analysis",
                   str(Path(video).resolve()), str(start), str(end), str(output)]
        # File-backed stderr cannot fill a pipe and deadlock the analysis.
        with (Path(directory) / "stderr.log").open("w+", encoding="utf-8") as errors:
            process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.DEVNULL, stderr=errors)
            try:
                while True:
                    if cancelled():
                        return None
                    try:
                        code = process.wait(timeout=0.1)
                        break
                    except subprocess.TimeoutExpired:
                        pass
                if cancelled():
                    return None
                if code != 0:
                    errors.seek(0)
                    raise RuntimeError(f"Processo de análise encerrou com código {code}: "
                                       + errors.read()[-8000:])
                return json.loads(output.read_text(encoding="utf-8"))
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()


def main() -> None:
    from wuwa_calculator.infrastructure.native_engine import load_engine

    video, start, end, output = sys.argv[1:]
    engine = load_engine()
    config = engine.AnalyzerConfig()
    config.verbose = False
    result = engine.analyze_video(video, float(start), float(end), config)
    events = [{"timestamp": float(e.timestamp), "damage": float(e.damage)}
              for e in sorted(result.events, key=lambda e: float(e.timestamp))]
    data = {name: int(getattr(result, name, 0)) for name in STATS}
    data.update(reason="native_complete", events=events,
                last_hit=max((e["timestamp"] for e in events), default=-1.0),
                total_damage=float(result.total_damage), total_hits=int(result.total_hits),
                peak_damage=float(result.peak_damage), duration=float(result.duration),
                engine_path=str(engine.__file__), python_path=sys.executable)
    Path(output).write_text(json.dumps(data, allow_nan=False), encoding="utf-8")


if __name__ == "__main__":
    main()
