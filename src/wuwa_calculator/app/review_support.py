"""Liga a análise da engine à revisão pelo usuário.

O painel de DPS só precisa de quatro coisas daqui:
    support = ReviewSupport(parent)       # cria o seletor de modo
    layout.addWidget(support.widget)      # mostra o seletor
    support.begin(data)                   # chamado quando a análise termina
    support.hits_replaced / totals_changed (sinais)  # resultado final

As regras de soma ficam em `domain.review`; esta classe só trata de Qt,
de buscar os recortes no vídeo e de gravar os exemplos de treino.
"""

from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QSettings, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from ..domain.review import (
    DamageTotals,
    HitEvent,
    ReviewDecision,
    ReviewMode,
    compute_totals,
    final_parts,
    review_queue,
)
from ..infrastructure.training_samples import TrainingSampleStore, new_session_id

# Instantes (s, relativos ao hit) recortados para a revisão e para o treino.
CROP_OFFSETS = (0.0, 0.1, 0.2)

_SETTINGS_ORG = "Tethys"
_SETTINGS_APP = "Tethys"


class _CropWorker(QObject):
    done = Signal(dict)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, extract: Callable[..., Any], video_path: str,
                 raw_events: list[Any], indices: list[int]) -> None:
        super().__init__()
        self._extract = extract
        self._video_path = video_path
        self._raw_events = raw_events
        self._indices = indices

    def run(self) -> None:
        try:
            crops = self._extract(
                self._video_path, self._raw_events, 0.6, list(CROP_OFFSETS), 96
            )
            self.done.emit(
                {index: list(images) for index, images in zip(self._indices, crops)}
            )
        except Exception as error:  # pybind11/IO: não pode derrubar a UI
            self.failed.emit(f"{type(error).__name__}: {error}\n{traceback.format_exc()}")
        finally:
            self.finished.emit()


