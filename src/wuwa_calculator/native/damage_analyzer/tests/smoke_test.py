#!/usr/bin/env python3
"""Teste de fumaça do damage_analyzer (Windows e Linux).

Gera um vídeo sintético (cenário escuro + HUD + números de dano laranja
subindo + contagem regressiva fora das zonas de HUD), roda o módulo e
confere se os números de dano esperados foram encontrados e se o HUD e o
contador foram ignorados.

Uso:
    python tests/smoke_test.py <pasta-com-o-módulo> [--keep]

Requisitos: numpy, opencv-python, pillow.
"""
import argparse
import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1280, 720, 30
DURATION = 8.0

# (instante em segundos, valor, x, y inicial)
DAMAGE = [
    (1.0, 489982, 560, 420),
    (2.0, 12345, 640, 400),
    (2.5, 7531, 600, 470),
    (3.4, 250000, 520, 380),
    (4.5, 999, 700, 430),
    (5.0, 48100, 650, 450),
    (5.1, 31337, 450, 330),   # coexiste com o anterior
    (6.5, 1500000, 480, 410),
]
LIFETIME = 0.8
RISE_PX_PER_SEC = 60


def find_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "DejaVuSans-Bold.ttf",
        "arialbd.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    raise SystemExit("Nenhuma fonte TrueType encontrada para o teste.")


def background() -> np.ndarray:
    rng = np.random.default_rng(7)
    y = np.linspace(25, 70, H, dtype=np.float32)[:, None, None]
    frame = np.repeat(np.repeat(y, W, axis=1), 3, axis=2)
    frame += rng.normal(0, 3, size=(H, W, 3))
    frame[..., 0] += 10  # leve tom azulado (BGR)
    return np.clip(frame, 0, 255).astype(np.uint8)


def draw_text(draw, xy, text, font, fill, outline, width):
    draw.text(xy, text, font=font, fill=fill,
              stroke_width=width, stroke_fill=outline)


def render(t: float, base: np.ndarray, fonts) -> np.ndarray:
    img = Image.fromarray(cv2.cvtColor(base, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(img)

    # --- HUD (deve ser ignorado pelas zonas) -----------------------------
    draw_text(draw, (30, 40), "128456", fonts["hud"], (255, 255, 255),
              (0, 0, 0), 2)                       # canto superior esquerdo
    draw_text(draw, (1080, 300), "845320", fonts["hud"], (255, 240, 200),
              (0, 0, 0), 2)                       # painel da equipe
    draw_text(draw, (1000, 640), "990011", fonts["hud"], (255, 255, 255),
              (0, 0, 0), 2)                       # habilidades

    # --- Contagem regressiva fora das zonas (filtro temporal) -------------
    countdown = 125 - int(t)  # 125,124,123... uma vez por segundo
    if 0.5 <= t <= 7.0:
        draw_text(draw, (300, 250), str(countdown), fonts["hud"],
                  (255, 255, 255), (0, 0, 0), 2)

    # --- Números de dano ---------------------------------------------------
    for start, value, x, y in DAMAGE:
        age = t - start
        if 0.0 <= age <= LIFETIME:
            yy = y - RISE_PX_PER_SEC * age
            draw_text(draw, (x, yy), str(value), fonts["damage"],
                      (255, 150, 40), (120, 40, 0), 3)

    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def make_video(path: Path) -> None:
    fonts = {"damage": find_font(38), "hud": find_font(30)}
    base = background()
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"MJPG"), FPS, (W, H))
    if not writer.isOpened():
        raise SystemExit("Não foi possível criar o vídeo de teste.")
    for i in range(int(DURATION * FPS)):
        writer.write(render(i / FPS, base, fonts))
    writer.release()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("module_dir", help="pasta que contém damage_analyzer*.so/.pyd")
    parser.add_argument("--keep", action="store_true", help="mantém o vídeo gerado")
    args = parser.parse_args()

    module_dir = Path(args.module_dir).resolve()
    if os.name == "nt":
        os.add_dll_directory(str(module_dir))
    sys.path.insert(0, str(module_dir))

    import damage_analyzer as da  # noqa: E402

    print("módulo:", da.__file__)
    print("modelos:", da.find_models_directory())

    with tempfile.TemporaryDirectory() as tmp:
        video = Path(tmp) / "sintético ção.avi"   # acentos de propósito
        make_video(video)
        if args.keep:
            Path("synthetic_test.avi").write_bytes(video.read_bytes())

        config = da.AnalyzerConfig()
        config.verbose = True
        result = da.analyze_video(str(video), 0.0, -1.0, config)

    expected = sorted(v for _, v, _, _ in DAMAGE)
    found = sorted(e.damage for e in result.events)

    print("\nEventos encontrados:")
    for e in result.events:
        print(f"  t={e.timestamp:5.2f}s  dano={e.damage:>8}  ({e.center_x},{e.center_y})")
    print("\nesperado:", expected)
    print("achado:  ", found)

    missing = [v for v in expected if v not in found]
    extra = [v for v in found if v not in expected]
    print("faltando:", missing)
    print("a mais:  ", extra)

    ok = not missing and not extra and result.total_hits == len(expected)
    print("\nRESULTADO:", "OK" if ok else "FALHOU")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
