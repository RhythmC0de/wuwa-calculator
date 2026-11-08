"""Download failures and command-line execution of the icon generator."""

from http.client import HTTPException
from io import BytesIO
from unittest.mock import MagicMock, Mock

import pytest
from PIL import Image

from wuwa_calculator.services.image import image_processor as processor


def response_with(data):
    """Create a mocked HTTP response yielding the supplied bytes."""
    response = MagicMock()
    response.__enter__.return_value.read.return_value = data
    return response


def test_download_opens_valid_image(monkeypatch):
    """Verify download opens valid image."""
    buffer = BytesIO()
    Image.new("RGB", (4, 3), "red").save(buffer, format="PNG")
    monkeypatch.setattr(
        processor,
        "urlopen",
        Mock(return_value=response_with(buffer.getvalue())),
    )

    image = processor.fetch_image_from_url("https://example.com/icon.png")

    assert image is not None
    assert image.size == (4, 3)
    assert image.mode == "RGB"
    image.close()


@pytest.mark.parametrize("error_type", [OSError, HTTPException, ValueError])
def test_download_expected_failures_return_none(monkeypatch, error_type):
    """Verify download expected failures return none."""
    monkeypatch.setattr(
        processor, "urlopen", Mock(side_effect=error_type("unavailable"))
    )
    assert (
        processor.fetch_image_from_url("https://example.com/icon.png") is None
    )


def test_invalid_image_returns_none(monkeypatch):
    """Verify invalid image returns none."""
    monkeypatch.setattr(
        processor, "urlopen", Mock(return_value=response_with(b"not an image"))
    )
    assert (
        processor.fetch_image_from_url("https://example.com/icon.png") is None
    )


def test_oversized_image_is_rejected(monkeypatch):
    """Verify oversized image is rejected."""
    monkeypatch.setattr(
        processor, "urlopen", Mock(return_value=response_with(b"image"))
    )
    monkeypatch.setattr(
        processor.Image,
        "open",
        Mock(side_effect=Image.DecompressionBombError("too many pixels")),
    )
    assert (
        processor.fetch_image_from_url("https://example.com/icon.png") is None
    )


def test_unexpected_errors_are_not_hidden(monkeypatch):
    """Verify unexpected errors are not hidden."""
    monkeypatch.setattr(
        processor, "urlopen", Mock(side_effect=TypeError("unexpected"))
    )
    with pytest.raises(TypeError, match="unexpected"):
        processor.fetch_image_from_url("https://example.com/icon.png")


@pytest.mark.parametrize(("success", "exit_code"), [(True, 0), (False, 1)])
def test_cli_forwards_arguments_and_returns_exit_status(
    monkeypatch, tmp_path, success, exit_code
):
    """Verify cli forwards arguments and returns exit status."""
    output = str(tmp_path / "icon.png")
    url = "https://example.com/icon.png"
    process = Mock(return_value=success)
    monkeypatch.setattr(processor, "process_icon", process)
    monkeypatch.setattr(
        processor.sys, "argv", ["image_processor", url, output, "64"]
    )

    assert processor.main() == exit_code
    process.assert_called_once_with(url, output, 64)


def test_cli_without_url_prints_usage(monkeypatch, capsys):
    """Verify cli without url prints usage."""
    process = Mock()
    monkeypatch.setattr(processor, "process_icon", process)
    monkeypatch.setattr(processor.sys, "argv", ["image_processor"])

    assert processor.main() == 1
    assert "Uso:" in capsys.readouterr().out
    process.assert_not_called()
