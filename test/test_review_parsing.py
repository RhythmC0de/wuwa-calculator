import pytest

from wuwa_calculator.domain.review import HitPart, ParseError, format_parts, parse_parts


def test_basic_forms():
    assert parse_parts("785 + 2518") == (HitPart(785), HitPart(2518))
    assert parse_parts("2071 x3") == (HitPart(2071, 3),)
    assert parse_parts("2071×3") == (HitPart(2071, 3),)
    assert parse_parts("17.040 ; 1,151") == (HitPart(17040), HitPart(1151))
    assert parse_parts("430 + 1574 x2") == (HitPart(430), HitPart(1574, 2))
    assert parse_parts("430 1574") == (HitPart(430), HitPart(1574))


def test_errors():
    for bad in ["", "   ", "abc", "12 + abc", "0", "5 x0", "5 x99", "999999999"]:
        with pytest.raises(ParseError):
            parse_parts(bad)


def test_roundtrip():
    parts = (HitPart(785), HitPart(2518, 3))
    assert parse_parts(format_parts(parts)) == parts
