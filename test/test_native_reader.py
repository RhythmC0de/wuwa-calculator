"""native_reader / service.extract_image_data com a leitura isolada simulada."""

import pytest

from wuwa_calculator.infrastructure import text_reading
from wuwa_calculator.services.ocr import native_reader, service


def _dict(text, x, y, w, h=22):
    return {"text": text, "confidence": 0.99, "x": x, "y": y, "width": w, "height": h}


def _panel():
    rows = [("HP", "15290"), ("ATK", "2387"), ("DEF", "1202"), ("Energy Regen", "139.2%"),
            ("Crit. Rate", "68.6%"), ("Crit. DMG", "260%"), ("Skill DMG", "7.9%"),
            ("Electro DMG Bonus", "82%")]
    lines = [_dict("Augusta", 200, 40, 150, 40)]
    for i, (label, value) in enumerate(rows):
        y = 170 + i * 54
        lines.append(_dict(label, 716 + len(label) * 6, y, len(label) * 12))
        lines.append(_dict(value, 1006 - len(value) * 6, y, len(value) * 12))
    return lines


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("TETHYS_STATS_OCR", raising=False)
    native_reader._warned.clear()


def test_le_totais_pelo_processo_isolado(monkeypatch, tmp_path):
    monkeypatch.setattr(text_reading, "read_lines_isolated", lambda *a, **k: _panel())
    stats, character = service.extract_image_data(tmp_path / "card.png")
    assert stats["hp"] == 15290.0 and stats["elemental_dmg"] == 82.0
    assert character == "augusta"


def test_engine_indisponivel_devolve_none(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise text_reading.EngineUnavailableError("sem modelo")
    monkeypatch.setattr(text_reading, "read_lines_isolated", boom)
    assert native_reader.read_lines(tmp_path / "card.png") is None


def test_falha_comum_devolve_none(monkeypatch, tmp_path):
    def boom(*args, **kwargs):
        raise RuntimeError("quebrou")
    monkeypatch.setattr(text_reading, "read_lines_isolated", boom)
    assert native_reader.read_lines(tmp_path / "card.png") is None


def test_variavel_desliga_a_engine(monkeypatch, tmp_path):
    monkeypatch.setattr(text_reading, "read_lines_isolated", lambda *a, **k: _panel())
    monkeypatch.setenv("TETHYS_STATS_OCR", "paddle")
    assert native_reader.read_lines(tmp_path / "card.png") is None


def test_imagem_sem_painel_devolve_vazio(monkeypatch, tmp_path):
    monkeypatch.setattr(
        text_reading, "read_lines_isolated", lambda *a, **k: [_dict("Augusta", 200, 40, 150, 40)]
    )
    stats, _ = service.extract_image_data(tmp_path / "card.png")
    assert stats == {}
