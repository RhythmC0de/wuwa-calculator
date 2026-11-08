"""Integration checks for native analysis outside the Qt process."""

import time
import unittest
from pathlib import Path
from unittest.mock import patch

from wuwa_calculator.infrastructure import video_analysis

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(
    (ROOT / "test/cobaia.mp4").is_file(), "reference video unavailable"
)
class IsolatedVideoAnalysisTest(unittest.TestCase):
    """Check native video analysis in a separate process."""

    def test_reference_segment_preserves_native_events_and_totals(self):
        """Verify reference segment preserves native events and totals."""
        result = video_analysis.analyze_isolated(
            str(ROOT / "test/cobaia.mp4"), 15.0, 18.0, lambda: False
        )
        self.assertEqual(result["total_hits"], 41)
        self.assertEqual(len(result["events"]), 41)
        self.assertEqual(result["total_damage"], 102210.0)
        self.assertEqual(
            result["total_damage"], sum(e["damage"] for e in result["events"])
        )

    def test_cancel_reaps_child(self):
        """Verify cancel reaps child."""
        processes = []
        original = video_analysis.subprocess.Popen

        def launch(*args, **kwargs):
            # The parent analyzer owns and reaps the process returned here.
            # pylint: disable-next=consider-using-with
            process = original(*args, **kwargs)
            processes.append(process)
            return process

        started = time.monotonic()
        with patch.object(
            video_analysis.subprocess, "Popen", side_effect=launch
        ):
            result = video_analysis.analyze_isolated(
                str(ROOT / "test/cobaia.mp4"),
                0.0,
                -1.0,
                lambda: time.monotonic() - started > 0.3,
            )
        self.assertIsNone(result)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())

    def test_native_error_reaches_parent(self):
        """Verify native error reaches parent."""
        with self.assertRaisesRegex(RuntimeError, "Could not open video"):
            video_analysis.analyze_isolated(
                str(ROOT / "test/does-not-exist.mp4"), 0.0, -1.0, lambda: False
            )


if __name__ == "__main__":
    unittest.main()
