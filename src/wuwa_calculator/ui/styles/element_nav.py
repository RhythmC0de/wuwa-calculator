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


def element_icon(element: str | None) -> str:
    return ELEMENT_ICONS.get(str(element), "◆")


def element_button_qss(element: str | None, extra_padding_right: int | None = None) -> str:
    background, border, text, hover = ELEMENT_NAV_COLORS.get(
        str(element), ELEMENT_NAV_COLORS["Spectro"]
    )
    padding_right = (
        f" padding-right: {extra_padding_right}px;"
        if extra_padding_right is not None
        else ""
    )
    return (
        f"QPushButton {{ background: {background}; color: {text}; "
        f"border: 1px solid {border}; border-radius: 7px; padding: 10px;"
        f"{padding_right} }}"
        f"QPushButton:hover {{ background: {hover}; border: 1px solid {border}; }}"
    )