class ReviewSupport(QObject):
    hits_replaced = Signal(list)    # [{"timestamp","damage","hits","peak"}, ...]
    totals_changed = Signal(dict)   # {"total_damage","total_hits","peak_damage","note"}

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)

        self._events: list[HitEvent] = []
        self._raw_events: list[Any] = []
        self._video_path = ""
        self._extract: Callable[..., Any] | None = None
        self._decisions: dict[int, ReviewDecision] = {}
        self._crops: dict[int, list[bytes]] = {}
        self._session = new_session_id()
        self._thread: QThread | None = None
        self._worker: _CropWorker | None = None
        self._loading_crops = False
        self._crops_attempted = False
        self._pending_callback: Callable[[], None] | None = None

        self.widget = QWidget()
        row = QHBoxLayout(self.widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        row.addWidget(QLabel("Modo"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Somente a engine", ReviewMode.AUTOMATIC.value)
        self.mode_combo.addItem("Com revisão minha", ReviewMode.REVIEW.value)
        self.mode_combo.setToolTip(
            "Somente a engine: o total usa só o que ela confirma.\n"
            "Com revisão: você confere os hits duvidosos (números sobrepostos "
            "ou empilhados) e o total usa a sua decisão."
        )
        row.addWidget(self.mode_combo)
        self.collect_check = QCheckBox("Guardar exemplos para treinar a IA local")
        self.collect_check.setToolTip(
            "Salva só o recorte do número e o valor que você confirmou, em uma "
            "pasta do seu computador. Nada é enviado para fora."
        )
        row.addWidget(self.collect_check)
        self.review_button = QPushButton("Revisar")
        self.review_button.clicked.connect(self.open_review)
        self.review_button.hide()
        row.addWidget(self.review_button)
        self.note_label = QLabel("")
        self.note_label.setWordWrap(True)
        row.addWidget(self.note_label, 1)

        saved_mode = str(self._settings.value("review/mode", ReviewMode.AUTOMATIC.value))
        index = max(0, self.mode_combo.findData(saved_mode))
        self.mode_combo.setCurrentIndex(index)
        self.collect_check.setChecked(
            str(self._settings.value("review/collect", "false")).lower() == "true"
        )
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.collect_check.toggled.connect(
            lambda on: self._settings.setValue("review/collect", "true" if on else "false")
        )

    # ------------------------------------------------------------------ estado
    @property
    def mode(self) -> ReviewMode:
        return ReviewMode(self.mode_combo.currentData())

    def begin(self, data: dict) -> None:
        """Recebe o resultado da engine (dict de `analysis_completed`)."""
        raw = list(data.get("events") or [])
        self._raw_events = raw
        self._events = [HitEvent.from_engine(i, e) for i, e in enumerate(raw)]
        self._video_path = str(data.get("video_path") or "")
        self._extract = data.get("extract_crops")
        self._decisions = {}
        self._crops = {}
        self._crops_attempted = False
        self._session = new_session_id()
        self._apply(open_dialog=True)

    def reset(self) -> None:
        """Chamado quando uma nova análise começa."""
        self._events, self._raw_events = [], []
        self._decisions, self._crops = {}, {}
        self._crops_attempted = False
        self.review_button.hide()
        self.note_label.setText("")

    def totals(self) -> DamageTotals:
        return compute_totals(self._events, self.mode, self._decisions)

    # ------------------------------------------------------------------ fluxo
    def _on_mode_changed(self, *_args) -> None:
        self._settings.setValue("review/mode", self.mode.value)
        if self._events:
            self._apply(open_dialog=True)

    def _apply(self, open_dialog: bool) -> None:
        """Recalcula totais/gráfico e, no modo revisão, abre a conferência."""
        self._emit_results()
        queue = review_queue(self._events)

        if self.mode is not ReviewMode.REVIEW or not queue:
            self.review_button.hide()
            return

        self.review_button.setText(f"Revisar ({len(queue)})")
        self.review_button.show()
        if open_dialog and not self._decisions:
            self._ensure_crops_then(self.open_review)

    def _emit_results(self) -> None:
        totals = self.totals()
        hits = []
        for event, parts in final_parts(self._events, self.mode, self._decisions):
            for part in parts:
                hits.append({
                    "timestamp": event.timestamp,
                    "damage": float(part.damage),
                    "hits": part.copies,
                    "peak": float(part.value),
                })
        note = self._note(totals)
        self.note_label.setText(note)
        self.hits_replaced.emit(hits)
        self.totals_changed.emit({
            "total_damage": float(totals.total_damage),
            "total_hits": totals.hits,
            "peak_damage": float(totals.peak_damage),
            "note": note,
        })

    def _note(self, totals: DamageTotals) -> str:
        if self.mode is ReviewMode.REVIEW:
            if totals.pending_items:
                return f"{totals.pending_items} hit(s) duvidoso(s) sem revisão."
            return f"Revisão concluída ({totals.reviewed_hits} conferidos)."
        if totals.pending_items:
            return (
                f"{totals.pending_items} hit(s) duvidoso(s) "
                f"({totals.pending_damage:,} de dano) fora do total."
            )
        return ""

    # ------------------------------------------------------------------ recortes
    def _ensure_crops_then(self, callback: Callable[[], None]) -> None:
        queue = review_queue(self._events)
        if self._crops_attempted or all(e.index in self._crops for e in queue):
            QTimer.singleShot(0, callback)
            return
        if self._loading_crops:
            return
        if self._extract is None or not self._video_path:
            # Engine antiga ou sem vídeo: a revisão abre sem imagens.
            self._crops_attempted = True
            QTimer.singleShot(0, callback)
            return

        self._loading_crops = True
        self.note_label.setText("Preparando as imagens para revisão...")
        self.review_button.setEnabled(False)

        thread = QThread(self)
        worker = _CropWorker(
            self._extract,
            self._video_path,
            [self._raw_events[e.index] for e in queue],
            [e.index for e in queue],
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        # Slots de QObject (não lambdas): rodam na thread da interface.
        worker.done.connect(self._on_crops_ready)
        worker.failed.connect(self._on_crops_failed)
        worker.finished.connect(thread.quit)
        thread.finished.connect(self._on_crops_thread_finished)
        self._pending_callback = callback
        self._thread, self._worker = thread, worker
        thread.start()

    def _on_crops_ready(self, crops: dict) -> None:
        self._crops.update(crops)

    def _on_crops_failed(self, message: str) -> None:
        self.note_label.setText("Não foi possível extrair as imagens do vídeo.")

    def _on_crops_thread_finished(self) -> None:
        callback = self._pending_callback
        self._pending_callback = None
        self._loading_crops = False
        self._crops_attempted = True
        self.review_button.setEnabled(True)
        if self._thread is not None:
            self._thread.deleteLater()
        if self._worker is not None:
            self._worker.deleteLater()
        self._thread = self._worker = None
        self.note_label.setText(self._note(self.totals()))
        if callback is not None:
            callback()

    # ------------------------------------------------------------------ diálogo
    def open_review(self) -> None:
        queue = review_queue(self._events)
        if not queue:
            return
        if not self._crops_attempted and any(e.index not in self._crops for e in queue):
            self._ensure_crops_then(self.open_review)
            return

        from ..ui.dialogs.damage_review_dialog import DamageReviewDialog

        dialog = DamageReviewDialog(
            queue, self._crops, self.widget.window(), initial=self._decisions
        )
        accepted = dialog.exec() == DamageReviewDialog.DialogCode.Accepted
        if not accepted:
            return
        self._decisions = dict(dialog.decisions)
        self._save_training(queue)
        self._emit_results()
        self.review_button.setText(f"Revisar ({len(queue)})")

    def _save_training(self, queue: list[HitEvent]) -> None:
        if not self.collect_check.isChecked():
            return
        store = TrainingSampleStore()
        saved = 0
        try:
            for event in queue:
                decision = self._decisions.get(event.index)
                crops = self._crops.get(event.index)
                if decision is None or not crops:
                    continue
                if store.save(self._session, event, decision, crops, CROP_OFFSETS):
                    saved += 1
        except OSError:
            self.note_label.setText("Não foi possível gravar os exemplos de treino.")
            return
        if saved:
            self.note_label.setText(
                f"{self._note(self.totals())} {saved} exemplo(s) guardado(s) para treino."
            )
