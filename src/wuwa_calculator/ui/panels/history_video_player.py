"""Player nativo QtMultimedia para a tela de histórico de rotações.

English: Native QtMultimedia player for the rotation history screen.
"""

from __future__ import annotations

import os
import sys
from importlib import import_module
from pathlib import Path

from PySide6.QtCore import QEvent, QSignalBlocker, QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider, QStyle,
    QVBoxLayout,
    QWidget,
)

# Allow direct execution from the app/ directory while keeping package imports
# as the canonical path used by the Tethys launcher.

from wuwa_calculator.ui.components.components import Card, TitleLabel


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


# [EXTRAIR] Integração de infraestrutura, não responsabilidade do widget.
# Este worker pode ser movido para services/native_analysis_worker.py quando
# a arquitetura de serviços do projeto estiver pronta.
class _NativeAnalysisThread(QThread):
    completed = Signal(object)
    failed = Signal(str)

    def __init__(self, video_path: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_path = video_path
        self._cancel_token = None
        self._cancel_requested = False

    def cancel(self) -> None:
        """Pede à engine que pare no próximo frame (seguro entre threads)."""
        self._cancel_requested = True
        token = self._cancel_token
        if token is not None:
            token.cancel()

    def run(self) -> None:
        try:
            # O localizador procura a extensão compilada em Windows e Linux
            # (native/damage_analyzer/build) sem depender de PYTHONPATH.
            try:
                from ...app import native_engine
            except ImportError:
                import native_engine  # type: ignore[no-redef]

            damage_analyzer = native_engine.load_engine()

            config = damage_analyzer.AnalyzerConfig()
            # A engine resolve os modelos padrão quando esses campos ficam
            # vazios. Não duplicamos em Python a lógica de localização dos
            # modelos nem os algoritmos de processamento da engine.
            config.model_path = ""
            config.dictionary_path = ""
            self._cancel_token = damage_analyzer.CancelToken()
            config.cancel_token = self._cancel_token
            if self._cancel_requested:
                return

            result = damage_analyzer.analyze_video(
                self.video_path,
                0.0,
                -1.0,
                config,
            )
            if self._cancel_requested:
                return
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class HistoryVideoPlayer(Card):
    """Player local incorporável baseado exclusivamente em QtMultimedia.

    English: Embeddable local player backed exclusively by QtMultimedia.
    """

    videoLoaded = Signal(str)
    videoStopped = Signal()
    analysisCompleted = Signal(object)
    analysisFailed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("mediaPlayer", True)
        self.video_path = ""
        self.duration_ms = 0
        self.is_dragging = False
        self._source_ready = False
        self._is_fullscreen = False
        self._last_display_second = -1
        self._analysis_thread = None
        self._analysis_running = False
        self._fullscreen_hide_timer = QTimer(self)
        self._fullscreen_hide_timer.setSingleShot(True)
        self._fullscreen_hide_timer.setInterval(2500)
        self._fullscreen_hide_timer.timeout.connect(self._hide_fullscreen_overlay)

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
        self.title_label = TitleLabel("Wuthering Waves")
        self.title_label.setObjectName("mediaPlayerTitle")
        header.addWidget(self.title_label)
        self.status_label = QLabel("PRONTO")
        self.status_label.setObjectName("mediaStatusBadge")
        header.addWidget(self.status_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)

        self.video_surface = QVideoWidget(self)
        self.video_surface.setObjectName("videoSurface")
        self._configure_video_surface()
        self.video_surface.setMouseTracking(True)
        self.video_surface.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video_surface.installEventFilter(self)
        self.video_surface.setAspectRatioMode(Qt.AspectRatioMode.KeepAspectRatio)
        self.media_player.setVideoOutput(self.video_surface)
        self.hud_label = QLabel("LIVE ANALYZER  //  60 FPS", self.video_surface)
        self.hud_label.setObjectName("videoHud")
        self.hud_label.setFixedHeight(26)
        self._position_video_hud()
        self.hud_label.raise_()
        self._build_fullscreen_overlay()
        layout.addWidget(self.video_surface, 1)

        toolbar = QFrame()
        toolbar.setObjectName("mediaToolbar")
        controls = QHBoxLayout(toolbar)
        controls.setContentsMargins(8, 5, 8, 5)
        controls.setSpacing(7)
        self.progress_slider = ClickableSeekSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setObjectName("playerProgress")
        self.progress_slider.setRange(0, 0)
        self.browse_button = self._button("▣  Selecionar vídeo")
        self.browse_button.setObjectName("mediaBrowseButton")
        self.browse_button.setText("▣")
        self.browse_button.setToolTip("Selecionar vídeo")
        self.browse_button.setFixedWidth(38)
        self.play_button = self._button("▶  Play")
        self.play_button.setObjectName("mediaPlayButton")
        self.play_button.setText("▶")
        self.play_button.setToolTip("Reproduzir ou pausar")
        self.play_button.setFixedWidth(42)
        self.stop_button = self._button("■  Parar")
        self.stop_button.setObjectName("mediaStopButton")
        self.stop_button.setText("■")
        self.stop_button.setToolTip("Parar vídeo")
        self.stop_button.setFixedWidth(42)
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        controls.addWidget(self.browse_button)
        controls.addWidget(self.play_button)
        controls.addWidget(self.stop_button)

        # A análise usa a engine C++/pybind11; o player continua responsável
        # apenas por dispará-la e apresentar o estado. Veja os marcadores
        # [EXTRAIR] abaixo para mover a integração para um serviço separado.
        self.analyze_button = self._button("Analisar")
        self.analyze_button.setObjectName("mediaAnalyzeButton")
        self.analyze_button.setToolTip("Analisar os números de dano deste vídeo")
        self.analyze_button.setEnabled(False)
        controls.addWidget(self.analyze_button)
        controls.addWidget(self.progress_slider, 1)

        self.time_label = QLabel("0:00 / 0:00")
        self.time_label.setObjectName("mediaTimeLabel")
        self.time_label.setFixedWidth(82)
        controls.addWidget(self.time_label)
        controls.addStretch(1)

        volume_label = QLabel("Volume")
        volume_label.setObjectName("mediaControlLabel")
        controls.addWidget(volume_label)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setObjectName("playerVolume")
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(60)
        controls.addWidget(self.volume_slider)

        self.subtitle_box = QComboBox()
        self.subtitle_box.setObjectName("mediaSubtitleBox")
        self.subtitle_box.setToolTip("Legendas")
        self.subtitle_box.setFixedWidth(90)
        self.subtitle_box.addItem("Legendas desativadas", -1)
        controls.addWidget(self.subtitle_box)
        self.fullscreen_button = self._button("⛶")
        self.fullscreen_button.setToolTip("Tela cheia")
        self.fullscreen_button.setFixedWidth(38)
        self.fullscreen_button.setEnabled(False)
        self.fullscreen_play_button.setEnabled(False)
        self.fullscreen_progress.setEnabled(False)
        controls.addWidget(self.fullscreen_button)
        layout.addWidget(toolbar)

    def _position_video_hud(self) -> None:
        self.hud_label.move(12, 12)

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._position_video_hud()
        if self._is_fullscreen:
            self._position_fullscreen_overlay()
        QTimer.singleShot(0, self._refresh_video_surface)

    def _build_fullscreen_overlay(self) -> None:
        self.fullscreen_overlay = QWidget(self.video_surface)
        self.fullscreen_overlay.setObjectName("fullscreenOverlay")
        self.fullscreen_overlay.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.fullscreen_overlay.setMouseTracking(True)
        self.fullscreen_overlay.installEventFilter(self)
        overlay_layout = QHBoxLayout(self.fullscreen_overlay)
        overlay_layout.setContentsMargins(10, 6, 10, 6)
        overlay_layout.setSpacing(7)

        self.fullscreen_play_button = self._button("▶")
        self.fullscreen_play_button.setObjectName("fullscreenPlayButton")
        self.fullscreen_play_button.setFixedSize(34, 30)
        self.fullscreen_play_button.setToolTip("Reproduzir ou pausar")
        overlay_layout.addWidget(self.fullscreen_play_button)

        self.fullscreen_time_label = QLabel("0:00 / 0:00")
        self.fullscreen_time_label.setObjectName("fullscreenTimeLabel")
        self.fullscreen_time_label.setFixedWidth(82)
        overlay_layout.addWidget(self.fullscreen_time_label)

        self.fullscreen_progress = ClickableSeekSlider(Qt.Orientation.Horizontal)
        self.fullscreen_progress.setObjectName("fullscreenProgress")
        self.fullscreen_progress.setRange(0, 0)
        overlay_layout.addWidget(self.fullscreen_progress, 1)

        self.fullscreen_volume = QSlider(Qt.Orientation.Horizontal)
        self.fullscreen_volume.setObjectName("fullscreenVolume")
        self.fullscreen_volume.setRange(0, 100)
        self.fullscreen_volume.setValue(100)
        self.fullscreen_volume.setFixedWidth(82)
        overlay_layout.addWidget(QLabel("◖"))
        overlay_layout.addWidget(self.fullscreen_volume)

        self.fullscreen_exit_button = self._button("×")
        self.fullscreen_exit_button.setObjectName("fullscreenExitButton")
        self.fullscreen_exit_button.setFixedSize(34, 30)
        self.fullscreen_exit_button.setToolTip("Sair da tela cheia (Esc)")
        overlay_layout.addWidget(self.fullscreen_exit_button)
        self.fullscreen_overlay.hide()
        for widget in [self.fullscreen_overlay, *self.fullscreen_overlay.findChildren(QWidget)]:
            widget.setMouseTracking(True)
            widget.installEventFilter(self)

    def _configure_video_surface(self) -> None:
        self.video_surface.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.video_surface.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        self.video_surface.setAutoFillBackground(False)
        self.video_surface.setUpdatesEnabled(True)
        self.video_surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, False)

    def _refresh_video_surface(self) -> None:
        self.video_surface.update()
        self.video_surface.repaint()

    @staticmethod
    def _button(text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("mediaControlButton")
        return button

    def _connect_signals(self) -> None:
        self.browse_button.clicked.connect(self.choose_video)
        self.analyze_button.clicked.connect(self.analyze_video)
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
        self.fullscreen_button.clicked.connect(self.enter_fullscreen)
        self.fullscreen_play_button.clicked.connect(self.toggle_playback)
        self.fullscreen_exit_button.clicked.connect(self.exit_fullscreen)
        self.fullscreen_progress.sliderMoved.connect(self.media_player.setPosition)
        self.fullscreen_progress.sliderReleased.connect(
            lambda: self.media_player.setPosition(self.fullscreen_progress.value())
        )
        self.fullscreen_volume.valueChanged.connect(self.set_volume)

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
        if self._analysis_running:
            self._set_status("Aguarde a análise atual terminar antes de trocar o vídeo")
            return False
        if not os.path.isfile(path):
            self._set_status("Arquivo de vídeo não encontrado")
            return False
        self.stop_video()
        self.video_path = str(Path(path).resolve())
        self._source_ready = False
        self.title_label.setText(Path(path).name)
        self.hud_label.setText("LIVE ANALYZER  //  READY")
        self._set_status(f"Carregando: {Path(path).name}")
        self._set_controls_enabled(True)
        self.analyze_button.setEnabled(not self._analysis_running)
        self.media_player.setSource(QUrl.fromLocalFile(self.video_path))
        self.videoLoaded.emit(self.video_path)
        self.media_player.play()
        QTimer.singleShot(0, self._refresh_video_surface)
        return True

    def toggle_playback(self) -> None:
        if not self.video_path:
            return
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def stop_video(self) -> None:
        self.exit_fullscreen()
        self._source_ready = False
        self.media_player.stop()
        self.media_player.setSource(QUrl())
        self.video_path = ""
        self.title_label.setText("Wuthering Waves")
        self.duration_ms = 0
        self.is_dragging = False
        self.progress_slider.setRange(0, 0)
        self.progress_slider.setValue(0)
        self.fullscreen_progress.setRange(0, 0)
        self.fullscreen_progress.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self.fullscreen_time_label.setText("0:00 / 0:00")
        self.play_button.setText("▶")
        self._set_status("PRONTO")
        self._set_controls_enabled(False)
        self.analyze_button.setEnabled(False)
        self._reset_subtitles()
        self.videoStopped.emit()

    def enter_fullscreen(self) -> None:
        if self._is_fullscreen:
            self._show_fullscreen_overlay()
            return
        self._is_fullscreen = True
        self.video_surface.setFullScreen(True)
        self.video_surface.setFocus(Qt.FocusReason.OtherFocusReason)
        self._show_fullscreen_overlay()

    def exit_fullscreen(self) -> None:
        if not self._is_fullscreen and not self.video_surface.isFullScreen():
            return
        self._is_fullscreen = False
        self._fullscreen_hide_timer.stop()
        self.fullscreen_overlay.hide()
        self.video_surface.setFullScreen(False)
        self._refresh_video_surface()

    def _show_fullscreen_overlay(self) -> None:
        if not self._is_fullscreen:
            return
        self._position_fullscreen_overlay()
        self.fullscreen_overlay.show()
        self.fullscreen_overlay.raise_()
        self._fullscreen_hide_timer.start()

    def _hide_fullscreen_overlay(self) -> None:
        if self._is_fullscreen:
            self.fullscreen_overlay.hide()

    def _position_fullscreen_overlay(self) -> None:
        margin = 24
        height = 48
        self.fullscreen_overlay.setGeometry(
            margin,
            max(margin, self.video_surface.height() - height - margin),
            max(220, self.video_surface.width() - margin * 2),
            height,
        )

    def eventFilter(self, watched: QWidget, event: QEvent) -> bool:
        if self._is_fullscreen and watched in {
            self.video_surface,
            self.fullscreen_overlay,
            *self.fullscreen_overlay.findChildren(QWidget),
        }:
            if event.type() in {QEvent.Type.MouseMove, QEvent.Type.MouseButtonPress, QEvent.Type.Enter}:
                self._show_fullscreen_overlay()
            elif event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
                self.exit_fullscreen()
                return True
            elif watched is self.video_surface and event.type() == QEvent.Type.Resize:
                self._position_fullscreen_overlay()
        return super().eventFilter(watched, event)

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

    def seek_to_seconds(self, seconds: float) -> None:
        """Seek the loaded video to a timestamp supplied by an external control."""
        if self.duration_ms <= 0:
            return
        position_ms = max(0, min(self.duration_ms, round(float(seconds) * 1000)))
        self.media_player.setPosition(position_ms)

    def _on_position_changed(self, position_ms: int) -> None:
        if not self._source_ready or not self.video_path or self.duration_ms <= 0:
            return
        if not self.is_dragging and not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(position_ms)
            display_second = position_ms // 1000
            if display_second != self._last_display_second:
                display_time = f"{self._clock(position_ms)} / {self._clock(self.duration_ms)}"
                self.time_label.setText(display_time)
                self.fullscreen_time_label.setText(display_time)
                self._last_display_second = display_second
        if not self.fullscreen_progress.isSliderDown():
            self.fullscreen_progress.setValue(position_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self.duration_ms = max(0, int(duration_ms))
        self._source_ready = self.duration_ms > 0 and bool(self.video_path)
        self.progress_slider.setRange(0, self.duration_ms)
        self.fullscreen_progress.setRange(0, self.duration_ms)
        self.time_label.setText(f"{self._clock(self.media_player.position())} / {self._clock(self.duration_ms)}")
        self.fullscreen_time_label.setText(
            f"{self._clock(self.media_player.position())} / {self._clock(self.duration_ms)}"
        )
        self._last_display_second = self.media_player.position() // 1000

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        playing = state == QMediaPlayer.PlaybackState.PlayingState
        paused = state == QMediaPlayer.PlaybackState.PausedState
        self.play_button.setText("Ⅱ" if playing else "▶")
        self.fullscreen_play_button.setText("Ⅱ" if playing else "▶")
        if paused:
            self._set_status("Pausado")
        elif playing:
            self._set_status("Reproduzindo")

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status in {
            QMediaPlayer.MediaStatus.LoadedMedia,
            QMediaPlayer.MediaStatus.BufferedMedia,
            QMediaPlayer.MediaStatus.BufferingMedia,
        }:
            QTimer.singleShot(0, self._refresh_video_surface)
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_button.setText("▶")
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

    # [EXTRAIR] Esta classe worker e o método analyze_video não são lógica do
    # player. Ao estabilizar a integração, mova-os para um módulo como
    # wuwa_calculator.services.damage_analysis e deixe aqui apenas os sinais.
    def analyze_video(self) -> None:
        """Executa a engine nativa sem bloquear o loop de eventos do Qt.

        A extensão ``damage_analyzer`` deve estar compilada/instalável no
        ambiente Python. O processamento de frames/OCR/filtros permanece em C++.
        """
        if not self.video_path or not os.path.isfile(self.video_path):
            self._set_status("Selecione um vídeo válido antes de analisar")
            return
        if self._analysis_running:
            return

        self._analysis_running = True
        self.analyze_button.setEnabled(False)
        self._set_status("Analisando vídeo…")
        self.hud_label.setText("DAMAGE ANALYSIS  //  RUNNING")

        thread = _NativeAnalysisThread(self.video_path, self)
        self._analysis_thread = thread
        thread.completed.connect(self._on_analysis_completed)
        thread.failed.connect(self._on_analysis_failed)
        thread.finished.connect(self._on_analysis_thread_finished)
        thread.start()

    def _on_analysis_completed(self, result: object) -> None:
        """Publica resultado da engine sem acoplar o player ao painel de DPS."""
        total = getattr(result, "total_damage", 0)
        hits = getattr(result, "total_hits", 0)
        peak = getattr(result, "peak_damage", 0)
        self._set_status(f"Análise concluída · {hits} acertos · dano {total:,.0f}")
        self.hud_label.setText("DAMAGE ANALYSIS  //  COMPLETE")
        self.analysisCompleted.emit(result)

    def _on_analysis_failed(self, message: str) -> None:
        self._set_status(f"Falha na análise: {message}")
        self.hud_label.setText("DAMAGE ANALYSIS  //  ERROR")
        self.analysisFailed.emit(message)

    def _on_analysis_thread_finished(self) -> None:
        self._analysis_running = False
        self.analyze_button.setEnabled(bool(self.video_path))
        thread = self._analysis_thread
        self._analysis_thread = None
        if thread is not None:
            thread.deleteLater()

    def shutdown_analysis(self) -> None:
        """Cancela a engine e aguarda a thread terminar (no próximo frame).

        Também é chamado pela janela principal ao fechar: widgets filhos não
        recebem closeEvent quando a janela fecha, e destruir um QThread ainda
        ativo derruba o processo.
        """
        thread = self._analysis_thread
        if thread is not None and thread.isRunning():
            thread.cancel()
            thread.wait()

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.play_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        self.fullscreen_button.setEnabled(enabled)
        self.fullscreen_play_button.setEnabled(enabled)
        self.fullscreen_progress.setEnabled(enabled)

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

    @staticmethod
    def _clock(milliseconds: int) -> str:
        total = max(0, int(milliseconds / 1000))
        return f"{total // 60}:{total % 60:02d}"

    def closeEvent(self, event) -> None:
        self.exit_fullscreen()
        self.shutdown_analysis()
        self.stop_video()
        super().closeEvent(event)
