"""Background video analysis workers independent of plot widgets."""

from __future__ import annotations

import math
import traceback
from collections import defaultdict

from PySide6.QtCore import QObject, Signal

ANALYSIS_BUCKET_SECONDS = 5.0


INACTIVITY_TIMEOUT = 12.0


MIN_INACTIVITY_ANALYSIS_SECONDS = 15.0


OCR_SAMPLE_FPS = 8.0


class CvDamageAnalysisWorker(QObject):
    """Analyze video frames and emit damage candidates."""

    progress = Signal(int)
    finished = Signal(object, float)
    failed = Signal(str)

    def __init__(
        self, video_path: str, skip_seconds: float, block_seconds: float
    ) -> None:
        super().__init__()
        self.video_path = video_path
        self.skip_seconds = max(0.0, skip_seconds)
        self.block_seconds = max(1.0, block_seconds)
        self._cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the active analysis worker."""
        self._cancelled = True

    def run(self) -> None:
        # Adia dependências de vídeo até o uso da análise.
        """Execute the worker and emit its result or failure signal."""
        # Keep ordered widget construction and painting steps together.
        # pylint: disable=too-many-locals
        # Load this optional/heavy dependency only when the action runs.
        # pylint: disable-next=import-outside-toplevel
        import cv2

        capture = cv2.VideoCapture(self.video_path, cv2.CAP_FFMPEG)
        if not capture.isOpened():
            self.failed.emit(
                "Não foi possível abrir o vídeo para análise OpenCV"
            )
            return
        try:
            fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            duration = frame_count / fps if frame_count else 0.0
            capture.set(cv2.CAP_PROP_POS_MSEC, self.skip_seconds * 1000.0)
            buckets: defaultdict[int, float] = defaultdict(float)
            recent_detections: dict[
                tuple[int, int, int], tuple[float, float]
            ] = {}
            frame_index = int(self.skip_seconds * fps)
            last_progress = -1
            while not self._cancelled:
                success, frame = capture.read()
                if not success:
                    break
                timestamp = frame_index / fps
                for value, center_x, center_y in self._detect_damage_events(
                    frame
                ):
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
            block_count = max(
                1,
                math.ceil(
                    max(0.0, end_time - self.skip_seconds) / self.block_seconds
                ),
            )
            results = []
            accumulated = 0.0
            for index in range(block_count):
                damage = buckets.get(
                    index + int(self.skip_seconds // self.block_seconds), 0.0
                )
                accumulated += damage
                timestamp = (
                    self.skip_seconds + (index + 1) * self.block_seconds
                )
                results.append(
                    (
                        min(timestamp, end_time),
                        damage / self.block_seconds,
                        accumulated,
                    )
                )
            self.finished.emit(results, end_time)
        except (OSError, RuntimeError, ValueError) as error:
            self.failed.emit(f"Falha durante análise OpenCV: {error}")
        finally:
            capture.release()

    @staticmethod
    def _detect_damage_events(frame) -> list[tuple[int, int, int]]:
        # Adia dependências de vídeo até o uso da análise.
        # Keep ordered widget construction and painting steps together.
        # pylint: disable=too-many-locals
        # Load this optional/heavy dependency only when the action runs.
        # pylint: disable-next=import-outside-toplevel
        import cv2

        height, width = frame.shape[:2]
        crop = frame[
            int(height * 0.05) : int(height * 0.65),
            int(width * 0.10) : int(width * 0.90),
        ]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        bright_text = cv2.inRange(hsv, (0, 0, 180), (180, 125, 255))
        warm_text = cv2.inRange(hsv, (5, 65, 130), (45, 255, 255))
        mask = cv2.bitwise_or(bright_text, warm_text)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        components = []
        for contour in contours:
            x, y, item_width, item_height = cv2.boundingRect(contour)
            area = cv2.contourArea(contour)
            if area < 8 or item_width < 2 or item_height < 7:
                continue
            if (
                item_width > 100
                or item_height > 80
                or item_width / max(1, item_height) > 4
            ):
                continue
            components.append((x, y, item_width, item_height, area))
        components.sort(key=lambda item: (item[1], item[0]))
        groups: list[list[tuple[int, int, int, int, float]]] = []
        for component in components:
            x, y, item_width, item_height, _area = component
            center_y = y + item_height / 2
            if groups:
                group = groups[-1]
                group_center_y = sum(
                    item[1] + item[3] / 2 for item in group
                ) / len(group)
                group_right = max(item[0] + item[2] for item in group)
                if (
                    abs(center_y - group_center_y)
                    <= max(12, item_height * 0.7)
                    and x <= group_right + 28
                ):
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
            density = min(
                1.0, filled_area / max(1, group_width * group_height)
            )
            estimated_damage = int(
                min(
                    9_999_999,
                    max(100, group_width * group_height * (1.0 + density)),
                )
            )
            events.append(
                (
                    estimated_damage,
                    int(width * 0.10 + (left + right) / 2),
                    int(height * 0.05 + (top + bottom) / 2),
                )
            )
        return events


class LiveDamageAnalysisWorker(QObject):
    """Executa a engine C++ nativa e publica seus eventos para a interface.

    A detecção, OCR, filtragem, rastreamento e deduplicação pertencem à
    engine.
    A análise roda em um processo separado, sem compartilhar bibliotecas
    com Qt.
    Esta classe apenas adapta o resultado nativo aos sinais Qt já
    consumidos
    pelo painel. O streaming incremental será adicionado na próxima
    etapa.
    """

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
        self.start_time = max(
            0.0, start_time if start_time is not None else skip_seconds
        )
        self._cancelled = False

    def update_position(self, seconds: float) -> None:
        # Mantido por compatibilidade com o painel atual. A engine analisa o
        # intervalo selecionado, sem depender da posição de reprodução.
        """Accept player position updates for the analysis worker."""
        # Retain keyword/signal compatibility with existing callers.
        # pylint: disable=unused-argument
        return

    def cancel(self) -> None:
        """Request cancellation of the active analysis worker."""
        self._cancelled = True

    def run(self) -> None:
        """Execute the worker and emit its result or failure signal."""
        try:
            if self._cancelled:
                return

            # Adia dependências de vídeo até o uso da análise.
            # pylint: disable-next=import-outside-toplevel
            from wuwa_calculator.infrastructure.video_analysis import (
                analyze_isolated,
            )

            scan_start = max(self.skip_seconds, self.start_time)
            data = analyze_isolated(
                self.video_path,
                scan_start,
                self.end_seconds if self.end_seconds > scan_start else -1.0,
                lambda: self._cancelled,
            )
            if data is None or self._cancelled:
                return

            for event in data["events"]:
                if self._cancelled:
                    return
                self.damage_detected.emit(
                    {
                        **event,
                        "hits": 1,
                        "peak": event["damage"],
                        "accumulated": 0.0,
                    }
                )
            data["video_path"] = self.video_path
            self.analysis_completed.emit(data)
        # Thread boundary: relay every worker failure through its Qt signal.
        # pylint: disable-next=broad-exception-caught
        except Exception as error:
            # Report unexpected pybind11/API errors too; otherwise the
            # QThread can
            # end without a useful message and the UI appears to do nothing.
            details = traceback.format_exc()
            self.failed.emit(
                f"Falha na engine nativa ({type(error).__name__}):"
                f" {error}\n\n{details}"
            )
        finally:
            # Sempre emite: o QThread só encerra seu loop de eventos por este
            # sinal. Cada worker está ligado ao seu próprio thread (veja
            # _start_live_analysis), então um worker cancelado não afeta
            # o novo.
            self.finished.emit()
