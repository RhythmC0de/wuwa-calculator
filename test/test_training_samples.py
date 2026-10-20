import tempfile
from pathlib import Path

from wuwa_calculator.domain.review import HitEvent, accept, correct, discard
from wuwa_calculator.infrastructure.training_samples import (
    PNG_SIGNATURE, TrainingSampleStore,
)

PNG = PNG_SIGNATURE + b"fake"


def test_roundtrip_and_dedupe():
    with tempfile.TemporaryDirectory() as tmp:
        store = TrainingSampleStore(Path(tmp))
        e = HitEvent(index=3, timestamp=21.86, damage=782518, confirmed=False)
        sid = store.save("s1", e, correct(e, [(785, 1), (2518, 1)]), [PNG, PNG], (0.0, 0.1))
        assert sid
        store.save("s1", e, correct(e, [(785, 1), (2518, 1)]), [PNG], (0.0,))
        samples = store.load()
        assert len(samples) == 1
        assert samples[0].parts == ((785, 1), (2518, 1))
        assert (Path(tmp) / samples[0].images[0]).exists()


def test_rejects_non_png_and_bad_lines():
    with tempfile.TemporaryDirectory() as tmp:
        store = TrainingSampleStore(Path(tmp))
        e = HitEvent(index=1, timestamp=1.0, damage=500)
        assert store.save("s", e, accept(e), [b"not a png"]) is None
        assert store.save("s", e, discard(e), [PNG]) is not None
        (Path(tmp) / "samples.jsonl").open("a").write("{lixo\n{\"id\":\"x\",\"kind\":\"accepted\",\"parts\":[[1,1]],\"images\":[\"../../etc/passwd\"],\"engine_value\":1}\n")
        assert len(store.load()) == 1
        assert len(list(store.labeled())) == 0


def test_export_script(tmp_path=None):
    import subprocess, sys
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "src"
        store = TrainingSampleStore(src)
        e = HitEvent(index=1, timestamp=1.0, damage=782518, confirmed=False)
        store.save("sess", e, correct(e, [(785, 1), (2518, 1)]), [PNG, PNG], (0.0, 0.1))
        e2 = HitEvent(index=2, timestamp=2.0, damage=500)
        store.save("sess2", e2, discard(e2), [PNG], (0.0,))
        out = Path(tmp) / "out"
        root = Path(__file__).resolve().parents[1]
        done = subprocess.run(
            [sys.executable, str(root / "tools" / "export_training_dataset.py"),
             "--source", str(src), "--out", str(out)],
            capture_output=True, text=True,
        )
        assert done.returncode == 0, done.stderr
        rows = (out / "labels.csv").read_text().splitlines()
        assert len(rows) == 4 and "785+2518" in rows[1]
        assert len(list((out / "images").glob("*.png"))) == 3
