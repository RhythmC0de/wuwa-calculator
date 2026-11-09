"""Plot widgets loaded only when a video needs a damage timeline."""

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget


class DpsPlotWidget(pg.PlotWidget):
    """DPS plot that emits the timestamp selected by the user."""

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
    # AxisItem provides SVG rendering through its graphics-item implementation.
    # pylint: disable=abstract-method
    """Format plot tick labels as grouped numeric values."""

    def tickStrings(self, values, scale, spacing):
        return [f"{value:,.0f}" for value in values]


class TimelineAxis(pg.AxisItem):
    # AxisItem provides SVG rendering through its graphics-item implementation.
    # pylint: disable=abstract-method
    """Format plot tick labels as minutes and seconds."""

    def tickStrings(self, values, scale, spacing):
        labels = []
        for value in values:
            total = max(0, int(value))
            labels.append(f"{total // 60}:{total % 60:02d}")
        return labels
