"""Rotation history tab for the PySide6 application."""

import os
import sys
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QUrl, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSlider, QSplitter, QTableWidget, QVBoxLayout, QWidget,
    QStyledItemDelegate,
)

from src.wuwa_calculator.app.components import Card, DataTable, MetricCard, TitleLabel
from src.wuwa_calculator.app.teams_tab import CharacterBadgeWidget
from src.wuwa_calculator.app.backend_adapter import (
    ROTATION_HISTORY_FILE,
    export_history_file,
    history_records,
    import_history_file,
    save_history_record,
)
from src.wuwa_calculator.app.styles import apply_glow
from src.wuwa_calculator.storage.team_storage import load_teams
from src.wuwa_calculator.data.images import CHARACTER_IMAGE_FALLBACKS
from src.wuwa_calculator.app.security_policy import allows_remote_content


def _read_network_reply(reply: object) -> object:
    if (
        not getattr(reply, "isOpen", lambda: False)()
        or getattr(reply, "error", lambda: QNetworkReply.NetworkError.UnknownNetworkError)()
        != QNetworkReply.NetworkError.NoError
    ):
        return b""
    return getattr(reply, "readAll", lambda: b"")()


class DamageBarDelegate(QStyledItemDelegate):
    def paint(self, painter: QPainter, option, index) -> None:
        value = index.data(Qt.ItemDataRole.DisplayRole)
        try:
            numeric = max(0.0, float(str(value).replace(",", "")))
        except (TypeError, ValueError):
            numeric = 0.0
        maximum = 1.0
        model = index.model()
        for row in range(model.rowCount()):
            try:
                maximum = max(maximum, float(str(model.index(row, index.column()).data()).replace(",", "")))
            except (TypeError, ValueError):
                continue
        painter.save()
        bar = option.rect.adjusted(6, option.rect.height() // 2 - 3, -6, -(option.rect.height() // 2 - 3))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(38, 48, 62, 180))
        painter.drawRoundedRect(bar, 3, 3)
        filled = bar.adjusted(0, 0, -int(bar.width() * (1 - min(1.0, numeric / maximum))), 0)
        painter.setBrush(QColor(67, 219, 193, 145))
        painter.drawRoundedRect(filled, 3, 3)
        painter.setPen(QColor("#F2F0FF"))
        painter.drawText(option.rect.adjusted(10, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, str(value))
        painter.restore()

# The active history player is QtMultimedia-based. The private legacy class
# below is retained only for source compatibility and is never instantiated.
vlc = None

HISTORY_FILE = ROTATION_HISTORY_FILE


class RotationForm(Card):
    def __init__(self, owner: "HistoryTab") -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.addWidget(TitleLabel("Teste de rotação salvo"))
        fields = QHBoxLayout()
        self.team_box = QComboBox()
        self.team_box.addItems(["Equipe 1", "Fusion quickswap", "Glacio control"])
        self.rotation_entry = QLineEdit()
        self.rotation_entry.setPlaceholderText("Nome da rotação")
        fields.addWidget(self.team_box)
        fields.addWidget(self.rotation_entry)
        layout.addLayout(fields)
        actions = QHBoxLayout()
        self.save_button = QPushButton("Salvar cálculo")
        self.import_button = QPushButton("Importar JSON")
        self.export_button = QPushButton("Exportar JSON")
        self.save_button.clicked.connect(owner.save_current)
        self.import_button.clicked.connect(owner.import_history)
        self.export_button.clicked.connect(owner.export_history)
        for button in (self.save_button, self.import_button, self.export_button):
            apply_glow(button, blur=18, opacity=140)
            actions.addWidget(button)
        layout.addLayout(actions)
        self.status_label = QLabel("Pronto para salvar um cálculo.")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)


class _LegacyVideoPlayer(Card):
    def __init__(self) -> None:
        super().__init__()
        self.instance = None
        self.player = None
        self.media = None
        self.video_path = ""
        self.duration_seconds = 0.0
        self.tracks_loaded = False
        self.is_seeking = False
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(100)
        self.poll_timer.timeout.connect(self.poll_position)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        header = QHBoxLayout()
        header.addWidget(TitleLabel("PLAYER VLC LOCAL"))
        self.state_label = QLabel("PRONTO PARA MÍDIA LOCAL")
        self.state_label.setObjectName("muted")
        header.addWidget(self.state_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)
        self.video_surface = QFrame()
        self.video_surface.setObjectName("card")
        self.video_surface.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.surface = self.video_surface
        surface_layout = QVBoxLayout(self.video_surface)
        empty = QLabel("Nenhum vídeo carregado")
        empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty.setObjectName("muted")
        surface_layout.addWidget(empty)
        layout.addWidget(self.video_surface, 1)
        self.progress = QSlider(Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderPressed.connect(self.begin_seek)
        self.progress.sliderMoved.connect(self.preview_seek)
        self.progress.sliderReleased.connect(self.seek_from_slider)
        layout.addWidget(self.progress)
        controls = QHBoxLayout()
        self.browse_button = QPushButton("Procurar vídeo")
        self.play_button = QPushButton("Play")
        self.stop_button = QPushButton("Stop")
        for button in (self.browse_button, self.play_button, self.stop_button):
            button.setObjectName("playerButton")
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
        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setFixedWidth(100)
        controls.addWidget(self.volume)
        self.subtitle_box = QComboBox()
        self.subtitle_box.addItems(["Legendas desativadas", "Legenda 1"])
        self.subtitle_box.currentIndexChanged.connect(self.select_subtitle)
        controls.addWidget(self.subtitle_box)
        layout.addLayout(controls)
        self.browse_button.clicked.connect(self.choose_video)
        self.play_button.clicked.connect(self.toggle_playback)
        self.stop_button.clicked.connect(self.stop_video)
        self.volume.valueChanged.connect(self.set_volume)

    def choose_video(self) -> None:
        source, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar vídeo de referência",
            "",
            "Vídeos (*.mp4 *.mkv *.avi *.mov *.webm);;Todos os arquivos (*)",
        )
        if source:
            self.load_video(source)

    def load_video(self, path: str) -> bool:
        if vlc is None:
            self.set_status("VLC indisponível: instale python-vlc e VLC Media Player")
            return False
        if not os.path.isfile(path):
            self.set_status("Arquivo de vídeo não encontrado")
            return False
        self.stop_video()
        try:
            self.instance = vlc.Instance("--no-video-title-show", "--quiet")
            self.player = self.instance.media_player_new()
            self.video_surface.update()
            window_id = int(self.video_surface.winId())
            if sys.platform.startswith("win"):
                self.player.set_hwnd(window_id)
            elif sys.platform.startswith("linux"):
                self.player.set_xwindow(window_id)
            elif sys.platform == "darwin":
                self.player.set_nsobject(window_id)
            self.media = self.instance.media_new(str(Path(path).resolve()))
            self.player.set_media(self.media)
            self.video_path = str(Path(path).resolve())
            self.tracks_loaded = False
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.set_status(f"Carregando: {Path(path).name}")
            if self.player.play() == -1:
                raise RuntimeError("libVLC recusou a reprodução do arquivo")
            self.play_button.setText("Pausar")
            self.poll_timer.start()
            return True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as error:
            self.set_status(f"Falha ao iniciar VLC: {error}")
            self.stop_video()
            return False

    def toggle_playback(self) -> None:
        if self.player is None:
            return
        try:
            if self.player.is_playing():
                self.player.pause()
                self.play_button.setText("Reproduzir")
            else:
                self.player.play()
                self.play_button.setText("Pausar")
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError) as error:
            self.set_status(f"Erro no controle VLC: {error}")

    def stop_video(self) -> None:
        self.poll_timer.stop()
        if self.player is not None:
            try:
                self.player.stop()
                self.player.release()
            except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
                pass
        if self.media is not None:
            try:
                self.media.release()
            except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
                pass
        if self.instance is not None:
            try:
                self.instance.release()
            except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
                pass
        self.player = None
        self.media = None
        self.instance = None
        self.duration_seconds = 0.0
        self.is_seeking = False
        self.progress.setValue(0)
        self.time_label.setText("0:00 / 0:00")
        self.play_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.play_button.setText("Play")

    def poll_position(self) -> None:
        if self.player is None:
            return
        try:
            length = max(0, self.player.get_length()) / 1000.0
            current = max(0, self.player.get_time()) / 1000.0
            self.duration_seconds = length
            if not self.is_seeking and not self.progress.isSliderDown() and length > 0:
                self.progress.setValue(int(min(1.0, current / length) * 1000))
            if not self.is_seeking:
                self.time_label.setText(f"{self.clock(current)} / {self.clock(length)}")
            if not self.tracks_loaded:
                self.load_subtitles()
            if length > 0 and current >= length:
                self.play_button.setText("Reproduzir")
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            return

    def begin_seek(self) -> None:
        self.is_seeking = True

    def preview_seek(self, value: int) -> None:
        if not self.duration_seconds:
            return
        preview_seconds = value / 1000.0 * self.duration_seconds
        self.time_label.setText(
            f"{self.clock(preview_seconds)} / {self.clock(self.duration_seconds)}"
        )

    def seek_from_slider(self) -> None:
        value = self.progress.value()
        if self.player is None or not self.duration_seconds:
            self.is_seeking = False
            return
        try:
            seconds = value / 1000.0 * self.duration_seconds
            self.player.set_time(int(seconds * 1000.0))
            self.time_label.setText(
                f"{self.clock(seconds)} / {self.clock(self.duration_seconds)}"
            )
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            pass
        finally:
            self.is_seeking = False

    def set_volume(self, value: int) -> None:
        if self.player is None:
            return
        try:
            self.player.audio_set_volume(max(0, min(100, int(value))))
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            return

    def load_subtitles(self) -> None:
        if self.player is None:
            return
        try:
            tracks = self.player.video_get_spu_description() or self.player.video_get_subtitle_description() or []
            with QSignalBlocker(self.subtitle_box):
                self.subtitle_box.clear()
                self.subtitle_box.addItem("Legendas desativadas", -1)
                for track_id, name in tracks:
                    if int(track_id) >= 0:
                        label = name.decode("utf-8", errors="replace") if isinstance(name, bytes) else str(name)
                        self.subtitle_box.addItem(label or "Legenda", int(track_id))
            self.tracks_loaded = True
        except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
            return

    def select_subtitle(self, index: int) -> None:
        if self.player is None:
            return
        track_id = self.subtitle_box.itemData(index)
        if track_id is not None:
            try:
                self.player.video_set_spu(int(track_id))
            except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
                return

    def set_status(self, text: str) -> None:
        self.state_label.setText(text)

    @staticmethod
    def clock(seconds: float) -> str:
        total = max(0, int(seconds))
        return f"{total // 60}:{total % 60:02d}"

    def closeEvent(self, event: object) -> None:
        self.stop_video()
        super().closeEvent(event)  # type: ignore[arg-type]


class HistoryTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        root = QHBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        splitter = QSplitter()
        root.addWidget(splitter)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(12)
        team_summary = Card()
        team_summary.setObjectName("historyTeamSummary")
        team_layout = QVBoxLayout(team_summary)
        team_layout.setContentsMargins(14, 12, 14, 12)
        team_layout.addWidget(TitleLabel("Equipe ativa"))
        self.team_summary_label = QLabel("Selecione uma equipe para visualizar a composição")
        self.team_summary_label.setObjectName("historyTeamMembers")
        self.team_summary_label.setWordWrap(True)
        team_layout.addWidget(self.team_summary_label)
        self.team_badges_layout = QHBoxLayout()
        self.team_badges_layout.setSpacing(8)
        team_layout.addLayout(self.team_badges_layout)
        left_layout.addWidget(team_summary)

        quick = QFrame()
        quick.setObjectName("historyQuickMetrics")
        quick_layout = QHBoxLayout(quick)
        quick_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_dps = QLabel("--")
        self.quick_damage = QLabel("--")
        for title, label in (("DPS TOTAL", self.quick_dps), ("DANO ACUMULADO", self.quick_damage)):
            block = QFrame()
            block.setObjectName("historyQuickMetric")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(10, 8, 10, 8)
            caption = QLabel(title)
            caption.setObjectName("historyMetricCaption")
            label.setObjectName("historyMetricValue")
            block_layout.addWidget(caption)
            block_layout.addWidget(label)
            quick_layout.addWidget(block)
        left_layout.addWidget(quick)
        self.rotation_form_widget = RotationForm(self)
        left_layout.addStretch(1)
        left_layout.addWidget(self.rotation_form_widget)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(12)
        analytics = Card()
        analytics_layout = QVBoxLayout(analytics)
        analytics_layout.setContentsMargins(16, 14, 16, 16)
        analytics_layout.addWidget(TitleLabel("Análise de Dano"))
        metrics = QHBoxLayout()
        self.metrics: dict[str, MetricCard] = {}
        for key, title in (("theoretical", "Teórico"), ("practical", "Prático"), ("accuracy", "Taxa de Acerto"), ("delta", "Delta")):
            card = MetricCard(title)
            card.setObjectName("historyStatCard")
            self.metrics[key] = card
            metrics.addWidget(card)
        analytics_layout.addLayout(metrics)
        right_layout.addWidget(analytics)

        audit = Card()
        audit_layout = QVBoxLayout(audit)
        audit_layout.setContentsMargins(16, 14, 16, 16)
        audit_layout.addWidget(TitleLabel("Auditoria de Habilidades | calculado versus jogabilidade"))
        self.audit_table = DataTable(("Personagem / Habilidade", "Tipo", "Não-crítico", "Crítico", "Esperado", "Prático", "Delta"))
        self.audit_table.setObjectName("historyAuditTable")
        self.audit_table.setAlternatingRowColors(True)
        self.audit_table.setItemDelegateForColumn(4, DamageBarDelegate(self.audit_table))
        self.audit_table.setItemDelegateForColumn(5, DamageBarDelegate(self.audit_table))
        audit_layout.addWidget(self.audit_table, 1)
        right_layout.addWidget(audit, 1)

        saved = Card()
        saved_layout = QVBoxLayout(saved)
        saved_layout.setContentsMargins(16, 14, 16, 16)
        saved_layout.addWidget(TitleLabel("Comparação salva"))
        self.saved_table = DataTable(("ID", "Equipe", "Rotação", "Dano total", "Data"))
        self.saved_table.setObjectName("historySavedTable")
        self.saved_table.setAlternatingRowColors(True)
        self.saved_table.cellClicked.connect(self.select_history)
        saved_layout.addWidget(self.saved_table)
        right_layout.addWidget(saved, 1)
        splitter.addWidget(right)
        splitter.setSizes([620, 720])
        self.rotation_form = self.rotation_form_widget
        self.team_network = QNetworkAccessManager(self)
        self.team_image_replies: dict[str, object] = {}
        self.current_result: object | None = None
        self.refresh_team_names()
        self.refresh_team_summary()
        self.refresh_history()

    def refresh_team_names(self) -> None:
        names = [str(team.get("name", "Equipe sem nome")) for team in load_teams()]
        if not names:
            names = ["Equipe 1"]
        current = self.rotation_form.team_box.currentText()
        self.rotation_form.team_box.clear()
        self.rotation_form.team_box.addItems(names)
        if current in names:
            self.rotation_form.team_box.setCurrentText(current)
        self.rotation_form.team_box.currentTextChanged.connect(self.refresh_team_summary)

    def refresh_team_summary(self, team_name: str | None = None) -> None:
        selected = team_name or self.rotation_form.team_box.currentText()
        teams = load_teams()
        team = next((item for item in teams if str(item.get("name", "")) == selected), None)
        characters = team.get("characters", []) if isinstance(team, dict) else []
        names = [str(character).title() for character in characters[:3]] if isinstance(characters, list) else []
        self.team_summary_label.setText("   ".join(f"◉ {name}" for name in names) or "Nenhum integrante configurado")
        while self.team_badges_layout.count():
            item = self.team_badges_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        for character in characters[:3] if isinstance(characters, list) else []:
            character_id = str(character).casefold()
            images = CHARACTER_IMAGE_FALLBACKS.get(character_id, {})
            badge = CharacterBadgeWidget()
            self.team_badges_layout.addWidget(badge)
            if isinstance(images, dict):
                self._load_team_badge(str(images.get("char", "")), badge, "char")
                self._load_team_badge(str(images.get("weapon", "")), badge, "weapon")
        self.team_badges_layout.addStretch(1)

    def _load_team_badge(self, url: str, badge: CharacterBadgeWidget, kind: str) -> None:
        if not url or not allows_remote_content(url):
            return
        reply = self.team_network.get(QNetworkRequest(QUrl(url)))
        self.team_image_replies[url] = reply
        reply.finished.connect(lambda: self._finish_team_badge(reply, badge, kind, url))

    def _finish_team_badge(self, reply: object, badge: CharacterBadgeWidget, kind: str, url: str) -> None:
        try:
            pixmap = QPixmap()
            pixmap.loadFromData(_read_network_reply(reply))
            if not pixmap.isNull():
                if kind == "char":
                    badge.set_pixmaps(char_pixmap=pixmap)
                else:
                    badge.set_pixmaps(weapon_pixmap=pixmap)
        except (AttributeError, RuntimeError, TypeError):
            pass
        self.team_image_replies.pop(url, None)

    def refresh_history(self) -> None:
        records = history_records()
        rows = [
            [
                str(item.get("id", "")),
                str(item.get("team", "")),
                str(item.get("rotation", "")),
                f"{float(item.get('damage', 0)):,.2f}",
                str(item.get("date", "")).replace("T", " "),
            ]
            for item in records
        ]
        self.saved_table.replace_rows(rows)

    def save_current(self) -> None:
        try:
            damage = float(getattr(self.current_result, "rotation_damage", 0.0))
            record = save_history_record(
                team=self.rotation_form.team_box.currentText(),
                rotation=self.rotation_form.rotation_entry.text(),
                damage=damage,
            )
        except (OSError, TypeError, ValueError) as error:
            self.rotation_form.status_label.setText(f"Falha ao salvar: {error}")
            return
        self.rotation_form.status_label.setText(f"Cálculo {record['id']} salvo.")
        self.refresh_history()

    def apply_calculation(self, result: object) -> None:
        self.current_result = result
        theoretical = float(getattr(result, "rotation_damage", 0.0))
        self.metrics["theoretical"].value_label.setText(f"{theoretical:,.0f}")
        self.quick_damage.setText(f"{theoretical:,.0f}")
        self.quick_dps.setText(f"{theoretical:,.0f}")
        self.metrics["practical"].value_label.setText("--")
        self.metrics["accuracy"].value_label.setText("--")
        self.metrics["delta"].value_label.setText("--")
        self.audit_table.replace_rows([[
            "Cálculo atual",
            "Rotação",
            f"{float(getattr(result, 'non_critical_per_hit', 0.0)):,.2f}",
            f"{float(getattr(result, 'critical_per_hit', 0.0)):,.2f}",
            f"{theoretical:,.2f}",
            "--",
            "--",
        ]])
        self.rotation_form.status_label.setText("Resultado calculado e pronto para salvar.")

    def import_history(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "Importar histórico", "", "JSON (*.json)")
        if not source:
            return
        try:
            imported = import_history_file(Path(source))
        except (OSError, TypeError, ValueError) as error:
            self.rotation_form.status_label.setText(f"Falha ao importar JSON: {error}")
            return
        self.refresh_team_names()
        self.refresh_history()
        self.rotation_form.status_label.setText(f"{len(imported)} cálculo(s) importado(s).")

    def export_history(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar histórico", "rotation_history.json", "JSON (*.json)")
        if destination:
            try:
                export_history_file(destination=Path(destination))
            except (OSError, TypeError, ValueError) as error:
                self.rotation_form.status_label.setText(f"Falha ao exportar JSON: {error}")
                return
            self.rotation_form.status_label.setText("Histórico exportado.")

    def select_history(self, row: int, _column: int) -> None:
        records = history_records()
        if row >= len(records):
            return
        record = records[row]
        damage = float(record.get("damage", 0))
        self.metrics["theoretical"].value_label.setText(f"{damage:,.0f}")
        practical = record.get("practical_damage")
        if practical in (None, ""):
            self.metrics["practical"].value_label.setText("--")
            self.metrics["delta"].value_label.setText("--")
        else:
            practical_value = float(practical)
            self.metrics["practical"].value_label.setText(f"{practical_value:,.0f}")
            self.metrics["delta"].value_label.setText(f"{practical_value - damage:+,.0f}")
        self.metrics["accuracy"].value_label.setText("--")
        self.current_result = None
        skills = record.get("skills", [])
        self.audit_table.replace_rows(self.skill_rows(skills) if isinstance(skills, list) else [])

    @staticmethod
    def skill_rows(skills: list[object]) -> list[list[str]]:
        rows: list[list[str]] = []
        for skill in skills:
            if not isinstance(skill, dict):
                continue
            rows.append([
                str(skill.get("skill", skill.get("name", "Habilidade"))),
                f"[{str(skill.get('type', 'Skill')).title()}]",
                str(skill.get("noncrit", skill.get("non_critical", "--"))),
                str(skill.get("crit", skill.get("critical", "--"))),
                str(skill.get("expected", "--")),
                str(skill.get("practical", "--")),
                str(skill.get("delta", "--")),
            ])
        return rows