"""Sidebar colors and icons keyed by resonator element."""

ELEMENT_NAV_COLORS = {
    "Aero": ("#145A4A", "#72E6C0", "#E8FFF8", "#1E8068"),
    "Glacio": ("#285A78", "#82D8FF", "#E4F8FF", "#397A9D"),
    "Electro": ("#49356F", "#B78CFF", "#F0E8FF", "#644B91"),
    "Fusion": ("#713D2C", "#FF8A65", "#FFF0E8", "#975039"),
    "Havoc": ("#642C43", "#E85D75", "#FFE8EE", "#873B58"),
    "Spectro": ("#665522", "#FFD76A", "#FFF8D6", "#87702D"),
}

ELEMENT_ICONS = {
    "Aero": "◈",
    "Glacio": "❄",
    "Electro": "✦",
    "Fusion": "♢",
    "Havoc": "◉",
    "Spectro": "✧",
}


def element_icon(element: str | None, fallback: str = "◆") -> str:
    """Return element icon."""
    return ELEMENT_ICONS.get(str(element), fallback)


def element_button_qss(
    element: str | None, extra_padding_right: int | None = None
) -> str:
    """Return element button qss."""
    background, border, text, hover = ELEMENT_NAV_COLORS.get(
        str(element), ELEMENT_NAV_COLORS["Spectro"]
    )
    padding_right = (
        f" padding-right: {extra_padding_right}px;"
        if extra_padding_right is not None
        else ""
    )
    return (
        f"QPushButton {{ background: {background}; color: {text}; border: 1px"
        f" solid {border}; border-radius: 7px; padding: 10px;{padding_right}"
        f" }}QPushButton:hover {{ background: {hover}; border: 1px solid"
        f" {border}; }}"
    )


# The main sidebar keeps its existing subdued palette.
WINDOW_NAV_COLORS = {
    "Aero": ("#163d4a", "#4cc9f0", "#d9f7ff", "#1f5668"),
    "Glacio": ("#163b52", "#72d2ff", "#e1f7ff", "#205d7d"),
    "Electro": ("#33204f", "#b084ff", "#f1e6ff", "#4d2d73"),
    "Fusion": ("#4b251d", "#ff8a65", "#fff0e8", "#713628"),
    "Havoc": ("#401d35", "#e56bba", "#ffe8f7", "#652d54"),
    "Spectro": ("#443b18", "#e8d66b", "#fffbe0", "#665a22"),
}
