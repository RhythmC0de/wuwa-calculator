"""Cartões de status de sites diferentes, com as linhas e posições que o OCR
deve devolver (valores lidos de capturas reais, sem o jogador e o UID)."""

from wuwa_calculator.services.ocr.layout import TextLine, find_totals

CHAR = 12.0  # largura aproximada de um caractere em pixels


def box(text, left, y, height=22.0):
    """Build an OCR text fixture from its left coordinate."""
    width = len(text) * CHAR * height / 22.0
    return TextLine(text, 0.99, left + width / 2, y, width, height)


def right_box(text, right, y, height=22.0):
    """Build an OCR text fixture from its right coordinate."""
    width = len(text) * CHAR * height / 22.0
    return TextLine(text, 0.99, right - width / 2, y, width, height)


def two_columns(left_rows, right_rows, y0=174, step=54):
    """Two columns."""
    lines = []
    for i, (label, value) in enumerate(left_rows):
        lines += [
            box(label, 716, y0 + i * step),
            right_box(value, 1006, y0 + i * step),
        ]
    for i, (label, value) in enumerate(right_rows):
        lines += [
            box(label, 1077, y0 + i * step),
            right_box(value, 1409, y0 + i * step),
        ]
    return lines


def echo_noise():
    # linhas dos Echos embaixo do painel: mesmos rótulos, valores pequenos
    """Build Echo substat lines that must not be mistaken for totals."""
    rows = [
        ("Res. Skill", "7.9%"),
        ("Crit. Rate", "7.5%"),
        ("Crit. DMG", "15%"),
        ("ATK", "50"),
        ("Heavy Attack", "9.4%"),
    ]
    lines = []
    for _col, left in enumerate((570, 860, 1145)):
        for i, (label, value) in enumerate(rows):
            lines += [
                box(label, left, 744 + i * 39, 18),
                right_box(value, left + 220, 744 + i * 39, 18),
            ]
        lines += [
            box("Crit. DMG", left + 150, 667, 18),
            right_box("44%", left + 220, 700, 22),
        ]
    return lines


def test_wuwaflex_duas_colunas_augusta():
    """Verify wuwaflex duas colunas augusta."""
    lines = (
        two_columns(
            [
                ("HP", "15290"),
                ("ATK", "2387"),
                ("DEF", "1202"),
                ("Energy Regen", "139.2%"),
                ("Crit. Rate", "68.6%"),
                ("Crit. DMG", "260%"),
            ],
            [
                ("Skill DMG", "7.9%"),
                ("Basic Attack DMG", "0%"),
                ("Heavy Attack DMG", "48.1%"),
                ("Liberation DMG", "20.2%"),
                ("Electro DMG Bonus", "82%"),
                ("Healing Bonus", "0%"),
            ],
        )
        + echo_noise()
    )
    stats = find_totals(lines)
    assert stats == {
        "hp": 15290.0,
        "atk": 2387.0,
        "def": 1202.0,
        "energy_regen": 139.2,
        "crit_rate": 68.6,
        "crit_dmg": 260.0,
        "skill_dmg": 7.9,
        "basic_atk_dmg": 0.0,
        "heavy_atk_dmg": 48.1,
        "liberation_dmg": 20.2,
        "elemental_dmg": 82.0,
        "healing_bonus": 0.0,
    }


def test_wuwaflex_jinhsi_spectro():
    """Verify wuwaflex jinhsi spectro."""
    lines = two_columns(
        [
            ("HP", "18618"),
            ("ATK", "2129"),
            ("DEF", "1395"),
            ("Energy Regen", "119.2%"),
            ("Crit. Rate", "79.6%"),
            ("Crit. DMG", "278.6%"),
        ],
        [
            ("Skill DMG", "41.6%"),
            ("Basic Attack DMG", "9.4%"),
            ("Heavy Attack DMG", "0%"),
            ("Liberation DMG", "15%"),
            ("Spectro DMG Bonus", "72%"),
            ("Healing Bonus", "0%"),
        ],
    )
    stats = find_totals(lines)
    assert stats["elemental_dmg"] == 72.0 and stats["hp"] == 18618.0
    assert stats["skill_dmg"] == 41.6 and stats["basic_atk_dmg"] == 9.4


