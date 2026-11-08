"""Read completed Qt network replies without changing their ownership."""

from PySide6.QtCore import QByteArray
from PySide6.QtNetwork import QNetworkReply


def read_reply_bytes(reply: object) -> QByteArray | bytes:
    """Return an open successful reply's data, or empty bytes on failure."""
    if (
        not getattr(reply, "isOpen", lambda: False)()
        or getattr(
            reply,
            "error",
            lambda: QNetworkReply.NetworkError.UnknownNetworkError,
        )()
        != QNetworkReply.NetworkError.NoError
    ):
        return b""
    return getattr(reply, "readAll", lambda: b"")()
