"""Interactive DPS timeline synchronized with the native Tethys video player."""

from __future__ import annotations

import math
import sys
from collections import defaultdict
from threading import Lock
from typing import Any
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pyqtgraph as pg
from PySide6.QtCore import QObject, QTime, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTimeEdit, QVBoxLayout, QWidget,
)

from src.wuwa_calculator.app.components import Card


ANALYSIS_BUCKET_SECONDS = 5.0
INACTIVITY_TIMEOUT = 12.0
MIN_INACTIVITY_ANALYSIS_SECONDS = 15.0
OCR_SAMPLE_FPS = 8.0


class DpsPlotWidget(pg.PlotWidget):
    timestampClicked = Signal(float)

    def __init__(self, parent: QWidget | None = None) -> None:
        axis_items = {
            "bottom": TimelineAxis(orientation="bottom"),
            "left": NumericAxis(orientation="left"),
            "right": NumericAxis(orientation="right"),
        }
        super().__init__(axisItems=axis_items, parent=parent)
        self.scene().sigMouseClicked.connect(self._on_scene_clicked)

    def _on_scene_clicked(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        view_box = self.getPlotItem().vb
        if not view_box.sceneBoundingRect().contains(event.scenePos()):
            return
        point = view_box.mapSceneToView(event.scenePos())
        if point.x() >= 0:
            self.timestampClicked.emit(float(point.x()))


class NumericAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        return [f"{value:,.0f}" for value in values]


class TimelineAxis(pg.AxisItem):
    def tickStrings(self, values, scale, spacing):
        labels = []
        for value in values:
            total = max(0, int(value))
            labels.append(f"{total // 60}:{total % 60:02d}")
        return labels


class CvDamageAnalysisWorker(QObject):
    progress = Signal(int)
    finished = Signal(object, float)
    failed = Signal(str)

    def __init__(self, video_path: str, skip_seconds: float, block_seconds: float) -> None:
        super().__init__()
        self.video_path = video_path
        self.skip_seconds = max(0.0, skip_seconds)
        self.block_seconds = max(1.0, block_seconds)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import cv2

        capture = cv2.VideoCapture(self.video_path, cv2.CAP_FFMPEG)
        if not capture.isOpened():
            self.failed.emit("Não foi possível abrir o vídeo para análise OpenCV")
            return
        try:
            fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration = frame_count / fps if frame_count else 0.0
            capture.set(cv2.CAP_PROP_POS_MSEC, self.skip_seconds * 1000.0)
            buckets: defaultdict[int, float] = defaultdict(float)
            recent_detections: dict[tuple[int, int, int], tuple[float, float]] = {}
            frame_index = int(self.skip_seconds * fps)
            last_progress = -1
            while not self._cancelled:
                success, frame = capture.read()
                if not success:
                    break
                timestamp = frame_index / fps
                for value, center_x, center_y in self._detect_damage_events(frame):
                    signature = (center_x // 50, center_y // 30, value // 100)
                    previous = recent_detections.get(signature)
                    if previous and timestamp - previous[0] < 0.35:
                        continue
                    recent_detections[signature] = (timestamp, value)
                    buckets[int(timestamp // self.block_seconds)] += value
                frame_index += 1
                if frame_count:
                    progress = int(min(100, frame_index / frame_count * 100))
                    if progress != last_progress:
                        self.progress.emit(progress)
                        last_progress = progress
            if self._cancelled:
                self.finished.emit([], duration)
                return
            end_time = max(duration, self.skip_seconds)
            block_count = max(1, math.ceil(max(0.0, end_time - self.skip_seconds) / self.block_seconds))
            results = []
            accumulated = 0.0
            for index in range(block_count):
                damage = buckets.get(index + int(self.skip_seconds // self.block_seconds), 0.0)
                accumulated += damage
                timestamp = self.skip_seconds + (index + 1) * self.block_seconds
                results.append((min(timestamp, end_time), damage / self.block_seconds, accumulated))
            self.finished.emit(results, end_time)
        except (OSError, RuntimeError, ValueError) as error:
            self.failed.emit(f"Falha durante análise OpenCV: {error}")
        finally:
            capture.release()

    @staticmethod
    def _detect_damage_events(frame) -> list[tuple[int, int, int]]:
        import cv2

        height, width = frame.shape[:2]
        crop = frame[int(height * 0.05):int(height * 0.65), int(width * 0.10):int(width * 0.90)]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        bright_text = cv2.inRange(hsv, (0, 0, 180), (180, 125, 255))
        warm_text = cv2.inRange(hsv, (5, 65, 130), (45, 255, 255))
        mask = cv2.bitwise_or(bright_text, warm_text)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        components = []
        for contour in contours:
            x, y, item_width, item_height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area < 8 or item_width < 2 or item_height < 7:
                continue
            if item_width > 100 or item_height > 80 or item_width / max(1, item_height) > 4:
                continue
            components.append((x, y, item_width, item_height, area))
        components.sort(key=lambda item: (item[1], item[0]))
        groups: list[list[tuple[int, int, int, int, float]]] = []
        for component in components:
            x, y, item_width, item_height, _area = component
            center_y = y + item_height / 2
            if groups:
                group = groups[-1]
                group_center_y = sum(item[1] + item[3] / 2 for item in group) / len(group)
                group_right = max(item[0] + item[2] for item in group)
                if abs(center_y - group_center_y) <= max(12, item_height * 0.7) and x <= group_right + 28:
                    group.append(component)
                    continue
            groups.append([component])
        events = []
        for group in groups:
            left = min(item[0] for item in group)
            right = max(item[0] + item[2] for item in group)
            top = min(item[1] for item in group)
            bottom = max(item[1] + item[3] for item in group)
            group_width = right - left
            group_height = bottom - top
            if len(group) < 2 and group_width < 16:
                continue
            filled_area = sum(item[4] for item in group)
            density = min(1.0, filled_area / max(1, group_width * group_height))
            estimated_damage = int(min(9_999_999, max(100, group_width * group_height * (1.0 + density))))
            events.append((estimated_damage, int(width * 0.10 + (left + right) / 2), int(height * 0.05 + (top + bottom) / 2)))
        return events


class LiveDamageAnalysisWorker(QObject):
    damage_detected = Signal(dict)
    analysis_completed = Signal(dict)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        video_path: str,
        skip_seconds: float,
        end_seconds: float = 0.0,
        start_time: float | None = None,
    ) -> None:
        super().__init__()
        self.video_path = video_path
        self.skip_seconds = max(0.0, skip_seconds)
        self.end_seconds = max(0.0, end_seconds)
        self.start_time = max(0.0, start_time if start_time is not None else skip_seconds)
        self._cancelled = False
        self._position_lock = Lock()
        self._target_seconds = self.start_time
        self._frame_processing = False
        self._idle_interval = 0.22
        self._active_interval = 1.0 / OCR_SAMPLE_FPS
        self.no_damage_timeout = INACTIVITY_TIMEOUT

    def update_position(self, seconds: float) -> None:
        with self._position_lock:
            if self._frame_processing:
                return
            # Mailbox de um único frame: posições intermediárias são descartadas.
            self._target_seconds = max(0.0, float(seconds))

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        import cv2
        from rapidocr_onnxruntime import RapidOCR

        capture = cv2.VideoCapture(self.video_path, cv2.CAP_FFMPEG)
        try:
            if not capture.isOpened():
                self.failed.emit("Não foi possível abrir o vídeo para análise ao vivo")
                return
            cv2.setNumThreads(1)
            ocr = RapidOCR()
            fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration = frame_count / fps if frame_count else 0.0
            capture.set(cv2.CAP_PROP_POS_MSEC, self.start_time * 1000.0)
            initial_success, _initial_frame = capture.read()
            if not initial_success:
                self.failed.emit("Não foi possível posicionar o vídeo no início da análise")
                return
            recent: dict[tuple[int, int, int], float] = {}
            warmup_observations: set[tuple[int, int, int]] = set()
            warmup_started: float | None = None
            learned_profile: tuple[float, float, float] | None = None
            combat_confirmed = False
            last_position = -1.0
            accumulated = 0.0
            last_detection_time = -1.0
            # O timeout ignora todo o vídeo anterior ao início efetivo da análise.
            last_hit_time = self.start_time
            no_damage_timer = 0.0
            completion_reason = "video_end"
            while not self._cancelled:
                with self._position_lock:
                    target = self._target_seconds
                startup_window = self.start_time <= target < self.start_time + 2.0
                interval = 0.0 if startup_window else (
                    self._active_interval
                    if last_detection_time >= 0 and target - last_detection_time < 1.5
                    else self._idle_interval
                )
                if target < self.skip_seconds or abs(target - last_position) < interval:
                    QThread.msleep(45)
                    continue
                if duration:
                    target = min(target, duration)
                no_damage_timer = max(0.0, target - last_hit_time) if last_hit_time >= 0 else 0.0
                if self.end_seconds and target >= self.end_seconds:
                    completion_reason = "manual_limit"
                    break
                analysis_elapsed = max(0.0, target - self.start_time)
                if (
                    not self.end_seconds
                    and analysis_elapsed >= MIN_INACTIVITY_ANALYSIS_SECONDS
                    and no_damage_timer >= self.no_damage_timeout
                ):
                    completion_reason = "inactivity"
                    break
                capture.set(cv2.CAP_PROP_POS_MSEC, target * 1000.0)
                success, frame = capture.read()
                if not success:
                    QThread.msleep(70)
                    continue
                if not self._is_game_screen(frame):
                    last_position = target
                    QThread.msleep(45)
                    continue
                with self._position_lock:
                    self._frame_processing = True
                try:
                    values = self._read_values(frame, ocr)
                finally:
                    with self._position_lock:
                        self._frame_processing = False
                fresh_values = []
                for value, center_x, center_y, item_width, item_height, color_score in values:
                    if combat_confirmed and learned_profile is not None:
                        learned_width, learned_height, learned_color = learned_profile
                        size_match = (
                            learned_width * 0.45 <= item_width <= learned_width * 2.2
                            and learned_height * 0.45 <= item_height <= learned_height * 2.2
                        )
                        if not size_match or color_score < learned_color * 0.35:
                            continue
                    signature = (value, center_x // 50, center_y // 30)
                    previous = recent.get(signature)
                    if previous is not None and target - previous < 0.65:
                        continue
                    recent[signature] = target
                    if len(recent) > 2048:
                        cutoff = target - 4.0
                        recent = {
                            key: seen_at
                            for key, seen_at in recent.items()
                            if seen_at >= cutoff
                        }
                    fresh_values.append(value)
                    if not combat_confirmed:
                        warmup_observations.add(signature)
                        warmup_started = target if warmup_started is None else warmup_started
                if not combat_confirmed:
                    if len(warmup_observations) < 2 or warmup_started is None or target - warmup_started < 0.25:
                        last_position = target
                        QThread.msleep(45)
                        continue
                    combat_confirmed = True
                    learned_values = [item for item in values if (item[0], item[1] // 50, item[2] // 30) in warmup_observations]
                    if learned_values:
                        learned_profile = (
                            sum(item[3] for item in learned_values) / len(learned_values),
                            sum(item[4] for item in learned_values) / len(learned_values),
                            sum(item[5] for item in learned_values) / len(learned_values),
                        )
                damage = float(sum(fresh_values))
                accumulated += damage
                if fresh_values:
                    last_detection_time = target
                    last_hit_time = target
                    no_damage_timer = 0.0
                self.damage_detected.emit({
                    "timestamp": target,
                    "damage": damage,
                    "hits": len(fresh_values),
                    "peak": max(fresh_values, default=0),
                    "accumulated": accumulated,
                })
                last_position = target
                QThread.msleep(45)
        except (OSError, RuntimeError, ValueError) as error:
            self.failed.emit(f"Falha durante análise ao vivo: {error}")
        finally:
            capture.release()
            if not self._cancelled:
                self.analysis_completed.emit({
                    "reason": completion_reason,
                    "last_hit": last_hit_time,
                })
            self.finished.emit()

    @staticmethod
    def _is_game_screen(frame) -> bool:
        import cv2

        height, width = frame.shape[:2]
        scene = frame[int(height * 0.16):int(height * 0.62), int(width * 0.24):int(width * 0.76)]
        hsv = cv2.cvtColor(scene, cv2.COLOR_BGR2HSV)
        mean_value = float(hsv[:, :, 2].mean())
        saturated_ratio = float((hsv[:, :, 1] > 45).mean())
        dark_ratio = float((hsv[:, :, 2] < 85).mean())
        return mean_value < 232.0 and (saturated_ratio > 0.025 or dark_ratio > 0.12)

    @staticmethod
    def _read_values(frame, ocr: Any) -> list[tuple[int, int, int, int, int, float]]:
        import cv2

        height, width = frame.shape[:2]
        roi_top = int(height * 0.16)
        roi_bottom = int(height * 0.62)
        roi_left = int(width * 0.24)
        roi_right = int(width * 0.76)
        crop = frame[roi_top:roi_bottom, roi_left:roi_right]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        bright_mask = cv2.inRange(hsv, (0, 0, 175), (180, 145, 255))
        warm_mask = cv2.inRange(hsv, (5, 55, 120), (45, 255, 255))
        candidate_mask = cv2.bitwise_or(bright_mask, warm_mask)
        candidate_mask = cv2.morphologyEx(
            candidate_mask,
            cv2.MORPH_OPEN,
            cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2)),
        )
        contours, _ = cv2.findContours(candidate_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not any(cv2.contourArea(contour) >= 12 for contour in contours):
            return []
        enlarged = cv2.resize(crop, None, fx=1.15, fy=1.15, interpolation=cv2.INTER_LINEAR)
        result, _ = ocr(enlarged)
        values = []
        for item in result or []:
            if len(item) < 3:
                continue
            box, text, confidence = item
            digits = "".join(character for character in str(text) if character.isdigit())
            if not digits or len(digits) > 8 or float(confidence) < 0.35:
                continue
            value = int(digits)
            if value < 100 or value > 100_000:
                continue
            points = [(point[0] / 1.15, point[1] / 1.15) for point in box]
            left = max(0, int(min(point[0] for point in points)))
            top = max(0, int(min(point[1] for point in points)))
            right = min(crop.shape[1], int(max(point[0] for point in points)) + 1)
            bottom = min(crop.shape[0], int(max(point[1] for point in points)) + 1)
            patch = crop[top:bottom, left:right]
            if patch.size == 0:
                continue
            patch_hsv = cv2.cvtColor(patch, cv2.COLOR_BGR2HSV)
            bright_ratio = float((patch_hsv[:, :, 2] > 170).mean())
            color_ratio = float(((patch_hsv[:, :, 1] > 55) & (patch_hsv[:, :, 2] > 120)).mean())
            surrounding = crop[max(0, top - 8):min(crop.shape[0], bottom + 8), max(0, left - 8):min(crop.shape[1], right + 8)]
            surrounding_hsv = cv2.cvtColor(surrounding, cv2.COLOR_BGR2HSV)
            if float(surrounding_hsv[:, :, 2].mean()) > 238 and color_ratio < 0.08:
                continue
            color_score = max(color_ratio, bright_ratio * 0.35)
            if color_score < 0.12:
                continue
            center_x = int(sum(point[0] for point in points) / len(points) + roi_left)
            center_y = int(sum(point[1] for point in points) / len(points) + roi_top)
            values.append((value, center_x, center_y, max(1, right - left), max(1, bottom - top), color_score))
        return values


class DpsSimulationPanel(Card):
    def __init__(self, video_player: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.video_player = video_player
        self.duration_seconds = 163.0
        self._dps_start_time = 0.0
        self.live_thread: QThread | None = None
        self.live_worker: LiveDamageAnalysisWorker | None = None
        self._live_blocks: defaultdict[int, list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
        self._total_hits = 0
        self._peak_hit = 0
        self._hit_times: list[float] = []
        self._observed_damage = 0.0
        self._observed_dps = 0.0
        self.has_real_data = False
        self._pending_position_ms = 0
        self._plot_dirty = False
        self._plot_update_timer = QTimer(self)
        self._plot_update_timer.setInterval(66)
        self._plot_update_timer.timeout.connect(self._flush_plot_update)
        self._position_timer = QTimer(self)
        self._position_timer.setInterval(33)
        self._position_timer.timeout.connect(self._flush_position)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(8)

        header = QHBoxLayout()
        panel_title = QLabel("Simulação de DPS x Tempo")
        panel_title.setObjectName("mediaSectionTitle")
        header.addWidget(panel_title)
        dps_key = QLabel("●  DPS real")
        dps_key.setObjectName("dpsLegend")
        damage_key = QLabel("●  Dano Acumulado")
        damage_key.setObjectName("damageLegend")
        hit_key = QLabel("●  Hit = novo número de dano")
        hit_key.setObjectName("hitLegend")
        header.addWidget(dps_key)
        header.addWidget(damage_key)
        header.addWidget(hit_key)
        for legend in (dps_key, damage_key, hit_key):
            legend.hide()
        self.analysis_status = QLabel("Aguardando números reais")
        self.analysis_status.setObjectName("dpsAnalysisStatus")
        header.addWidget(self.analysis_status)
        self.hit_label = QLabel("Hits: 0")
        self.hit_label.setObjectName("dpsCursorLabel")
        header.addWidget(self.hit_label)
        self.position_label = QLabel("Cursor: 0.00s")
        self.position_label.setObjectName("dpsCursorLabel")
        header.addWidget(self.position_label, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header)

        metrics = QHBoxLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setSpacing(10)
        self.damage_metric = self._metric(metrics, "Dano acumulado")
        self.hits_metric = self._metric(metrics, "Hits")
        self.dps_metric = self._metric(metrics, "DPS médio")
        self.peak_metric = self._metric(metrics, "Maior hit")
        layout.addLayout(metrics)
        controls = QVBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(6)

        form = QHBoxLayout()
        form.setSpacing(6)
        self.skip_intro_time = self._time_box()
        self.analysis_start_time = self._time_box()
        self.analysis_end_time = self._time_box()
        form.addWidget(QLabel("Ignorar vinheta"))
        form.addWidget(self.skip_intro_time)
        form.addWidget(QLabel("Início da análise"))
        form.addWidget(self.analysis_start_time)
        form.addWidget(QLabel("Fim da análise"))
        form.addWidget(self.analysis_end_time)
        self.analyze_button = QPushButton("Análise ao vivo")
        self.analyze_button.setObjectName("dpsAnalyzeButton")
        self.analyze_button.setMinimumWidth(130)
        self.analyze_button.clicked.connect(self._toggle_live_analysis)
        form.addWidget(self.analyze_button)
        controls.addLayout(form)
        layout.addLayout(controls)

        self.plot = DpsPlotWidget(self)
        self.plot.setObjectName("dpsPlot")
        self.plot.getPlotItem().hideButtons()
        self.plot.setBackground("#080B18")
        self.plot.setMinimumHeight(141)
        self.plot.setMaximumHeight(260)
        self.plot.getPlotItem().layout.setContentsMargins(2, 2, 2, 2)
        self.plot.setLabel("bottom", "")
        self.plot.setLabel("left", "")
        self.plot.showAxis("right")
        damage_axis = self.plot.getPlotItem().getAxis("right")
        damage_axis.setLabel("")
        damage_axis.setWidth(68)
        damage_axis.setPen(pg.mkPen("#6870A8"))
        damage_axis.setTextPen(pg.mkPen("#C7C8EA"))
        self.damage_view = pg.ViewBox()
        self.plot.scene().addItem(self.damage_view)
        self.plot.getPlotItem().getAxis("right").linkToView(self.damage_view)
        self.damage_view.setXLink(self.plot.getPlotItem().vb)
        self.plot.getPlotItem().vb.sigResized.connect(self._sync_damage_view)
        self.plot.showGrid(x=True, y=True, alpha=0.16)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.getPlotItem().setMouseEnabled(x=False, y=False)
        self.plot.getPlotItem().setMenuEnabled(False)
        self.plot.setAntialiasing(False)
        self.plot.setClipToView(True)
        self.plot.setDownsampling(auto=True, mode="peak")
        self.plot.enableAutoRange(False)
        for axis_name in ("left", "bottom"):
            axis = self.plot.getPlotItem().getAxis(axis_name)
            axis.setPen(pg.mkPen("#6870A8"))
            axis.setTextPen(pg.mkPen("#C7C8EA"))
        self.glow_curve = self.plot.plot([], [], pen=pg.mkPen((0, 217, 255, 70), width=7))
        self.curve = self.plot.plot([], [], pen=pg.mkPen("#00D9FF", width=2.5))
        self.damage_glow_curve = pg.PlotDataItem(pen=pg.mkPen((61, 196, 255, 65), width=6))
        self.damage_curve = pg.PlotDataItem(pen=pg.mkPen("#55D6FF", width=2))
        self.damage_view.addItem(self.damage_glow_curve)
        self.damage_view.addItem(self.damage_curve)
        self.damage_peaks = pg.ScatterPlotItem(
            size=10,
            symbol="t",
            brush=pg.mkBrush("#FFD76A"),
            pen=pg.mkPen("#FFF4B0", width=1),
        )
        self.damage_lows = pg.ScatterPlotItem(
            size=8,
            symbol="o",
            brush=pg.mkBrush("#55D6FF"),
            pen=pg.mkPen("#C7F5FF", width=1),
        )
        self.plot.addItem(self.damage_peaks)
        self.plot.addItem(self.damage_lows)
        self.cursor = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#67D9FF", width=2),
        )
        self.plot.addItem(self.cursor)
        self.cutoff_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#FFD76A", width=2, style=Qt.PenStyle.DashLine),
        )
        self.cutoff_line.hide()
        self.plot.addItem(self.cutoff_line)
        self.mini_plot = pg.PlotWidget(self)
        self.mini_plot.setObjectName("dpsMiniPlot")
        self.mini_plot.getPlotItem().hideButtons()
        self.mini_plot.setBackground("#0B1023")
        self.mini_plot.setFixedHeight(14)
        self.mini_plot.hideAxis("left")
        self.mini_plot.hideAxis("bottom")
        self.mini_plot.setMouseEnabled(x=False, y=False)
        self.mini_plot.getPlotItem().setMenuEnabled(False)
        self.mini_plot.setAntialiasing(False)
        self.mini_plot.setClipToView(True)
        self.mini_plot.setDownsampling(auto=True, mode="peak")
        self.mini_plot.enableAutoRange(False)
        self.mini_curve = self.mini_plot.plot([], [], pen=pg.mkPen((117, 75, 255, 120), width=2))
        self.mini_markers = pg.ScatterPlotItem(size=7, brush=pg.mkBrush("#B77CFF"), pen=pg.mkPen("#FFFFFF", width=1))
        self.mini_plot.addItem(self.mini_markers)
        layout.addWidget(self.plot, 1)
        layout.addWidget(self.mini_plot)

        self.plot.timestampClicked.connect(self._seek_video)
        self.video_player.media_player.positionChanged.connect(
            self._queue_position,
            Qt.ConnectionType.QueuedConnection,
        )
        self.video_player.media_player.durationChanged.connect(self._on_duration_changed)
        self.video_player.videoLoaded.connect(self._on_video_loaded)
        self.video_player.videoStopped.connect(self._stop_live_analysis)
        self._render_curve()

    @staticmethod
    def _metric(layout: QHBoxLayout, title: str) -> QLabel:
        label = QLabel(f"{title}: --")
        label.setObjectName("dpsMetric")
        layout.addWidget(label, 1)
        return label

    @staticmethod
    def _time_box() -> QTimeEdit:
        control = QTimeEdit(QTime(0, 0, 0))
        control.setDisplayFormat("mm:ss")
        control.setTimeRange(QTime(0, 0, 0), QTime(23, 59, 59))
        control.setKeyboardTracking(False)
        control.setFixedWidth(78)
        return control

    def _render_curve(self) -> None:
        self.glow_curve.setData([], [])
        self.curve.setData([], [])
        self.damage_glow_curve.setData([], [])
        self.damage_curve.setData([], [])
        self.damage_peaks.setData([], [])
        self.damage_lows.setData([], [])
        self.mini_curve.setData([], [])
        self.mini_markers.setData([], [])
        self.plot.setXRange(0, max(1.0, self.duration_seconds), padding=0.02)
        self.plot.setYRange(0, 1, padding=0)
        self.plot.showAxis("bottom", True)
        self.plot.showAxis("left", False)
        self.plot.showAxis("right", True)
        self.plot.setTitle("Aguardando dano real do vídeo...", color="#A8A8D5", size="11pt")
        self.damage_metric.setText("Dano acumulado: --")
        self.hits_metric.setText("Hits: 0")
        self.dps_metric.setText("DPS médio: --")
        self.peak_metric.setText("Maior hit: --")
        self.damage_view.setYRange(0, 100, padding=0)
        if self._dps_start_time >= 0:
            self._render_initial_analysis_point()

    def _render_initial_analysis_point(self) -> None:
        self._set_plot_data(
            [self._dps_start_time],
            [0.0],
            [0.0],
            [],
            x_duration=self._analysis_end_seconds() or self.duration_seconds,
        )

    def _sync_damage_view(self) -> None:
        self.damage_view.setGeometry(self.plot.getPlotItem().vb.sceneBoundingRect())

    def _set_plot_data(
        self,
        times: list[float],
        values: list[float],
        accumulated: list[float],
        marker_times: list[float],
        x_duration: float | None = None,
    ) -> None:
        visible_duration = max(1.0, x_duration or self.duration_seconds)
        peak = max(values, default=1.0)
        total_damage = max(accumulated, default=0.0)
        scaled_accumulated = accumulated
        self.glow_curve.setData(times, values)
        self.curve.setData(times, values)
        self.damage_glow_curve.setData(times, scaled_accumulated)
        self.damage_curve.setData(times, scaled_accumulated)
        peak_points, low_points = self._extreme_points(times, values)
        self.damage_peaks.setData(
            x=[point[0] for point in peak_points],
            y=[point[1] for point in peak_points],
        )
        self.damage_lows.setData(
            x=[point[0] for point in low_points],
            y=[point[1] for point in low_points],
        )
        self.plot.showAxis("bottom", True)
        self.plot.showAxis("left", True)
        self.plot.showAxis("right", True)
        self.plot.setTitle("")
        self.plot.getAxis("left").setTicks(None)
        self.plot.getAxis("right").setTicks(None)
        self.plot.setXRange(0, visible_duration, padding=0.02)
        self.plot.setYRange(0, max(1.0, peak) * 1.12, padding=0)
        self.damage_view.setYRange(0, max(100.0, total_damage) * 1.12, padding=0)
        self._sync_damage_view()
        self.mini_curve.setData(times, values)
        visible_markers = [timestamp for timestamp in marker_times if timestamp <= visible_duration]
        self.mini_markers.setData(x=visible_markers, y=[max(1.0, peak) * 0.5] * len(visible_markers))
        self.mini_plot.setXRange(0, visible_duration, padding=0)
        self.mini_plot.setYRange(0, max(1.0, peak), padding=0)

    @staticmethod
    def _extreme_points(
        times: list[float], values: list[float]
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        """Find local damage peaks and meaningful low points for chart markers."""
        if len(values) < 3:
            return [], []
        peaks: list[tuple[float, float]] = []
        lows: list[tuple[float, float]] = []
        positive_values = [value for value in values if value > 0]
        floor = min(positive_values, default=0.0)
        for index in range(1, len(values) - 1):
            previous_value = values[index - 1]
            value = values[index]
            next_value = values[index + 1]
            if value <= 0:
                continue
            if value >= previous_value and value >= next_value and value > previous_value:
                peaks.append((times[index], value))
            if value <= previous_value and value <= next_value and value <= next_value and value <= floor * 1.15:
                lows.append((times[index], value))
        if not peaks:
            highest_index = max(range(len(values)), key=values.__getitem__)
            if values[highest_index] > 0:
                peaks.append((times[highest_index], values[highest_index]))
        return peaks, lows

    def _render_live_blocks(self) -> None:
        if not self._live_blocks:
            return
        block_seconds = ANALYSIS_BUCKET_SECONDS
        analysis_start = self._dps_start_time
        analysis_end = self._analysis_end_seconds()
        maximum_block = max(self._live_blocks)
        entries = [
            (index, self._live_blocks.get(index, [0.0, 0.0, 0.0]))
            for index in range(maximum_block + 1)
        ]
        times = [analysis_start]
        dps_values = [0.0]
        accumulated = [0.0]
        running_total = 0.0
        for _, values in entries:
            running_total += values[0]
            block_time = analysis_start + (len(times) - 0.5) * block_seconds
            if analysis_end:
                block_time = min(block_time, analysis_end)
            times.append(block_time)
            dps_values.append(values[0] / block_seconds)
            accumulated.append(running_total)
        self._set_plot_data(
            times,
            dps_values,
            accumulated,
            self._hit_times,
            x_duration=analysis_end or self.duration_seconds,
        )
        self._observed_damage = running_total
        last_observed_time = self._live_blocks[maximum_block][2]
        elapsed = max(0.0, min(last_observed_time, analysis_end or last_observed_time) - analysis_start)
        self._observed_dps = self._observed_damage / max(0.1, elapsed)
        self.damage_metric.setText(f"Dano acumulado: {self._observed_damage:,.0f}")
        self.hits_metric.setText(f"Hits: {self._total_hits}")
        self.dps_metric.setText(f"DPS médio: {self._observed_dps:,.0f}")
        self.peak_metric.setText(f"Maior hit: {self._peak_hit:,.0f}")

    def _on_video_loaded(self, video_path: str) -> None:
        self._start_live_analysis(video_path)

    def _analysis_start_seconds(self) -> float:
        """Return the manual video timestamp where live analysis should begin."""
        return self._time_to_seconds(self.analysis_start_time)

    def _scan_start_seconds(self) -> float:
        return max(
            self._time_to_seconds(self.skip_intro_time),
            self._analysis_start_seconds(),
        )

    def _analysis_end_seconds(self) -> float:
        """Return zero for an unlimited analysis end time."""
        return self._time_to_seconds(self.analysis_end_time)

    @staticmethod
    def _time_to_seconds(control: QTimeEdit) -> float:
        time = control.time()
        return float(time.hour() * 3600 + time.minute() * 60 + time.second())

    def _toggle_live_analysis(self) -> None:
        if self.live_worker is not None:
            self._stop_live_analysis()
            return
        video_path = getattr(self.video_player, "video_path", "")
        if video_path:
            self._start_live_analysis(video_path)
        else:
            self.analysis_status.setText("Carregue um vídeo primeiro")

    def _start_live_analysis(self, video_path: str) -> None:
        self._stop_live_analysis()
        self._dps_start_time = self._analysis_start_seconds()
        self._plot_update_timer.stop()
        self._plot_dirty = False
        self.cutoff_line.hide()
        self._live_blocks.clear()
        self._render_initial_analysis_point()
        self._total_hits = 0
        self._peak_hit = 0
        self._hit_times.clear()
        self.has_real_data = False
        self.damage_metric.setText("Dano acumulado: --")
        self.dps_metric.setText("DPS médio: --")
        self.peak_metric.setText("Maior hit: --")
        self.hit_label.setText("Hits: 0")
        self.analysis_status.setText(
            f"Aguardando números reais a partir de {self._analysis_start_seconds():.0f}s..."
        )
        self.analyze_button.setText("Parar análise")
        self.live_thread = QThread(self)
        self.live_worker = LiveDamageAnalysisWorker(
            video_path,
            self._scan_start_seconds(),
            self._analysis_end_seconds(),
            self._analysis_start_seconds(),
        )
        self.live_worker.moveToThread(self.live_thread)
        self.live_thread.started.connect(self.live_worker.run)
        self.live_worker.damage_detected.connect(self._on_live_damage)
        self.live_worker.analysis_completed.connect(self._on_analysis_completed)
        self.live_worker.failed.connect(self._on_live_failed)
        self.live_worker.finished.connect(self._on_live_finished)
        self.live_thread.finished.connect(self._on_live_thread_finished)
        self.live_thread.start()
        self.live_thread.setPriority(QThread.Priority.LowPriority)

    def _on_analysis_completed(self, data: dict) -> None:
        last_hit = float(data.get("last_hit", -1.0))
        if last_hit < 0:
            last_hit = self._pending_position_ms / 1000.0
        self.cutoff_line.setValue(last_hit)
        self.cutoff_line.show()
        self.analysis_status.setText(
            f"Concluída (Último hit em {self._clock_seconds(last_hit)})"
        )
        self._plot_dirty = True
        if not self._plot_update_timer.isActive():
            self._plot_update_timer.start()

    def _on_live_damage(self, data: dict) -> None:
        timestamp = float(data.get("timestamp", 0.0))
        damage = float(data.get("damage", 0.0))
        hits = int(data.get("hits", 0))
        peak = float(data.get("peak", 0.0))
        if damage <= 0 or hits <= 0:
            return
        if timestamp < self._dps_start_time:
            return
        block_seconds = ANALYSIS_BUCKET_SECONDS
        block_index = int(max(0.0, timestamp - self._dps_start_time) // block_seconds)
        block = self._live_blocks[block_index]
        block[0] += damage
        block[1] += hits
        block[2] = timestamp
        block[3] = max(block[3], peak)
        self._total_hits += hits
        self._peak_hit = max(self._peak_hit, peak)
        self._hit_times.extend([timestamp] * hits)
        self.has_real_data = True
        self._plot_dirty = True
        if not self._plot_update_timer.isActive():
            self._plot_update_timer.start()
        self.hit_label.setText(f"Hits: {self._total_hits}")
        self.analysis_status.setText(f"Ao vivo {self._clock_seconds(timestamp)}")

    def _flush_plot_update(self) -> None:
        if not self._plot_dirty:
            self._plot_update_timer.stop()
            return
        self._plot_dirty = False
        self._render_live_blocks()

    @staticmethod
    def _clock_seconds(seconds: float) -> str:
        total = max(0, int(seconds))
        return f"{total // 60}:{total % 60:02d}"

    def _on_live_failed(self, message: str) -> None:
        self.analysis_status.setText(message)
        self._stop_live_analysis()

    def _on_live_finished(self) -> None:
        if self.live_thread is not None:
            self.live_thread.quit()

    def _on_live_thread_finished(self) -> None:
        if self.live_worker is not None:
            self.live_worker.deleteLater()
        thread = self.live_thread
        self.live_worker = None
        self.live_thread = None
        self.analyze_button.setText("Análise ao vivo")
        if thread is not None:
            thread.deleteLater()

    def _stop_live_analysis(self) -> None:
        if self.live_worker is not None:
            self.live_worker.cancel()
            self.analysis_status.setText("Análise ao vivo parada")

    def _on_duration_changed(self, duration_ms: int) -> None:
        if duration_ms > 0:
            self.duration_seconds = duration_ms / 1000.0
            if not self.has_real_data:
                self._render_curve()

    def _queue_position(self, position_ms: int) -> None:
        self._pending_position_ms = position_ms
        if not self._position_timer.isActive():
            self._position_timer.start()

    def _flush_position(self) -> None:
        self._position_timer.stop()
        position_ms = self._pending_position_ms
        seconds = max(0.0, position_ms / 1000.0)
        self.cursor.setValue(seconds)
        self.position_label.setText(f"Cursor: {seconds:.2f}s")
        if self.live_worker is not None:
            self.live_worker.update_position(seconds)

    def _seek_video(self, seconds: float) -> None:
        self.video_player.seek_to_seconds(max(0.0, min(self.duration_seconds, seconds)))
