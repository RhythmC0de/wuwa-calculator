"""Testes do read_text (API_LEVEL 4) sem precisar do modelo de detecção.

1. Leitura de texto completo com caixas conhecidas, numa ficha sintética.
2. Pós-processamento do detector com um mapa de probabilidade sintético.

Uso: python text_reader_test.py <pasta com o módulo compilado>
"""

import importlib
import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, sys.argv[1])
d = importlib.import_module("damage_analyzer")

assert d.API_LEVEL >= 4, d.API_LEVEL

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)
font_path = next((p for p in FONT_CANDIDATES if os.path.exists(p)), None)
font = (
    ImageFont.truetype(font_path, 30)
    if font_path
    else ImageFont.load_default()
)

ROWS = [
    ("HP", "15290"),
    ("ATK", "2387"),
    ("DEF", "1202"),
    ("Energy Regen", "139.2%"),
    ("Crit. Rate", "68.6%"),
    ("Crit. DMG", "260%"),
]

image = Image.new("RGB", (900, 120 + 60 * len(ROWS)), (28, 34, 46))
draw = ImageDraw.Draw(image)
boxes, expected = [], []
for i, (label, value) in enumerate(ROWS):
    y = 60 + i * 60
    draw.text((60, y), label, fill=(240, 240, 240), font=font)
    lx0, ly0, lx1, ly1 = draw.textbbox((60, y), label, font=font)
    vw = draw.textlength(value, font=font)
    draw.text((840 - vw, y), value, fill=(240, 200, 90), font=font)
    vx0, vy0, vx1, vy1 = draw.textbbox((840 - vw, y), value, font=font)
    for box, text in (
        ((lx0, ly0, lx1, ly1), label),
        ((vx0, vy0, vx1, vy1), value),
    ):
        boxes.append(
            [
                int(box[0]),
                int(box[1]),
                int(box[2] - box[0]),
                int(box[3] - box[1]),
            ]
        )
        expected.append(text)

with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "card.png")
    image.save(path)
    lines = d.read_text(path, boxes=boxes, min_confidence=0.0)

got = [line.text for line in lines]
print("lido:     ", got)
print("esperado: ", expected)
mismatch = [
    (g, e)
    for g, e in zip(got, expected)
    if g.replace(" ", "") != e.replace(" ", "")
]
assert len(got) == len(expected), (len(got), len(expected))
assert not mismatch, mismatch
for line, box in zip(lines, boxes):
    assert (
        abs(line.x - (box[0] + box[2] / 2)) < 1.0
        and abs(line.y - (box[1] + box[3] / 2)) < 1.0
    )

# Sem modelo de detecção e sem caixas: o detector clássico acha as linhas.
with tempfile.TemporaryDirectory() as tmp:
    path = os.path.join(tmp, "card.png")
    image.save(path)
    found_boxes = d.detect_text_boxes(path)
    auto = d.read_text(
        path,
        detection_model_path=os.path.join(tmp, "nao_existe.onnx"),
        min_confidence=0.0,
    )
print("clássico:", [line.text for line in auto])
assert len(found_boxes) >= len(expected) - 3, len(found_boxes)
# Palavras de um mesmo rótulo podem sair em caixas separadas; os valores não.
auto_text = {line.text.replace(" ", "") for line in auto}
values = {v.replace(" ", "") for _, v in ROWS}
assert values <= auto_text, values - auto_text
assert {"ATK", "DEF"} <= auto_text, auto_text

# Pós-processamento do DBNet: duas linhas de texto num mapa 100x200
rows = [[0.0] * 200 for _ in range(100)]


def fill(x0, y0, x1, y1, probability=0.9):
    """Fill a rectangular region in the synthetic probability map."""
    for row_index in range(y0, y1):
        for column_index in range(x0, x1):
            rows[row_index][column_index] = probability


fill(20, 20, 80, 30)  # linha de cima, à esquerda
fill(120, 21, 180, 31)  # mesma altura, à direita
fill(20, 60, 100, 70)  # linha de baixo
fill(150, 85, 160, 87, 0.9)  # fino demais (2 px): descartado
fill(40, 90, 60, 96, 0.4)  # nota baixa: descartado
# Exercise the diagnostic API for detector post-processing.
# pylint: disable-next=protected-access
found = d._boxes_from_probability_map(rows, 400, 200)  # escala 2x
print("caixas:", found)
assert len(found) == 3, found
assert found[0][0] < found[1][0] and abs(found[0][1] - found[1][1]) < 10
# Esquerda antes da direita.
assert found[2][1] > found[0][1]
# Linha de baixo por último.
x, y, w, h = found[0]
assert x <= 40 and y <= 40 and x + w >= 160 and y + h >= 60, found[0]
# Cobre a região (em 2x), com folga.
print("OK")
