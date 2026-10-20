"""Exemplos de treino gerados pela revisão do usuário (somente local).

Cada decisão do usuário vira um exemplo rotulado: recortes PNG do número +
os valores corretos. Nada sai da máquina; o conjunto serve para treinar, depois,
um leitor de dígitos próprio (veja tools/train_digit_reader.py).

Formato em disco (dentro de `root`):
    samples.jsonl          uma linha JSON por exemplo (última linha do mesmo
                           `id` vence, assim reprocessar não duplica)
    images/<id>_<k>.png    recortes (k = instante do evento)
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from ..domain.review import DecisionKind, HitEvent, ReviewDecision

SCHEMA_VERSION = 1
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_PNG_BYTES = 4 * 1024 * 1024
SAMPLES_FILE = "samples.jsonl"
IMAGES_DIR = "images"


def default_training_dir() -> Path:
    """Pasta de dados do usuário (nunca dentro do diretório do programa)."""
    override = os.environ.get("TETHYS_DATA_DIR")
    if override:
        return Path(override).expanduser() / "training"
    if sys.platform.startswith("win"):
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    elif sys.platform == "darwin":
        base = str(Path.home() / "Library" / "Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "Tethys" / "training"


def new_session_id() -> str:
    """Agrupa os exemplos de uma mesma revisão (sem guardar nome do vídeo)."""
    return uuid.uuid4().hex[:12]


def _sample_id(session: str, event: HitEvent) -> str:
    raw = f"{session}:{event.index}:{event.timestamp:.3f}".encode()
    return hashlib.sha1(raw).hexdigest()[:16]


def _valid_png(data: bytes) -> bool:
    return (
        isinstance(data, (bytes, bytearray))
        and data.startswith(PNG_SIGNATURE)
        and len(data) <= MAX_PNG_BYTES
    )


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


@dataclass(frozen=True)
class TrainingSample:
    id: str
    session: str
    engine_value: int
    engine: dict
    kind: str
    parts: tuple[tuple[int, int], ...]  # (valor, cópias); vazio = descartado
    images: tuple[str, ...]             # caminhos relativos a root
    offsets: tuple[float, ...]


class TrainingSampleStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else default_training_dir()

    # ------------------------------------------------------------------ escrita
    def save(
        self,
        session: str,
        event: HitEvent,
        decision: ReviewDecision,
        crops: Sequence[bytes],
        offsets: Sequence[float] = (0.0,),
    ) -> str | None:
        """Grava um exemplo. Devolve o id, ou None se não há imagem válida
        (sem recorte não há o que treinar)."""
        valid = [(k, png) for k, png in enumerate(crops) if _valid_png(png)]
        if not valid:
            return None

        sample_id = _sample_id(session, event)
        image_paths: list[str] = []
        used_offsets: list[float] = []
        for k, png in valid:
            relative = f"{IMAGES_DIR}/{sample_id}_{k}.png"
            _atomic_write(self.root / relative, bytes(png))
            image_paths.append(relative)
            used_offsets.append(float(offsets[k]) if k < len(offsets) else 0.0)

        record = {
            "schema_version": SCHEMA_VERSION,
            "id": sample_id,
            "session": session,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "engine_value": event.damage,
            "engine": {
                "confirmed": event.confirmed,
                "stacked": event.stacked,
                "verified": event.verified,
                "repeats": event.repeats,
                "observations": event.observations,
                "digit_pitch": round(event.digit_pitch, 4),
                "width": event.width,
                "height": event.height,
            },
            "kind": decision.kind.value,
            "parts": [[p.value, p.copies] for p in decision.parts],
            "images": image_paths,
            "offsets": used_offsets,
        }

        self.root.mkdir(parents=True, exist_ok=True)
        line = json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
        with open(self.root / SAMPLES_FILE, "a", encoding="utf-8") as handle:
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        return sample_id

    # ------------------------------------------------------------------ leitura
    def load(self) -> list[TrainingSample]:
        """Lê os exemplos, ignorando linhas corrompidas/inválidas."""
        path = self.root / SAMPLES_FILE
        if not path.exists():
            return []

        latest: dict[str, TrainingSample] = {}
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []

        for line in lines:
            sample = self._parse(line)
            if sample is not None:
                latest[sample.id] = sample
        return list(latest.values())

    def _parse(self, line: str) -> TrainingSample | None:
        try:
            data = json.loads(line)
            sample_id = str(data["id"])
            if not sample_id.isalnum():
                return None
            kind = DecisionKind(data["kind"]).value
            parts = tuple((int(v), int(c)) for v, c in data["parts"])
            images = tuple(str(p) for p in data["images"])
            for relative in images:
                # só aceita caminhos dentro de images/, sem ".."
                candidate = (self.root / relative).resolve()
                if (self.root / IMAGES_DIR).resolve() not in candidate.parents:
                    return None
            return TrainingSample(
                id=sample_id,
                session=str(data.get("session", "")),
                engine_value=int(data["engine_value"]),
                engine=dict(data.get("engine", {})),
                kind=kind,
                parts=parts,
                images=images,
                offsets=tuple(float(o) for o in data.get("offsets", [])),
            )
        except (KeyError, TypeError, ValueError):
            return None

    def count(self) -> int:
        return len(self.load())

    def labeled(self) -> Iterable[TrainingSample]:
        """Exemplos com rótulo útil (aceitos/corrigidos); descartes servem
        como 'não é dano' em outro treino."""
        return (s for s in self.load() if s.kind != DecisionKind.DISCARDED.value)
