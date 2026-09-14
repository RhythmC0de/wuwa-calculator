"""Player nativo QtMultimedia para a tela de histórico de rotações.

English: Native QtMultimedia player for the rotation history screen.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, QUrl
from PySide6.QtGui import QResizeEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider, QStyle,
    QVBoxLayout,
    QWidget,
)

# Allow direct execution from the app/ directory while keeping package imports
# as the canonical path used by the Tethys launcher.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.components import Card, TitleLabel


class ClickableSeekSlider(QSlider):
    """Barra de busca com suporte a arraste e clique direto na posição.

    English: Seek bar that supports both dragging and direct position clicks.
    """

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.maximum() > self.minimum():
            value = QStyle.sliderValueFromPosition(
                self.minimum(),
                self.maximum(),
                event.position().x(),
                max(1, self.width()),
            )
            self.sliderPressed.emit()
            self.setValue(value)
            self.sliderMoved.emit(value)
            self.sliderReleased.emit()
            event.accept()
            return
        super().mousePressEvent(event)


class HistoryVideoPlayer(Card):
    """Player local incorporável baseado exclusivamente em QtMultimedia.

    English: Embeddable local player backed exclusively by QtMultimedia.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_path = ""
        self.duration_ms = 0
        self.is_dragging = False

        self.media_player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.media_player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.title_label = TitleLabel("")
        header.addWidget(self.title_label)
        self.status_label = QLabel("PRONTO PARA MÍDIA LOCAL")
        self.status_label.setObjectName("muted")
        header.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)

        self.video_surface = QVideoWidget(self)
        self.video_surface.setObjectName("videoSurface")
        self.video_surface.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.media_player.setVideoOutput(self.video_surface)
        layout.addWidget(self.video_surface, 1)

        self.progress_slider = ClickableSeekSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("playerProgress")
        self.progress_slider.setRange(0, 0)
        layout.addWidget(self.progress_slider)

        controls = QHBoxLayout()
        controls.setSpacing(7)
        self.browse_button = self._button("Selecionar Vídeo")
        self.play_button = self._button("Play")
        self.stop_button = self._button("Parar")
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.browse_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.stop_button)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("muted")
        controls.addWidget(self.time_label)
        controls.addStretch(1)

        controls.addWidget(QLabel("Volume"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("playerVolume")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(110)
        controls.addWidget(self.volume_slider)

        self.subtitle_box = QComboBox()
        self.subtitle_box.setObjectName("playerSubtitles")
        self.subtitle_box.addItem("Legendas desativadas", -1)
        controls.addWidget(self.subtitle_box)
        layout.addLayout(controls)

    @staticmethod
    def _button(text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("playerButton")
        return button

    def _connect_signals(self) -> None:
        self.browse_button.clicked.connect(self.choose_video)
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop_video)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.progress_slider.sliderPressed.connect(self._begin_seek)
        self.progress_slider.sliderMoved.connect(self._preview_seek)
        self.progress_slider.sliderReleased.connect(self._commit_seek)
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.media_player.errorOccurred.connect(self._on_error)
        self.media_player.tracksChanged.connect(self._populate_subtitles)
        self.subtitle_box.currentIndexChanged.connect(self._select_subtitle)

    def choose_video(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar vídeo de referência",
            "",
            "Vídeos (*.mp4 *.mkv *.avi *.mov *.webm);;Todos os arquivos (*)",
        )
        if path:
            self.load_video(path)

    def load_video(self, path: str) -> bool:
        if not os.path.isfile(path):
            self._set_status("Arquivo de vídeo não encontrado")
            return False
        self.stop_video()
        self.video_path = str(Path(path).resolve())
        self.title_label.setText(Path(path).name)
        self._set_status(f"Carregando: {Path(path).name}")
        self._set_controls_enabled(True)
        self.media_player.setSource(QUrl.fromLocalFile(self.video_path))
        self.media_player.play()
        return True

    def toggle_playback(self) -> None:
        if not self.video_path:
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_video(self) -> None:
        self.media_player.stop()
        self.video_path = ""
        self.title_label.setText("")
        self.duration_ms = 0
        self.is_dragging = False
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self.play_button.setText("Play")
        self._set_controls_enabled(False)
        self._reset_subtitles()

    def set_volume(self, value: int) -> None:
        self.audio_output.setVolume(max(0, min(100, int(value))) / 100.0)

    def _begin_seek(self) -> None:
        self.is_dragging = True

    def _preview_seek(self, value: int) -> None:
        self.time_label.setText(f"{self._clock(value)} / {self._clock(self.duration_ms)}")

    def _commit_seek(self) -> None:
        if self.duration_ms > 0:
            self.media_player.setPosition(self.progress_slider.value())
        self.is_dragging = False

    def _on_position_changed(self, position_ms: int) -> None:
        if not self.is_dragging and not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position_ms)
            self.time_label.setText(f"{self._clock(position_ms)} / {self._clock(self.duration_ms)}")

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.duration_ms = max(0, int(duration_ms))
        self.progress_slider.setRange(0, self.duration_ms)
        self.time_label.setText(f"{self._clock(self.media_player.position())} / {self._clock(self.duration_ms)}")

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        paused = state == QMediaPlayer.PlaybackState.PausedState
        self.play_button.setText("Pausar" if playing else "Continuar")
        if paused:
            self._set_status("Pausado")
        elif playing:
            self._set_status("Reproduzindo")

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_button.setText("Play")
        elif status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._set_status("Arquivo de mídia inválido")

    def _on_error(self, _error: QMediaPlayer.Error, message: str) -> None:
        self._set_status(message or "Falha ao reproduzir mídia")

    def _populate_subtitles(self) -> None:
        tracks = self.media_player.subtitleTracks()
        with QSignalBlocker(self.subtitle_box):
            self.subtitle_box.clear()
            self.subtitle_box.addItem("Legendas desativadas", -1)
            for index, track in enumerate(tracks):
                description = track.stringValue(track.Key.Title) or f"Legenda {index + 1}"
                self.subtitle_box.addItem(description, index)

    def _select_subtitle(self, index: int) -> None:
        track_index = self.subtitle_box.itemData(index)
        if track_index is not None:
            self.media_player.setActiveSubtitleTrack(int(track_index))

    def _reset_subtitles(self) -> None:
        with QSignalBlocker(self.subtitle_box):
            self.subtitle_box.clear()
            self.subtitle_box.addItem("Legendas desativadas", -1)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.play_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    @staticmethod
    def _clock(milliseconds: int) -> str:
        total = max(0, int(milliseconds / 1000))
        return f"{total // 60}:{total % 60:02d}"

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self.video_surface.update()

    def closeEvent(self, event) -> None:
        self.stop_video()
        super().closeEvent(event)