def test_coluna_unica_com_nomes_res_shorekeeper():
    """Verify coluna unica com nomes res shorekeeper."""
    rows = [
        ("HP", "41811"),
        ("ATK", "1188"),
        ("DEF", "1349"),
        ("Energy Regen", "243.9%"),
        ("Crit. Rate", "5%"),
        ("Crit. DMG", "208.8%"),
        ("Res. Skill DMG Bonus", "19.5%"),
        ("Basic Attack DMG Bonus", "24.4%"),
        ("Heavy Attack DMG Bonus", "20.3%"),
        ("Res. Liberation DMG Bonus", "14.2%"),
        ("Spectro DMG Bonus", "30%"),
        ("Healing Bonus", "0%"),
    ]
    lines = []
    for i, (label, value) in enumerate(rows):
        lines += [
            box(label, 311, 145 + i * 27, 14),
            right_box(value, 545, 145 + i * 27, 14),
        ]
    stats = find_totals(lines)
    assert stats["hp"] == 41811.0 and stats["crit_rate"] == 5.0
    assert stats["skill_dmg"] == 19.5 and stats["liberation_dmg"] == 14.2
    assert stats["elemental_dmg"] == 30.0


def test_total_com_bonus_embaixo_e_rotulo_quebrado_carlotta():
    """Verify total com bonus embaixo e rotulo quebrado carlotta."""
    lines = []
    rows = [  # (rótulo, total, y do rótulo, linha menor de base+bônus)
        ("HP", "17480", 44, "12450 + 5030.0"),
        ("ATK", "2275", 104, "962 + 1313.0"),
        ("DEF", "1611", 164, "1197 + 414.0"),
        ("Crit Rate", "75.5%", 224, "+70.5%"),
        ("Crit DMG", "304.2%", 284, "+154.2%"),
        ("Energy Regen", "108.4%", 344, "+8.4%"),
    ]
    for label, total, y, detail in rows:
        lines += [
            box(label, 1005, y, 24),
            right_box(total, 1345, y - 10, 24),  # total sobe um pouco
            right_box(detail, 1345, y + 15, 14),
        ]  # base + bônus, fonte menor
    more = [
        ("Glacio DMG Bonus", "42.0%", 404),
        ("Basic Attack DMG Bonus", "18.0%", 464),
        ("Heavy Attack DMG Bonus", "19.5%", 524),
        ("Resonance Skill DMG Bonus", "51.4%", 584),
    ]
    for label, value, y in more:
        lines += [box(label, 1005, y, 24), right_box(value, 1345, y, 24)]
    lines += [
        box("Resonance Liberation DMG", 1005, 632, 24),
        box("Bonus", 1005, 656, 24),
        right_box("16.5%", 1345, 645, 24),
    ]
    stats = find_totals(lines)
    assert (
        stats["hp"] == 17480.0
        and stats["atk"] == 2275.0
        and stats["def"] == 1611.0
    )
    assert stats["crit_rate"] == 75.5 and stats["crit_dmg"] == 304.2
    assert stats["energy_regen"] == 108.4 and stats["elemental_dmg"] == 42.0
    assert stats["liberation_dmg"] == 16.5 and stats["skill_dmg"] == 51.4


def test_cartao_oficial_so_com_echos_e_rejeitado():
    """Verify cartao oficial so com echos e rejeitado."""
    columns = [
        [
            ("Crit. DMG", "44%"),
            ("ATK", "150"),
            ("Resonance Skill DMG Bonus", "7.9%"),
            ("Crit. Rate", "7.5%"),
            ("Crit. DMG", "15%"),
            ("ATK", "50"),
            ("Heavy Attack DMG Bonus", "9.4%"),
        ],
        [
            ("Electro DMG Bonus", "30%"),
            ("ATK", "100"),
            ("DEF", "8.1%"),
            ("Energy Regen", "10.8%"),
            ("Crit. Rate", "10.5%"),
            ("HP", "430"),
            ("Crit. DMG", "21%"),
        ],
        [
            ("ATK", "18%"),
            ("HP", "2280"),
            ("Energy Regen", "10.8%"),
            ("Crit. DMG", "15%"),
            ("ATK", "7.1%"),
            ("Crit. Rate", "6.3%"),
            ("Heavy Attack DMG Bonus", "9.4%"),
        ],
    ]
    lines = []
    for c, rows in enumerate(columns):
        left = 70 + c * 378
        for i, (label, value) in enumerate(rows):
            lines += [
                box(label, left, 735 + i * 34, 20),
                right_box(value, left + 305, 735 + i * 34, 20),
            ]
    assert find_totals(lines) is None


def test_sem_linhas_devolve_none():
    """Verify sem linhas devolve none."""
    assert find_totals([]) is None
