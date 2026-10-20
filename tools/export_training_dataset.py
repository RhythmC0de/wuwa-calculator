#!/usr/bin/env python3
"""Exporta os exemplos coletados na revisão para um conjunto de treino.

Uso:
    python tools/export_training_dataset.py [--source PASTA] --out dataset/

Gera:
    dataset/images/*.png       recortes (um por instante)
    dataset/labels.csv         image,split,kind,label,copies_total,engine_value
    dataset/summary.txt        contagens para saber se já há dados suficientes

`label` é o texto correto: valores separados por "+", cópias como "x3"
(ex.: "785+2518", "2071x3"). Descartes ("não é dano") saem com label vazio e
servem de exemplo negativo. O split treino/validação é feito por sessão
(todos os recortes de uma mesma análise ficam no mesmo lado), para a
validação não "ver" o mesmo hit que o treino.

Só usa a biblioteca padrão.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wuwa_calculator.infrastructure.training_samples import (  # noqa: E402
    TrainingSampleStore,
    default_training_dir,
)

VALIDATION_PERCENT = 15
MIN_RECOMMENDED = 300  # exemplos rotulados antes de valer a pena treinar


def split_of(session: str) -> str:
    bucket = int(hashlib.sha1(session.encode()).hexdigest(), 16) % 100
    return "val" if bucket < VALIDATION_PERCENT else "train"


def label_of(parts: tuple[tuple[int, int], ...]) -> str:
    return "+".join(f"{v}" + (f"x{c}" if c > 1 else "") for v, c in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, default=None,
                        help=f"pasta de exemplos (padrão: {default_training_dir()})")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    store = TrainingSampleStore(args.source)
    samples = store.load()
    if not samples:
        print(f"Nenhum exemplo em {store.root}.")
        return 1

    images_out = args.out / "images"
    images_out.mkdir(parents=True, exist_ok=True)

    kinds: Counter[str] = Counter()
    splits: Counter[str] = Counter()
    disagreements = 0

    with open(args.out / "labels.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["image", "split", "kind", "label", "copies_total", "engine_value"])
        for sample in samples:
            split = split_of(sample.session)
            label = label_of(sample.parts)
            copies = sum(c for _, c in sample.parts)
            for relative in sample.images:
                source = store.root / relative
                if not source.is_file():
                    continue
                shutil.copyfile(source, images_out / source.name)
                writer.writerow([f"images/{source.name}", split, sample.kind,
                                 label, copies, sample.engine_value])
                splits[split] += 1
            kinds[sample.kind] += 1
            if sample.kind == "corrected":
                disagreements += 1

    labeled = kinds["accepted"] + kinds["corrected"]
    lines = [
        f"Exemplos: {len(samples)}  (aceitos {kinds['accepted']}, "
        f"corrigidos {kinds['corrected']}, descartados {kinds['discarded']})",
        f"Imagens: treino {splits['train']}, validação {splits['val']}",
        f"A engine errou em {disagreements} de {labeled} exemplos rotulados.",
    ]
    if labeled < MIN_RECOMMENDED:
        lines.append(
            f"Ainda poucos dados: o recomendado é ter pelo menos {MIN_RECOMMENDED} "
            "exemplos rotulados (aceitos + corrigidos) antes de treinar."
        )
    summary = "\n".join(lines)
    (args.out / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
