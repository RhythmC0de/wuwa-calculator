"""Exercise mode selection and native event delivery to human review."""

from unittest.mock import Mock

import pytest
from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QApplication, QWidget

from wuwa_calculator.domain.review import ReviewMode, correct
from wuwa_calculator.infrastructure import video_analysis
from wuwa_calculator.ui import review_support
from wuwa_calculator.ui.panels.dps_simulation_panel import DpsSimulationPanel
from wuwa_calculator.ui.workers.video_analysis_worker import (
    LiveDamageAnalysisWorker,
)


@pytest.fixture(name="review_panel")
def fixture_review_panel(monkeypatch, tmp_path):
    """Build real controls without native playback or user preferences."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QT_QPA_PLATFORMTHEME", "")
    monkeypatch.setenv("QT_STYLE_OVERRIDE", "Fusion")
    app = QApplication.instance() or QApplication([])
    settings = QSettings(
        str(tmp_path / "review.ini"), QSettings.Format.IniFormat
    )
    monkeypatch.setattr(review_support, "QSettings", lambda *_: settings)

    class Media(QObject):
        """Emit playback events without loading native multimedia."""

        positionChanged = Signal(int)
        durationChanged = Signal(int)

    class Player(QWidget):
        """Provide the panel's video player interface."""

        videoLoaded = Signal(str)
        videoStopped = Signal()

        def __init__(self):
            super().__init__()
            self.media_player = Media(self)

    player = Player()
    panel = DpsSimulationPanel(player)
    yield panel
    panel.close()
    panel.deleteLater()
    player.deleteLater()
    app.processEvents()


def test_mode_selector_and_corrected_totals(review_panel, monkeypatch):
    """Keep pending events available and apply user corrections to totals."""
    support = review_panel.review_support
    prepare = Mock()
    monkeypatch.setattr(support, "_ensure_crops_then", prepare)
    # Drive the result slot as the worker does, with JSON-compatible events.
    review_panel._on_analysis_completed(  # pylint: disable=protected-access
        {
            "events": [
                {"timestamp": 1.0, "damage": 1000, "confirmed": True},
                {"timestamp": 2.0, "damage": 782518, "confirmed": False},
            ],
            "last_hit": 2.0,
            "total_hits": 1,
            "total_damage": 1000,
            "peak_damage": 1000,
            "duration": 3.0,
            "video_path": "video.mp4",
        }
    )
    assert support.mode_combo.count() == 2
    assert support.mode_combo.isEnabled()
    assert review_panel.damage_metric.text() == "Dano acumulado: 1,000"
    support.mode_combo.setCurrentIndex(
        support.mode_combo.findData(ReviewMode.REVIEW.value)
    )
    assert support.mode is ReviewMode.REVIEW
    assert not support.review_button.isHidden()
    prepare.assert_called_once()
    # Simulate a completed dialog decision, then exercise its result signals.
    # pylint: disable=protected-access
    support._decisions[1] = correct(support._events[1], [(785, 1), (2518, 1)])
    support._apply(open_dialog=False)
    assert review_panel.damage_metric.text() == "Dano acumulado: 4,303"
    assert review_panel.hits_metric.text() == "Hits: 3"
    support.mode_combo.setCurrentIndex(0)
    assert review_panel.damage_metric.text() == "Dano acumulado: 1,000"


def test_worker_preserves_review_events(monkeypatch):
    """Retain confirmation flags and video path in the completion signal."""
    event = {"timestamp": 2.0, "damage": 123, "confirmed": False}
    monkeypatch.setattr(
        video_analysis,
        "analyze_isolated",
        lambda *_args: {"events": [event], "total_hits": 0},
    )
    worker = LiveDamageAnalysisWorker("video.mp4", 0)
    results = []
    worker.analysis_completed.connect(results.append)
    worker.run()
    assert results[0]["events"] == [event]
    assert results[0]["video_path"] == "video.mp4"


def test_failed_frames_preserve_error_and_allow_retry(review_panel):
    """Keep failed image extraction recoverable without opening the dialog."""
    support = review_panel.review_support
    callback = Mock()
    # Exercise the worker failure and completion slots in delivery order.
    # pylint: disable=protected-access
    support._pending_callback = callback
    support._on_crops_failed("decoder failed")
    support._on_crops_thread_finished()
    callback.assert_not_called()
    assert not support._crops_attempted
    assert support.review_button.isEnabled()
    assert "tentar novamente" in support.note_label.text()
    assert support.note_label.toolTip() == "decoder failed"


def test_empty_frames_are_not_marked_ready(review_panel):
    """Reject empty PNG results rather than treating them as loaded frames."""
    support = review_panel.review_support
    # pylint: disable=protected-access
    support._events = [review_support.HitEvent(0, 1.0, 123, confirmed=False)]
    callback = Mock()
    support._pending_callback = callback
    support._on_crops_ready({0: [b"", b"", b""]})
    support._on_crops_thread_finished()
    callback.assert_not_called()
    assert not support._crops_attempted
    assert "sem frame" in support.note_label.toolTip()


def test_review_dialog_displays_decoded_png(review_panel):
    """Render real PNG bytes in the review dialog before asking for input."""
    # pylint: disable=import-outside-toplevel
    from PySide6.QtCore import QBuffer, QIODevice, Qt
    from PySide6.QtGui import QPixmap
    from wuwa_calculator.ui.dialogs.damage_review_dialog import (
        DamageReviewDialog,
    )

    image = QPixmap(120, 60)
    image.fill(Qt.GlobalColor.yellow)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    event = review_support.HitEvent(0, 1.0, 123, confirmed=False)
    dialog = DamageReviewDialog(
        [event], {0: [bytes(buffer.data())]}, review_panel
    )
    label = dialog.images_row.itemAt(0).widget()
    assert not label.pixmap().isNull()
    assert label.pixmap().toImage().pixelColor(0, 0) == Qt.GlobalColor.yellow
    dialog.close()
    dialog.deleteLater()


def test_crop_worker_preserves_integer_keys_across_threads(review_panel):
    """Transport indexed PNG images through Qt without QVariantMap loss."""
    # pylint: disable=import-outside-toplevel
    from PySide6.QtCore import QEventLoop, QTimer

    support = review_panel.review_support
    # pylint: disable=protected-access
    support._events = [review_support.HitEvent(7, 1.0, 123, confirmed=False)]
    support._raw_events = [{}] * 8
    support._video_path = "video.mp4"
    support._extract = lambda *_args: [[b"png-data"]]
    loop = QEventLoop()
    callback = Mock(side_effect=loop.quit)
    support._ensure_crops_then(callback)
    timer = QTimer()
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(3000)
    loop.exec()
    timer.stop()
    callback.assert_called_once()
    assert support._crops == {7: [b"png-data"]}
    assert not support._crop_error
