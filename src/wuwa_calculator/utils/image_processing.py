"""utils/image_processing.py — preparação de imagens para OCR."""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter


def load_image(path: str | Path) -> Image.Image:
    """Abre a imagem e garante modo RGB."""
    img = Image.open(path)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    return img


def resize_keep_aspect(
        img: Image.Image,
        width: int = 1280) -> Image.Image:
    """Redimensiona mantendo a proporção."""
    w, h = img.size
    if w <= width:
        return img
    new_h = int(h * width / w)
    return img.resize((width, new_h), Image.Resampling.LANCZOS)


def to_grayscale(img: Image.Image) -> Image.Image:
    """Converte para escala de cinza."""
    return img.convert("L")


def enhance_for_ocr(
        img: Image.Image,
        contrast: float = 1.8) -> Image.Image:
    """Aumenta contraste e nitidez para facilitar o OCR."""
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = img.filter(ImageFilter.SHARPEN)
    return img


def prepare_for_ocr(
        path: str | Path,
        width: int = 1280) -> Image.Image:
    """
    Pipeline completo:
    1. Abre
    2. Redimensiona
    3. Escala de cinza
    4. Contraste + nitidez
    """
    img = load_image(path)
    img = resize_keep_aspect(img, width)
    img = to_grayscale(img)
    img = enhance_for_ocr(img)
    return img


def crop_region(
    img: Image.Image,
    box: tuple[int, int, int, int],
) -> Image.Image:
    """Corta uma região (left, top, right, bottom)."""
    return img.crop(box)
