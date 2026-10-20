"""Serviço para imagens personalizadas de personagens (sem dependência de CWD)."""

from __future__ import annotations

import re
import shutil
from enum import Enum
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from wuwa_calculator.storage.paths import user_data_dir

MAX_IMAGE_FILE_BYTES = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_PACKAGE_DATA = Path(__file__).resolve().parent.parent / "data" / "characters"


class ImageType(Enum):
    ICON = "icons"
    SPRITE = "sprites"
    SPLASH = "splashes"


class ImageService:
    supported_extensions = frozenset({".png", ".jpg", ".jpeg", ".webp"})

    def __init__(self, custom_root: Path | None = None, default_root: Path | None = None) -> None:
        self.default_root = default_root or _PACKAGE_DATA
        self.custom_root = custom_root or (user_data_dir() / "custom_images")

    @staticmethod
    def _check_id(character_id: str) -> str:
        if not isinstance(character_id, str) or not _SAFE_ID.fullmatch(character_id):
            raise ValueError("Identificador de personagem inválido.")
        return character_id

    def validate_extension(self, source_path: Path) -> str:
        extension = Path(source_path).suffix.lower()
        if extension not in self.supported_extensions:
            raise ValueError(f"Extensão de imagem não suportada: {extension}")
        return extension

    def get_image(self, character_id: str, image_type: ImageType) -> Path:
        cid = self._check_id(character_id)
        for extension in sorted(self.supported_extensions):
            custom = self.custom_root / image_type.value / f"{cid}{extension}"
            if custom.is_file():
                return custom
        default = self.default_root / image_type.value / f"{cid}.png"
        if default.is_file():
            return default
        return self.default_root / image_type.value / "default.png"

    def _verify(self, source: Path) -> None:
        if not source.is_file():
            raise FileNotFoundError(f"Imagem de origem não encontrada: {source}")
        if source.stat().st_size > MAX_IMAGE_FILE_BYTES:
            raise ValueError("Imagem maior que o limite de 10 MB.")
        try:
            with Image.open(source) as image:
                width, height = image.size
                if width * height > MAX_IMAGE_PIXELS:
                    raise ValueError("Resolução da imagem acima do limite permitido.")
                image.verify()
        except (UnidentifiedImageError, OSError) as error:
            raise ValueError("O arquivo não é uma imagem válida.") from error

    def set_custom_image(self, character_id: str, image_type: ImageType, source_path: Path) -> Path:
        cid = self._check_id(character_id)
        source = Path(source_path)
        extension = self.validate_extension(source)
        self._verify(source)
        directory = self.custom_root / image_type.value
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / f"{cid}{extension}"
        for other in directory.glob(f"{cid}.*"):  # avoid stale files with another extension
            if other != destination:
                other.unlink(missing_ok=True)
        shutil.copyfile(source, destination)
        return destination
