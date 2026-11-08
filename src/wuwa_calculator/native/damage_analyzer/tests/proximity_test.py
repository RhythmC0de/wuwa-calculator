#!/usr/bin/env python3
"""Testes sintéticos do fix22: proximidade no apagamento por contador e no
filtro de sufixo.

Uso: python tests/proximity_test.py <pasta-com-o-módulo> [--keep]
  A) contador mudando num canto + hit real no centro com valor dentro da
  faixa  -> 12000 deve ficar
  B) 24274 e 2424274 em lugares distantes (dois hits reais)
  -> os dois ficam
  C) 24274 e 2424274 colados (mistura)
  -> só 24274 fica"""

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np

W, H, FPS = 1920, 1080, 30


def text(f, s, x, y):
    """Draw outlined damage text in a synthetic video frame."""
    cv2.putText(f, s, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 0, 0), 12)
    cv2.putText(
        f, s, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (255, 255, 255), 5
    )


def make(name, frames_fn, n=75):
    """Write a synthetic video using the supplied frame renderer."""
    p = str(TMP / (name + ".avi"))
    vw = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*"MJPG"), FPS, (W, H))
    for i in range(n):
        f = np.full((H, W, 3), (60, 50, 45), np.uint8)
        frames_fn(f, i)
        vw.write(f)
    vw.release()
    return p


rnd = random.Random(1)
counter = [rnd.randint(9000, 15000) for _ in range(200)]


# A: contador mudando num ponto fixo + hit real no centro com valor
# dentro da faixa
def a(f, i):
    """Render an animated counter and a separate real damage hit."""
    text(f, str(counter[i // 2]), 1450, 560)  # contador (muda a cada 2 frames)
    if 15 <= i < 60:
        text(f, "12000", 800, 700 - (i - 15) * 3)  # hit real, centro, sobe


# B: sufixo em lugares distantes (ambos reais)
def b(f, i):
    """Render two spatially separated damage values sharing a suffix."""
    if 10 <= i < 50:
        text(f, "24274", 300, 600 - (i - 10) * 2)
    if 18 <= i < 55:
        text(f, "2424274", 1100, 700 - (i - 18) * 2)


# C: sufixo no mesmo lugar (mistura): o longo deve cair
def c(f, i):
    """Render overlapping values that simulate a merged OCR candidate."""
    if 10 <= i < 50:
        text(f, "24274", 800, 600 - (i - 10) * 2)
    if 18 <= i < 55:
        text(f, "2424274", 930, 670 - (i - 18) * 2)


TMP = Path(tempfile.mkdtemp())
vids = {
    k: make("syn22_" + k, fn) for k, fn in {"A": a, "B": b, "C": c}.items()
}
NATIVE_ANALYSIS_CODE = """
import sys; sys.path.insert(0,sys.argv[1])
import damage_analyzer as d, json
out={}
for k,p in json.loads(sys.argv[2]).items():
    c=d.AnalyzerConfig(); r=d.analyze_video(p,0,-1,c)
    out[k]=sorted((e.damage,e.confirmed) for e in r.events)
print(json.dumps(out))
"""
build = sys.argv[1]
r = subprocess.run(
    [
        sys.executable,
        "-c",
        NATIVE_ANALYSIS_CODE,
        build,
        json.dumps({k: str(v) for k, v in vids.items()}),
    ],
    capture_output=True,
    text=True,
    check=False,
)
if r.returncode:
    print(r.stderr[-800:])
    sys.exit(2)
got = {k: [v for v, _ in x] for k, x in json.loads(r.stdout).items()}
expect = {"A": [12000], "B": [24274, 2424274], "C": [24274]}
ok = True
for k in "ABC":
    good = sorted(got[k]) == sorted(expect[k])
    ok &= good
    print(
        k, "OK" if good else "FALHOU", "achado", got[k], "esperado", expect[k]
    )
print("RESULTADO:", "OK" if ok else "FALHOU")
sys.exit(0 if ok else 1)
