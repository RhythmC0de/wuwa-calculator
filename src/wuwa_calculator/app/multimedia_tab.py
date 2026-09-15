"""Glassmorphism multimedia workspace for video rotation analysis."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget, QFrame, QSizePolicy,
)

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.wuwa_calculator.app.components import Card, TitleLabel
from src.wuwa_calculator.app.dps_simulation_panel import DpsSimulationPanel
from src.wuwa_calculator.app.history_video_player import HistoryVideoPlayer


EVENTS = (
    (15, "⚔", "Habilidade A", "Lançamento da habilidade básica."),
    (22, "⚔", "Habilidade B", "Conjuração da habilidade secundária."),
    (34, "✦", "Ultimate", "Ativação da habilidade final."),
    (47, "♜", "Buff", "Aplicação de buff de dano."),
    (72, "◇", "Esquiva", "Movimento de esquiva."),
    (88, "⚔", "Habilidade A", "Nova sequência de habilidades."),
    (125, "✦", "Ultimate", "Segundo uso da habilidade final."),
    (151, "◈", "Fim do vídeo", "Encerramento da análise no último frame."),
)


def _clock(milliseconds: int) -> str:
    total = max(0, int(milliseconds / 1000))
    return f"{total // 60}:{total % 60:02d}"


def _panel_title(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("mediaSectionTitle")
    return label


def _compact_width(widget: QWidget) -> None:
    widget.setMinimumWidth(0)
    widget.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)


class EventTimelinePanel(Card):
    def __init__(self, video_player: HistoryVideoPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.event_rows: list[tuple[float, QFrame, QLabel]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(6)
        header = QHBoxLayout()
        header.addWidget(_panel_title("Linha do Tempo de Eventos"))
        self.duration_label = QLabel("2:43")
        self.duration_label.setObjectName("mediaPanelDuration")
        header.addWidget(self.duration_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        events_layout = QVBoxLayout()
        events_layout.setSpacing(5)
        for event_index, (reference_timestamp, icon, title, description) in enumerate(EVENTS):
            row = QFrame()
            row.setObjectName("eventRow")
            category = "Ultimate" if "Ultimate" in title else "Buff" if "Buff" in title else "Skill"
            row.setProperty("category", category)
            row.setProperty("stripe", "even" if event_index % 2 == 0 else "odd")
            row.setMinimumHeight(40)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 5, 8, 5)
            row_layout.setSpacing(9)
            time_label = QLabel(_clock(reference_timestamp * 1000))
            time_label.setObjectName("eventTimestamp")
            time_label.setFixedWidth(38)
            icon_label = QLabel(icon)
            icon_label.setObjectName("eventIcon")
            icon_label.setFixedSize(24, 24)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            text_layout = QVBoxLayout()
            text_layout.setSpacing(0)
            title_label = QLabel(title)
            title_label.setObjectName("eventTitle")
            category_label = QLabel(f"[{category}]")
            category_label.setObjectName("eventCategory")
            description_label = QLabel(description)
            description_label.setObjectName("eventDescription")
            description_label.setWordWrap(True)
            text_layout.addWidget(title_label)
            text_layout.addWidget(category_label)
            text_layout.addWidget(description_label)
            row_layout.addWidget(time_label)
            row_layout.addWidget(icon_label)
            row_layout.addLayout(text_layout, 1)
            events_layout.addWidget(row)
            self.event_rows.append((reference_timestamp, row, time_label))
        events_layout.addStretch(1)
        layout.addLayout(events_layout, 1)
        self._reference_event_rows = list(self.event_rows)
        self._pending_position_ms = 0
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(50)
        self._position_timer.timeout.connect(self._flush_position)
        video_player.media_player.positionChanged.connect(
            self._queue_position,
            Qt.ConnectionType.QueuedConnection,
        )
        video_player.media_player.durationChanged.connect(self._set_duration)

    def _set_duration(self, duration_ms: int) -> None:
        if duration_ms > 0:
            self.duration_label.setText(_clock(duration_ms))
            duration_seconds = duration_ms / 1000.0
            reference_end = EVENTS[-1][0]
            scale = duration_seconds / reference_end if reference_end else 1.0
            self.event_rows = [
                (reference_timestamp * scale, row, time_label)
                for reference_timestamp, row, time_label in self._reference_event_rows
            ]
            for timestamp, _row, time_label in self.event_rows:
                time_label.setText(_clock(round(timestamp * 1000)))

    def _queue_position(self, position_ms: int) -> None:
        self._pending_position_ms = position_ms
        if not self._position_timer.isActive():
            self._position_timer.start()

    def _flush_position(self) -> None:
        self._position_timer.stop()
        seconds = self._pending_position_ms / 1000.0
        active_timestamp = max((timestamp for timestamp, _row, _time_label in self.event_rows if timestamp <= seconds), default=-1)
        for timestamp, row, _time_label in self.event_rows:
            row.setProperty("active", timestamp == active_timestamp)
            row.style().unpolish(row)
            row.style().polish(row)


class VideoInfoPanel(Card):
    def __init__(self, video_player: HistoryVideoPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)
        layout.addWidget(_panel_title("Informações do vídeo"))
        metrics_grid = QGridLayout()
        metrics_grid.setHorizontalSpacing(18)
        metrics_grid.setVerticalSpacing(3)
        self.duration_value = QLabel("2:43")
        metrics = (
            ("Duração", self.duration_value),
            ("Resolução", "1920 x 1080"),
            ("FPS", "60"),
            ("Tamanho", "248 MB"),
            ("Formato", "MP4"),
        )
        for index, (name, value) in enumerate(metrics):
            self._add_metric(metrics_grid, index // 2, index % 2, name, value)
        layout.addLayout(metrics_grid)
        video_player.media_player.durationChanged.connect(self._set_duration)

    @staticmethod
    def _add_metric(layout: QGridLayout, row_index: int, column: int, name: str, value: str | QLabel) -> None:
        cell = QVBoxLayout()
        cell.setSpacing(0)
        label = QLabel(name)
        label.setObjectName("metricName")
        value_label = value if isinstance(value, QLabel) else QLabel(value)
        value_label.setObjectName("metricValue")
        cell.addWidget(label)
        cell.addWidget(value_label)
        layout.addLayout(cell, row_index, column)

    def _set_duration(self, duration_ms: int) -> None:
        if duration_ms > 0:
            self.duration_value.setText(_clock(duration_ms))


class PlaybackOptionsPanel(Card):
    def __init__(self, video_player: HistoryVideoPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        layout.addWidget(_panel_title("Opções de reprodução"))
        speed_combo = self._add_combo(layout, "Velocidade", ("1.0x", "0.5x", "1.5x", "2.0x"))
        speed_combo.currentTextChanged.connect(
            lambda value: video_player.media_player.setPlaybackRate(float(value.rstrip("x")))
        )

    @staticmethod
    def _add_combo(layout: QVBoxLayout, label_text: str, values: tuple[str, ...]) -> QComboBox:
        row = QHBoxLayout()
        label = QLabel(label_text)
        label.setObjectName("optionLabel")
        label.setWordWrap(True)
        label.setMinimumWidth(128)
        combo = QComboBox()
        combo.setObjectName("mediaOptionCombo")
        combo.setMinimumWidth(108)
        combo.addItems(values)
        row.addWidget(label, 1)
        row.addWidget(combo)
        layout.addLayout(row)
        return combo

class VideoActionsPanel(Card):
    def __init__(self, video_player: HistoryVideoPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_player = video_player
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        layout.addWidget(_panel_title("Controles do vídeo"))
        actions = QHBoxLayout()
        actions.setSpacing(6)
        buttons = (
            ("▣  Capturar Frame", self._capture_frame),
            ("⌂  Abrir Pasta", self._open_folder),
        )
        for text, callback in buttons:
            button = QPushButton(text)
            button.setObjectName("mediaQuickAction")
            button.setMinimumHeight(30)
            button.clicked.connect(callback)
            actions.addWidget(button, 1)
        layout.addLayout(actions)
        self.status_label = QLabel("")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)

    def _set_status(self, message: str) -> None:
        self.status_label.setText(message)

    def _capture_frame(self) -> None:
        if not self.video_player.video_path:
            self._set_status("Carregue um vídeo primeiro")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar captura", "captura.png", "PNG (*.png)")
        if path and self.video_player.video_surface.grab().save(path):
            self._set_status("Captura salva")

    def _open_folder(self) -> None:
        folder = str(Path(self.video_player.video_path).parent) if self.video_player.video_path else str(Path.home())
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


class MultimediaTab(QWidget):
    """Full glassmorphism workspace for video, DPS and rotation events."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(8)
        protocol_bar = QFrame()
        protocol_bar.setObjectName("frequencyProtocolBar")
        protocol_layout = QVBoxLayout(protocol_bar)
        protocol_layout.setContentsMargins(14, 9, 14, 9)
        protocol_layout.setSpacing(2)
        protocol_header = QHBoxLayout()
        protocol_title = QLabel("[ TETHYS PROTOCOL // OBSERVATÓRIO DE FREQUÊNCIAS ]")
        protocol_title.setObjectName("frequencyProtocolTitle")
        protocol_header.addWidget(protocol_title)
        protocol_badge = QLabel(
            "STATUS: Sincronizado com o Terminal Central // Dados descartados à Necroestrela"
        )
        protocol_badge.setObjectName("frequencyProtocolBadge")
        protocol_badge.setWordWrap(False)
        protocol_badge.setMinimumHeight(28)
        protocol_badge.setMinimumWidth(430)
        protocol_badge.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        protocol_header.addWidget(protocol_badge, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        protocol_layout.addLayout(protocol_header)
        protocol_subtitle = QLabel(
            "Mesa de Areia de Combate • Mapeando oscilações de ressonância e isolando ruídos."
        )
        protocol_subtitle.setObjectName("frequencyProtocolSubtitle")
        protocol_layout.addWidget(protocol_subtitle)
        layout.addWidget(protocol_bar)
        self.video_player = HistoryVideoPlayer()
        self.video_player.setMinimumHeight(340)
        self.dps_panel = DpsSimulationPanel(self.video_player)
        self.dps_panel.setMinimumHeight(300)
        self.dps_panel.setMaximumHeight(394)
        self.event_panel = EventTimelinePanel(self.video_player)
        self.info_panel = VideoInfoPanel(self.video_player)
        self.options_panel = PlaybackOptionsPanel(self.video_player)
        self.actions_panel = VideoActionsPanel(self.video_player)
        for panel in (
            self.video_player,
            self.dps_panel,
            self.event_panel,
            self.info_panel,
            self.options_panel,
            self.actions_panel,
        ):
            _compact_width(panel)

        left_column = QWidget()
        _compact_width(left_column)
        left_layout = QVBoxLayout(left_column)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        left_layout.addWidget(self.video_player, 3)
        left_layout.addWidget(self.dps_panel, 2)
        right_column = QWidget()
        _compact_width(right_column)
        right_column.setMinimumWidth(270)
        right_column.setMaximumWidth(270)
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        self.event_panel.setMaximumHeight(430)
        right_layout.addWidget(self.event_panel, 0)

        compact_controls = Card()
        compact_controls.setObjectName("mediaSupportPanel")
        compact_controls_layout = QVBoxLayout(compact_controls)
        compact_controls_layout.setContentsMargins(8, 8, 8, 8)
        compact_controls_layout.setSpacing(4)
        compact_controls_layout.addWidget(self.info_panel)
        compact_controls_layout.addWidget(self.options_panel)
        compact_controls_layout.addWidget(self.actions_panel)
        right_layout.addWidget(compact_controls, 1)

        columns = QGridLayout()
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setHorizontalSpacing(14)
        columns.addWidget(left_column, 0, 0)
        columns.addWidget(right_column, 0, 1)
        columns.setColumnStretch(0, 7)
        columns.setColumnStretch(1, 3)
        layout.addLayout(columns, 1)

    def closeEvent(self, event) -> None:
        self.video_player.stop_video()
        super().closeEvent(event)

    def set_active(self, active: bool) -> None:
        if active:
            self.setUpdatesEnabled(True)
            return
        self.dps_panel._stop_live_analysis()
        self.video_player.media_player.pause()
        self.setUpdatesEnabled(False)
