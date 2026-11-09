"""Check that multimedia starts on video selection rather than tab entry."""

import os
import subprocess
import sys
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal
from PySide6.QtWidgets import QApplication

from wuwa_calculator.ui.panels import history_video_player as player_module
from wuwa_calculator.ui.tabs.multimedia_tab import MultimediaTab


@pytest.fixture(name="media_tab")
def fixture_media_tab(monkeypatch):
    """Create the full tab without starting audio or media playback."""
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QT_QPA_PLATFORMTHEME", "")
    app = QApplication.instance() or QApplication([])
    tab = MultimediaTab()
    monkeypatch.setattr(tab.dps_panel, "_start_live_analysis", Mock())
    yield tab
    tab.close()
    app.processEvents()
    tab.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)


def test_tab_does_not_initialize_playback(media_tab, monkeypatch):
    """Navigation and empty controls must leave the backend uninitialized."""
    constructor = Mock(side_effect=AssertionError("Unexpected media backend"))
    monkeypatch.setattr(player_module, "_multimedia_types", constructor)
    player = media_tab.video_player
    media_tab.set_active(False)
    media_tab.set_active(True)
    player.toggle_playback()
    player.enter_fullscreen()
    player.stop_video()
    player.set_volume(25)
    player.set_playback_rate(1.5)
    assert not player.load_video("/missing/tethys-video.mp4")
    assert player.media_player is None
    assert player.audio_output is None
    assert player.fullscreen_overlay is None
    constructor.assert_not_called()


def test_video_load_initializes_once_and_relays_signals(
    media_tab, monkeypatch, tmp_path
):
    """Connect existing controls to the backend created for the first video."""

    class MediaSignals(QObject):
        """Supply Qt signals for the mocked playback backend."""

        positionChanged = Signal(int)
        durationChanged = Signal(int)
        playbackStateChanged = Signal(object)
        mediaStatusChanged = Signal(object)
        errorOccurred = Signal(object, str)
        tracksChanged = Signal()

    # Import native video types only for the test that actually loads a video.
    # pylint: disable=import-outside-toplevel
    from PySide6.QtMultimedia import QMediaPlayer
    from PySide6.QtMultimediaWidgets import QVideoWidget

    signals = MediaSignals()
    backend = Mock()
    for name in (
        "positionChanged",
        "durationChanged",
        "playbackStateChanged",
        "mediaStatusChanged",
        "errorOccurred",
        "tracksChanged",
    ):
        setattr(backend, name, getattr(signals, name))
    backend.position.return_value = 0
    backend.PlaybackState = QMediaPlayer.PlaybackState
    backend.playbackState.return_value = (
        QMediaPlayer.PlaybackState.PlayingState
    )
    constructor = Mock(return_value=backend)
    audio = Mock()
    monkeypatch.setattr(
        player_module,
        "_multimedia_types",
        Mock(
            return_value=(constructor, Mock(return_value=audio), QVideoWidget)
        ),
    )
    player = media_tab.video_player
    player.volume_slider.setValue(35)
    player.set_playback_rate(1.5)
    positions = []
    player.positionChanged.connect(positions.append)
    video = tmp_path / "video.mp4"
    video.touch()
    assert player.load_video(str(video))
    assert isinstance(player.video_surface, QVideoWidget)
    assert player.hud_label.parent() is player.video_surface
    assert player.fullscreen_overlay is None
    audio.setVolume.assert_called_once_with(0.35)
    backend.setPlaybackRate.assert_called_once_with(1.5)
    backend.setVideoOutput.assert_called_once_with(player.video_surface)
    signals.durationChanged.emit(10000)
    signals.positionChanged.emit(2000)
    assert player.duration_ms == 10000
    assert positions == [2000]
    assert media_tab.info_panel.duration_value.text() == "0:10"
    assert player.load_video(str(video))
    constructor.assert_called_once_with(player)
    assert backend.play.call_count == 2

    signals.durationChanged.emit(10000)
    signals.positionChanged.emit(2000)
    _check_fullscreen_controls(player, backend, audio)


def _check_fullscreen_controls(player, backend, audio):
    """Check lazy fullscreen creation, controls, and reuse after exit."""
    player.enter_fullscreen()
    overlay = player.fullscreen_overlay
    assert overlay is not None
    assert player.fullscreen_progress.maximum() == 10000
    assert player.fullscreen_progress.value() == 2000
    assert player.fullscreen_time_label.text() == player.time_label.text()
    assert player.fullscreen_volume.value() == 35
    player.fullscreen_volume.setValue(60)
    assert player.volume_slider.value() == 60
    audio.setVolume.assert_called_with(0.6)
    player.fullscreen_progress.sliderMoved.emit(5000)
    backend.setPosition.assert_called_with(5000)
    player.fullscreen_play_button.click()
    backend.pause.assert_called_once()
    player.fullscreen_exit_button.click()
    player.enter_fullscreen()
    assert player.fullscreen_overlay is overlay
    player.stop_video()
    assert player.fullscreen_progress.value() == 0
    assert player.fullscreen_progress.maximum() == 0
    assert not player.fullscreen_play_button.isEnabled()


def test_tab_opens_without_plotting_imports():
    """Keep the plotting dependency out of the first navigation path."""
    env = os.environ.copy()
    env.update(QT_QPA_PLATFORM="offscreen", QT_QPA_PLATFORMTHEME="")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; "
            "from PySide6.QtWidgets import QApplication; "
            "from wuwa_calculator.ui.tabs.multimedia_tab "
            "import MultimediaTab; "
            "app = QApplication([]); tab = MultimediaTab(); "
            "tab.show(); app.processEvents(); "
            "tab.set_active(False); tab.set_active(True); "
            "assert tab.dps_panel.plot is None; "
            "assert 'pyqtgraph' not in sys.modules; "
            "assert 'numpy' not in sys.modules; "
            "assert 'PySide6.QtMultimedia' not in sys.modules; "
            "assert 'PySide6.QtMultimediaWidgets' not in sys.modules; "
            "assert tab.video_player.fullscreen_overlay is None; tab.close()",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr


def test_plot_is_created_once_when_results_arrive(media_tab):
    """Build timelines on demand and retain them when clearing results."""
    panel = media_tab.dps_panel
    assert panel.plot is None
    # pylint: disable=protected-access
    panel._on_analysis_completed(
        {
            "last_hit": 2.0,
            "total_hits": 1,
            "total_damage": 749,
            "events": [{"timestamp": 2.0, "damage": 749}],
            "duration": 3.0,
        }
    )
    plot = panel.plot
    assert plot is not None
    assert panel._plot_placeholder.isHidden()
    panel._flush_plot_update()
    assert panel.curve.getData()[1][-1] == 749 / 5.0
    panel._on_duration_changed(3000)
    panel._render_curve()
    assert panel.plot is plot
