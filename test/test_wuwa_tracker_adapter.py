"""Expected HTTP failures degrade gracefully; programming errors propagate."""

from http.client import HTTPException
from unittest.mock import Mock

import pytest

from wuwa_calculator.infrastructure import wuwa_tracker_adapter as adapter

CATALOG_HTML = (
    '{"character":{"name":"Augusta",'
    '"iconSrc":"/api/character-icons/augusta.png"},'
    '"firstStartDate":"2026-01-01 00:00:00"}'
)


@pytest.mark.parametrize("error_type", [OSError, HTTPException, ValueError])
def test_page_failures_return_empty_catalog(monkeypatch, error_type):
    """Verify page failures return empty catalog."""
    monkeypatch.setattr(
        adapter, "fetch_text", Mock(side_effect=error_type("unavailable"))
    )
    assert adapter.fetch_banner_catalog() == []


@pytest.mark.parametrize("error_type", [OSError, HTTPException, ValueError])
def test_image_failures_preserve_banner_metadata(monkeypatch, error_type):
    """Verify image failures preserve banner metadata."""
    monkeypatch.setattr(adapter, "fetch_text", Mock(return_value=CATALOG_HTML))
    monkeypatch.setattr(
        adapter, "fetch_image_bytes", Mock(side_effect=error_type("failed"))
    )

    banners = adapter.fetch_banner_catalog()

    assert len(banners) == 1
    assert banners[0]["name"] == "Augusta"
    assert banners[0]["image_bytes"] == b""


@pytest.mark.parametrize("error_type", [OSError, HTTPException, ValueError])
def test_fallback_failures_return_none(monkeypatch, error_type):
    """Verify fallback failures return none."""
    monkeypatch.setattr(
        adapter, "fetch_image_bytes", Mock(side_effect=error_type("failed"))
    )
    assert adapter.fetch_fallback_banner() is None


@pytest.mark.parametrize("error_type", [TypeError, RuntimeError])
@pytest.mark.parametrize(
    ("entry_point", "failed_fetch"),
    [
        (adapter.fetch_banner_catalog, "fetch_text"),
        (adapter.fetch_banner_catalog, "fetch_image_bytes"),
        (adapter.fetch_fallback_banner, "fetch_image_bytes"),
    ],
)
def test_programming_errors_propagate(
    monkeypatch, error_type, entry_point, failed_fetch
):
    """Verify programming errors propagate."""
    monkeypatch.setattr(adapter, "fetch_text", Mock(return_value=CATALOG_HTML))
    monkeypatch.setattr(
        adapter, failed_fetch, Mock(side_effect=error_type("unexpected"))
    )
    with pytest.raises(error_type, match="unexpected"):
        entry_point()


def test_successful_download_populates_banner_image(monkeypatch):
    """Verify successful download populates banner image."""
    monkeypatch.setattr(adapter, "fetch_text", Mock(return_value=CATALOG_HTML))
    monkeypatch.setattr(
        adapter, "fetch_image_bytes", Mock(return_value=b"png")
    )

    banners = adapter.fetch_banner_catalog()

    assert len(banners) == 1
    assert banners[0]["name"] == "Augusta"
    assert banners[0]["image_bytes"] == b"png"
