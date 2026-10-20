"""Tela de revisão dos hits que a engine não conseguiu fechar sozinha."""

from __future__ import annotations

from typing import Mapping, Sequence

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ...domain.review import (
    HitEvent,
    ParseError,
    ReviewDecision,
    accept,
    correct,
    discard,
    format_parts,
    parse_parts,
)

CROP_MAX_WIDTH = 380
CROP_MAX_HEIGHT = 200


def _clock(seconds: float) -> str:
    minutes, rest = divmod(max(0.0, seconds), 60.0)
    return f"{int(minutes):02d}:{rest:04.1f}"


def _why(event: HitEvent) -> str:
    if event.stacked:
        return (
            "Vários números iguais empilhados no mesmo lugar. A engine sabe o "
            "valor, mas não quantas vezes ele apareceu."
        )
    return (
        "Os dígitos parecem sobrepostos (o número lido pode ser a mistura de "
        "dois ou mais). Confira a imagem."
    )


class DamageReviewDialog(QDialog):
    """Mostra um item por vez e coleta uma decisão para cada um.

    `crops[event.index]` é a lista de PNGs do evento (um por instante). A
    janela não lê vídeo nem grava nada: devolve `decisions` e quem chamou
    decide o que fazer com elas.
    """

    def __init__(
        self,
        queue: Sequence[HitEvent],
        crops: Mapping[int, Sequence[bytes]],
        parent: QWidget | None = None,
        initial: Mapping[int, ReviewDecision] | None = None,
    ) -> None:
        super().__init__(parent)
        self._queue = list(queue)
        self._crops = crops
        self.decisions: dict[int, ReviewDecision] = dict(initial or {})
        self._position = 0

        self.setWindowTitle("Revisar hits duvidosos")
        self.setModal(True)
        self.resize(900, 520)

        root = QVBoxLayout(self)
        root.setSpacing(10)

        self.progress_label = QLabel()
        self.progress_label.setObjectName("mediaSectionTitle")
        root.addWidget(self.progress_label)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        root.addWidget(self.info_label)

        self.images_row = QHBoxLayout()
        self.images_row.setSpacing(8)
        images_host = QWidget()
        images_host.setLayout(self.images_row)
        images_host.setMinimumHeight(CROP_MAX_HEIGHT + 8)
        root.addWidget(images_host, 1)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        edit_row = QHBoxLayout()
        edit_row.addWidget(QLabel("Valor(es) corretos:"))
        self.values_edit = QLineEdit()
        self.values_edit.setPlaceholderText("Ex.: 785 + 2518   ou   2071 x3")
        self.values_edit.setClearButtonEnabled(True)
        self.values_edit.returnPressed.connect(self._apply_correction)
        edit_row.addWidget(self.values_edit, 1)
        self.apply_button = QPushButton("Aplicar correção")
        self.apply_button.clicked.connect(self._apply_correction)
        edit_row.addWidget(self.apply_button)
        root.addLayout(edit_row)

        copies_row = QHBoxLayout()
        self.copies_label = QLabel("Cópias deste valor:")
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 50)
        self.copies_spin.setValue(2)
        self.accept_button = QPushButton("Aceitar leitura da engine  (A)")
        self.accept_button.clicked.connect(self._accept_reading)
        self.discard_button = QPushButton("Não é dano  (D)")
        self.discard_button.clicked.connect(self._discard)
        copies_row.addWidget(self.copies_label)
        copies_row.addWidget(self.copies_spin)
        copies_row.addStretch(1)
        copies_row.addWidget(self.accept_button)
        copies_row.addWidget(self.discard_button)
        root.addLayout(copies_row)

        nav = QHBoxLayout()
        self.previous_button = QPushButton("◀ Anterior")
        self.previous_button.clicked.connect(lambda: self._go(-1))
        self.next_button = QPushButton("Próximo ▶")
        self.next_button.clicked.connect(lambda: self._go(1))
        self.finish_button = QPushButton("Concluir revisão")
        self.finish_button.setDefault(False)
        self.finish_button.clicked.connect(self._finish)
        nav.addWidget(self.previous_button)
        nav.addWidget(self.next_button)
        nav.addStretch(1)
        nav.addWidget(self.finish_button)
        root.addLayout(nav)

        for key, handler in (
            ("A", self._accept_reading),
            ("D", self._discard),
            ("Left", lambda: self._go(-1)),
            ("Right", lambda: self._go(1)),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
            shortcut.activated.connect(handler)

        self._show_current()

    # ---------------------------------------------------------------- estado
    @property
    def _event(self) -> HitEvent:
        return self._queue[self._position]

    def _decided_count(self) -> int:
        return sum(1 for e in self._queue if e.index in self.decisions)

    def _show_current(self) -> None:
        event = self._event
        total = len(self._queue)
        self.progress_label.setText(
            f"Item {self._position + 1} de {total}  ·  "
            f"{self._decided_count()} revisados"
        )
        flags = []
        if event.stacked:
            flags.append("empilhado")
        if not event.confirmed:
            flags.append("não confirmado")
        self.info_label.setText(
            f"<b>{_clock(event.timestamp)}</b> · a engine leu "
            f"<b>{event.damage:,}</b> ({', '.join(flags) or 'ok'})<br>"
            f"{_why(event)}"
        )

        self._render_images(event)

        existing = self.decisions.get(event.index)
        if existing is not None and existing.parts:
            self.values_edit.setText(format_parts(existing.parts))
        elif event.stacked:
            self.values_edit.setText(f"{event.damage} x2")
        else:
            self.values_edit.setText(str(event.damage))
        self.copies_spin.setValue(
            existing.parts[0].copies
            if existing is not None and len(existing.parts) == 1
            else 2
        )

        # A contagem de cópias só faz sentido quando há um único valor repetido.
        self.copies_label.setVisible(event.stacked)
        self.copies_spin.setVisible(event.stacked)

        self.status_label.setText(self._decision_text(existing))
        self.previous_button.setEnabled(self._position > 0)
        self.next_button.setEnabled(self._position < total - 1)
        self.values_edit.setFocus()
        self.values_edit.selectAll()

    @staticmethod
    def _decision_text(decision: ReviewDecision | None) -> str:
        if decision is None:
            return "Sem decisão ainda: vale o que a engine contaria sozinha."
        if not decision.parts:
            return "Decisão: não é dano (fora do total)."
        return f"Decisão: {format_parts(decision.parts)}  →  {decision.damage:,} de dano."

    def _render_images(self, event: HitEvent) -> None:
        while self.images_row.count():
            item = self.images_row.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        shown = 0
        for png in self._crops.get(event.index, ()):
            if not png:
                continue
            pixmap = QPixmap()
            if not pixmap.loadFromData(bytes(png), "PNG"):
                continue
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setPixmap(
                pixmap.scaled(
                    CROP_MAX_WIDTH,
                    CROP_MAX_HEIGHT,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            self.images_row.addWidget(label, 1)
            shown += 1

        if shown == 0:
            self.images_row.addWidget(
                QLabel("Não foi possível ler o frame deste hit no vídeo."), 1
            )

    # ---------------------------------------------------------------- ações
    def _store(self, decision: ReviewDecision) -> None:
        self.decisions[self._event.index] = decision
        if self._position < len(self._queue) - 1:
            self._position += 1
        self._show_current()

    def _accept_reading(self) -> None:
        event = self._event
        copies = self.copies_spin.value() if event.stacked else None
        self._store(accept(event, copies))

    def _discard(self) -> None:
        self._store(discard(self._event))

    def _apply_correction(self) -> None:
        try:
            parts = parse_parts(self.values_edit.text())
        except ParseError as error:
            self.status_label.setText(f"⚠ {error}")
            return
        event = self._event
        pairs = [(p.value, p.copies) for p in parts]
        # Texto igual à leitura da engine, com a mesma contagem, é "aceitar".
        if len(pairs) == 1 and pairs[0] == (event.damage, 1) and not event.stacked:
            self._store(accept(event))
        else:
            self._store(correct(event, pairs))

    def _go(self, step: int) -> None:
        target = self._position + step
        if 0 <= target < len(self._queue):
            self._position = target
            self._show_current()

    def _finish(self) -> None:
        pending = len(self._queue) - self._decided_count()
        if pending:
            answer = QMessageBox.question(
                self,
                "Concluir revisão",
                f"{pending} item(ns) sem decisão. Eles seguem a regra "
                "automática (não confirmados ficam fora do total). Concluir?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.accept()
