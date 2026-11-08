# The stylesheet is one contiguous theme template.
"""Global visual system for the PySide6 application."""

# * EDITAVEL: altere cores globais e regras QSS aqui; o wallpaper gera
# uma paleta complementar.
# ! Nao use #RRGGBBAA no QColor: _with_alpha produz o formato Qt #AARRGGBB.

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

BG = "#080B18"
CARD = "#0F1428"
BORDER = "#394071"
HEADER = "#161D39"
TEXT = "#F2F0FF"
MUTED = "#A8A8D5"
ACCENT = "#A855F7"
GOLD = "#FFD76A"
CURRENT_GLOW_COLOR = ACCENT
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_WALLPAPER = (
    "url("
    f"{(PROJECT_ROOT / 'Assets' / 'app_background_reference.png').as_posix()}"
    ")"
)


def _with_alpha(color: str, opacity: int) -> str:
    alpha = max(0, min(255, opacity))
    return f"#{alpha:02X}{color.lstrip('#')}"


def apply_glow(
    widget: QWidget, blur: float = 24.0, opacity: int = 180
) -> None:
    """Apply a themed drop-shadow glow to a widget."""
    widget.setProperty("_glow_mode", "global")
    widget.setProperty("_glow_blur", blur)
    widget.setProperty("_glow_opacity", opacity)
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    effect.setColor(QColor(_with_alpha(CURRENT_GLOW_COLOR, opacity)))
    widget.setGraphicsEffect(effect)


ELEMENT_GLOW_COLORS = {
    "Aero": "#72E6C0",
    "Glacio": "#82D8FF",
    "Electro": "#B78CFF",
    "Fusion": "#FF8A65",
    "Havoc": "#E85D75",
    "Spectro": "#FFD76A",
}


def apply_element_glow(
    widget: QWidget, element: str, blur: float = 24.0, opacity: int = 180
) -> None:
    """Apply the selected elemental glow to a widget."""
    widget.setProperty("_glow_mode", "element")
    widget.setProperty("_glow_element", element)
    widget.setProperty("_glow_blur", blur)
    widget.setProperty("_glow_opacity", opacity)
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0, 0)
    color = ELEMENT_GLOW_COLORS.get(element, ACCENT)
    effect.setColor(QColor(_with_alpha(color, opacity)))
    widget.setGraphicsEffect(effect)


def refresh_glows(root: QWidget) -> None:
    """Refresh registered glows after the appearance changes."""
    for widget in [root, *root.findChildren(QWidget)]:
        mode = widget.property("_glow_mode")
        if mode == "global":
            apply_glow(
                widget,
                float(widget.property("_glow_blur")),
                int(widget.property("_glow_opacity")),
            )
        elif mode == "element":
            apply_element_glow(
                widget,
                str(widget.property("_glow_element")),
                float(widget.property("_glow_blur")),
                int(widget.property("_glow_opacity")),
            )


def _wallpaper_palette(wallpaper: str) -> tuple[str, str, str, str, str]:
    # Keep ordered widget construction and painting steps together.
    # pylint: disable=too-many-locals
    source = (
        QUrl(wallpaper).toLocalFile()
        if wallpaper.startswith("file:")
        else wallpaper
    )
    image = QImage(
        source or str(PROJECT_ROOT / "Assets" / "app_background_reference.png")
    )
    if image.isNull():
        return CARD, HEADER, BORDER, ACCENT, MUTED

    sample = image.scaled(32, 18).convertToFormat(QImage.Format.Format_RGB32)
    red = green = blue = 0
    for y in range(sample.height()):
        for x in range(sample.width()):
            color = sample.pixelColor(x, y)
            red += color.red()
            green += color.green()
            blue += color.blue()
    count = max(1, sample.width() * sample.height())
    average = QColor(red // count, green // count, blue // count)
    surface = QColor(
        max(20, average.red() // 3),
        max(20, average.green() // 3),
        max(24, average.blue() // 3),
    )
    panel = QColor(
        max(28, average.red() // 4 + 10),
        max(28, average.green() // 4 + 10),
        max(32, average.blue() // 4 + 12),
    )
    border = QColor(
        min(255, average.red() + 55),
        min(255, average.green() + 55),
        min(255, average.blue() + 55),
    )
    accent = QColor(
        min(255, average.red() + 105),
        min(255, average.green() + 105),
        min(255, average.blue() + 105),
    )
    muted = QColor(
        min(235, max(150, average.red() + 95)),
        min(235, max(150, average.green() + 95)),
        min(235, max(150, average.blue() + 95)),
    )
    return (
        surface.name(),
        panel.name(),
        border.name(),
        accent.name(),
        muted.name(),
    )


def wallpaper_palette(wallpaper: str = "") -> tuple[str, str, str, str, str]:
    """Return the colors derived from the active wallpaper."""
    return _wallpaper_palette(wallpaper)


def _accent_preset(name: str) -> str:
    return {
        "Ciano Tethys": "#6FEAFF",
        "Dourado Sol": "#FFD76A",
        "Roxo Nécro": "#B78CFF",
        "Vermelho Alerta": "#FF6B6B",
    }.get(name, "#6FEAFF")


def accent_preset(name: str) -> str:
    """Return the configured interface accent color."""
    return _accent_preset(name)


def application_qss(
    show_background: bool = True,
    wallpaper: str = "",
    interface_opacity: int = 85,
    accent_theme: str = "Ciano Tethys",
) -> str:
    """Build the application stylesheet from the selected appearance."""
    # Preserve the exported color used by existing glow effects.
    # pylint: disable-next=global-statement
    global CURRENT_GLOW_COLOR
    background_rule = f"background-color: {BG};"
    (
        wallpaper_surface,
        wallpaper_panel,
        wallpaper_border,
        wallpaper_accent,
        wallpaper_muted,
    ) = (
        _wallpaper_palette(wallpaper)
        if show_background
        else (BG, CARD, BORDER, ACCENT, MUTED)
    )
    selected_accent = _accent_preset(accent_theme)
    CURRENT_GLOW_COLOR = selected_accent
    # Acrylic stays translucent while the setting changes its material
    # intensity.
    panel_alpha = max(150, min(225, round(112 + interface_opacity * 1.13)))
    return (
        f"\n    QMainWindow {{\n        {background_rule}\n        color:"
        f" {TEXT};\n    }}\n    QWidget {{ background: transparent; color:"
        f' {TEXT}; font-family: "Bahnschrift", "Segoe UI"; font-size: 13px;'
        " }\n    QLabel { background: transparent; }\n    QWidget#appShell"
        " { background: transparent; }\n    QFrame#sidebar { background:"
        f" rgba(12, 16, 32, {panel_alpha}); border-right: 1px solid #202744;"
        " }\n    QTabWidget#mainTabs { background: transparent; border: 0;"
        " }\n    QTabWidget#mainTabs::pane { border: 0; background:"
        " transparent; }\n    QPushButton#nav, QPushButton#navActive {"
        " text-align: left; border: 0; padding: 10px; border-radius: 7px;"
        " }\n    QPushButton#nav { background: #161D39; color: #EDEAFF;"
        " }\n    QPushButton#nav:hover { background: #24265A; border: 1px"
        " solid #A855F7; }\n    QPushButton#navActive { background:"
        " #48209A; color: #FFFFFF; font-weight: 800; }\n   "
        ' QPushButton#nav[element="Aero"],'
        ' QPushButton#navActive[element="Aero"] { background: #145A4A;'
        " border: 1px solid #72E6C0; color: #E8FFF8; }\n   "
        ' QPushButton#nav[element="Glacio"],'
        ' QPushButton#navActive[element="Glacio"] { background: #285A78;'
        " border: 1px solid #82D8FF; color: #E4F8FF; }\n   "
        ' QPushButton#nav[element="Electro"],'
        ' QPushButton#navActive[element="Electro"] { background: #49356F;'
        " border: 1px solid #B78CFF; color: #F0E8FF; }\n   "
        ' QPushButton#nav[element="Fusion"],'
        ' QPushButton#navActive[element="Fusion"] { background: #713D2C;'
        " border: 1px solid #FF8A65; color: #FFF0E8; }\n   "
        ' QPushButton#nav[element="Havoc"],'
        ' QPushButton#navActive[element="Havoc"] { background: #642C43;'
        " border: 1px solid #E85D75; color: #FFE8EE; }\n   "
        ' QPushButton#nav[element="Spectro"],'
        ' QPushButton#navActive[element="Spectro"] { background: #665522;'
        " border: 1px solid #FFD76A; color: #FFF8D6; }\n   "
        ' QPushButton#nav[element="Aero"]:hover,'
        ' QPushButton#navActive[element="Aero"]:hover { background: #1E8068;'
        ' }\n    QPushButton#nav[element="Glacio"]:hover,'
        ' QPushButton#navActive[element="Glacio"]:hover { background:'
        ' #397A9D; }\n    QPushButton#nav[element="Electro"]:hover,'
        ' QPushButton#navActive[element="Electro"]:hover { background:'
        ' #644B91; }\n    QPushButton#nav[element="Fusion"]:hover,'
        ' QPushButton#navActive[element="Fusion"]:hover { background:'
        ' #975039; }\n    QPushButton#nav[element="Havoc"]:hover,'
        ' QPushButton#navActive[element="Havoc"]:hover { background:'
        ' #873B58; }\n    QPushButton#nav[element="Spectro"]:hover,'
        ' QPushButton#navActive[element="Spectro"]:hover { background:'
        " #87702D; }\n    QFrame#card {\n        background: rgba(15, 20,"
        f" 40, {panel_alpha});\n        border: 1px solid rgba(168, 85, 247,"
        " 155);\n        border-radius: 12px;\n    }\n    QFrame#appHeader"
        f" {{ background: rgba(13, 17, 34, {panel_alpha}); border: 1px solid"
        " rgba(57, 64, 113, 180); border-radius: 10px; }\n    QScrollArea,"
        " QScrollArea > QWidget, QScrollArea > QWidget > QWidget {"
        " background: transparent; border: 0; }\n    QFrame#videoSurface {"
        " background: rgba(11, 13, 18, 235); border: 1px solid rgba(0, 217,"
        " 255, 70); border-radius: 8px; }\n    QFrame#mediaToolbar {"
        " background: rgba(8, 14, 27, 235); border: 1px solid rgba(0, 217,"
        " 255, 90); border-radius: 7px; }\n    QFrame#mediaSupportPanel {"
        " background: rgba(7, 15, 28, 185); border: 1px solid rgba(0, 217,"
        " 255, 70); border-radius: 8px; }\n    QFrame#mediaSupportPanel"
        " QFrame#card { background: transparent; border: 0; border-radius:"
        " 0; }\n    QLabel#videoHud { color: #8FF6FF; background: rgba(5,"
        " 12, 22, 205); border: 1px solid rgba(0, 217, 255, 100);"
        " border-radius: 5px; padding: 4px 9px; font-size: 10px; font-weight:"
        " 800; }\n    QPushButton#mediaControlButton,"
        " QPushButton#mediaBrowseButton, QPushButton#mediaPlayButton,"
        " QPushButton#mediaStopButton { background: rgba(20, 35, 55, 230);"
        " color: #DDFBFF; border: 1px solid rgba(0, 217, 255, 85);"
        " border-radius: 5px; min-height: 26px; font-weight: 800; }\n   "
        " QPushButton#mediaControlButton:hover,"
        " QPushButton#mediaBrowseButton:hover,"
        " QPushButton#mediaPlayButton:hover,"
        " QPushButton#mediaStopButton:hover { background: rgba(0, 110, 145,"
        " 220); border-color: #6FEAFF; }\n    QLabel#mediaTimeLabel,"
        " QLabel#mediaControlLabel { color: #B7DCE5; font-size: 10px;"
        " font-weight: 700; }\n    QSlider#playerProgress { min-height:"
        " 14px; }\n    QFrame#frequencyProtocolBar { background: rgba(11,"
        " 13, 18, 220); border: 1px solid rgba(0, 217, 255, 70);"
        " border-radius: 7px; }\n    QLabel#frequencyProtocolTitle { color:"
        " #6FEAFF; font-size: 12px; font-weight: 800; letter-spacing: 1px;"
        " }\n    QLabel#frequencyProtocolSubtitle { color: #8A99AD;"
        " font-size: 9px; margin-top: 4px; }\n   "
        " QLabel#frequencyProtocolBadge { color: #00D9FF; font-family:"
        ' "Bahnschrift", "Segoe UI", sans-serif; font-size: 11px; border: 1px'
        " solid rgba(0, 217, 255, 76); border-radius: 5px; padding: 4px 10px;"
        " min-height: 28px; white-space: nowrap; }\n   "
        " QLabel#mediaSectionTitle { color: #F2F0FF; font-size: 13px;"
        " font-weight: 800; }\n    QLabel#mediaPanelDuration { color:"
        " #67D9FF; font-size: 12px; font-weight: 800; }\n    QFrame#eventRow"
        " { background: rgba(11, 13, 18, 190); border: 1px solid rgba(0,"
        " 217, 255, 50); border-radius: 7px; }\n   "
        ' QFrame#eventRow[category="Skill"] { border-left: 3px solid'
        ' #6FEAFF; }\n    QFrame#eventRow[category="Ultimate"] {'
        " border-left: 3px solid #C084FC; }\n   "
        ' QFrame#eventRow[category="Buff"] { border-left: 3px solid #FFD76A;'
        ' }\n    QFrame#eventRow[stripe="even"] { background: rgba(20, 29,'
        ' 45, 205); }\n    QFrame#eventRow[active="true"] { background:'
        " rgba(72, 32, 154, 215); border-color: #B77CFF; }\n   "
        " QLabel#eventTimestamp { color: #C7C8EA; font-size: 11px;"
        " font-weight: 800; }\n    QLabel#eventIcon { color: #B77CFF;"
        " background: rgba(35, 38, 65, 210); border: 1px solid #6547A8;"
        " border-radius: 12px; font-size: 13px; }\n    QLabel#eventTitle {"
        " color: #F2F0FF; font-size: 11px; font-weight: 800; }\n   "
        " QLabel#eventDescription { color: #A8A8D5; font-size: 9px; }\n   "
        " QLabel#eventCategory { color: #6FEAFF; font-size: 8px;"
        ' font-weight: 900; }\n    QFrame#eventRow[category="Ultimate"]'
        " QLabel#eventCategory { color: #C084FC; }\n   "
        ' QFrame#eventRow[category="Buff"] QLabel#eventCategory { color:'
        ' #FFD76A; }\n    QFrame#eventRow[active="true"] QLabel#eventTitle,'
        ' QFrame#eventRow[active="true"] QLabel#eventDescription,'
        ' QFrame#eventRow[active="true"] QLabel#eventTimestamp { color:'
        " #FFFFFF; }\n    QLabel#metricName, QLabel#optionLabel { color:"
        f" {MUTED}; font-size: 9px; text-transform: uppercase; }}\n   "
        " QLabel#metricValue { color: #F2F0FF; font-size: 13px; font-weight:"
        " 900; }\n    QComboBox#mediaOptionCombo { min-width: 104px;"
        " padding: 6px 8px; font-size: 11px; background: rgba(11, 16, 34,"
        " 210); border-color: rgba(103, 112, 168, 180); }\n   "
        " QLabel#dpsMetric { color: #8FF6FF; background: rgba(10, 28, 43,"
        " 225); border: 1px solid rgba(0, 217, 255, 105); border-radius: 6px;"
        " padding: 7px 9px; font-size: 10px; font-weight: 900; }\n   "
        " QPushButton#dpsAnalyzeButton { color: #06141C; background:"
        " #6FEAFF; border: 1px solid #B8F8FF; border-radius: 6px; padding:"
        " 7px 12px; font-weight: 900; }\n   "
        " QPushButton#dpsAnalyzeButton:hover { background: #B8F8FF;"
        " border-color: #FFFFFF; }\n    QPushButton#mediaQuickAction {"
        f" background: rgba(11, 13, 18, 225); color: {TEXT}; border: 1px solid"
        " rgba(212, 175, 55, 150); border-radius: 6px; padding: 8px 7px;"
        " font-size: 11px; font-weight: 700; }\n   "
        " QPushButton#mediaQuickAction:hover { background: rgba(31, 35, 42,"
        " 235); border-color: #D4AF37; }\n    QFrame#currentBannerCard {"
        " background: transparent; border: 0; border-radius: 0; }\n   "
        " QFrame#bannerTimeline {\n        background: rgba(20, 19, 31,"
        " 188);\n        border: 1px solid rgba(150, 180, 205, 95);\n       "
        " border-radius: 10px;\n    }\n    QLabel#bannerTimelineTitle {"
        " color: #F7D878; font-size: 18px; font-weight: 800; }\n   "
        " QLabel#bannerCurrentHighlight {\n        color: #FFFFFF;\n       "
        " background: rgba(12, 16, 30, 225);\n        border: 1px solid"
        " rgba(212, 175, 55, 165);\n        border-radius: 6px;\n       "
        ' padding: 6px 12px;\n        font-family: "Bahnschrift", "Segoe'
        ' UI";\n        font-size: 18px;\n        font-weight: 800;\n    }\n'
        "    QLabel#bannerTimelineSection { color: #D6D5E8; font-size: 11px;"
        " font-weight: 800; text-transform: uppercase; }\n   "
        " QFrame#bannerTimelinePast {\n        background: rgba(12, 12, 22,"
        " 150);\n        border-right: 1px solid rgba(133, 143, 180, 100);\n "
        "       border-radius: 6px;\n        min-width: 332px;\n    }\n   "
        " QFrame#bannerTimelineFuture { background: transparent; border: 0;"
        " }\n    QScrollArea#bannerTimelineScroll { background:"
        " transparent; border: 0; }\n    QFrame#bannerTimelineCard {\n     "
        "   background: rgba(31, 30, 48, 225);\n        border: 1px solid"
        " rgba(133, 143, 180, 125);\n        border-radius: 7px;\n    }\n   "
        " QFrame#bannerTimelineCard:hover {\n        border: 1px solid"
        " rgba(103, 232, 212, 190);\n        background: rgba(40, 39, 62,"
        " 235);\n    }\n    QFrame#bannerTimelinePastCard {\n       "
        " background: rgba(31, 30, 48, 190);\n        border: 1px solid"
        " rgba(133, 143, 180, 105);\n        border-radius: 6px;\n    }\n   "
        " QFrame#bannerTimelinePastCard:hover {\n        border: 1px solid"
        " rgba(103, 232, 212, 170);\n    }\n    QLabel#bannerTimelineThumb"
        " {\n        background: #0D0D15;\n        color: #67E8D4;\n       "
        " border: 1px solid rgba(212, 175, 55, 100);\n        border-radius:"
        " 5px;\n    }\n    QLabel#bannerTimelineName { color: #F3F1FF;"
        " font-size: 12px; font-weight: 800; }\n    QLabel#bannerTimelineTBA"
        " {\n        color: #8FF6FF;\n        background: rgba(25, 34, 62,"
        " 215);\n        border: 1px solid rgba(180, 119, 255, 190);\n       "
        " border-radius: 5px;\n        padding: 5px 8px;\n       "
        ' font-family: "Bahnschrift", "Segoe UI";\n        font-size: 14px;\n'
        "        font-weight: 900;\n    }\n    QLabel#bannerTimelineRarity"
        " { color: #FFD76A; font-size: 12px; font-weight: 800; }\n   "
        " QLabel#bannerTimelineDate {\n        color: #7DEBFF;\n       "
        ' font-family: "Bahnschrift", "Segoe UI";\n        font-size: 11px;\n'
        "        font-weight: 800;\n        background: rgba(22, 42, 62,"
        " 205);\n        border: 1px solid rgba(103, 232, 212, 145);\n       "
        " border-radius: 4px;\n        padding: 3px 6px;\n       "
        " text-shadow: 0 0 8px #35D9FF;\n    }\n    QLabel#bannerTimelineTag"
        " { color: #67E8D4; font-size: 9px; font-weight: 800; }\n   "
        " QLabel#bannerTimelineEmpty { color: #A8A8D5; padding: 14px; }\n  "
        "  QPushButton#bannerTimelineArrow {\n        background: rgba(52,"
        " 49, 76, 220);\n        color: #F7D878;\n        border: 1px solid"
        " rgba(103, 232, 212, 120);\n        border-radius: 5px;\n       "
        " font-size: 16px;\n        font-weight: 800;\n        padding: 0;\n "
        "   }\n    QPushButton#bannerTimelineArrow:hover { background:"
        " #3F5270; color: #FFFFFF; }\n    QFrame#upcomingBannersSection {\n"
        "        background: rgba(12, 11, 16, 218);\n        border: 1px"
        " solid rgba(255, 255, 255, 28);\n        border-radius: 12px;\n   "
        " }\n    QLabel#upcomingBannersTitle { color: #F5F5F5; font-size:"
        " 15px; font-weight: 900; }\n    QLabel#upcomingBannersSubtitle {"
        " color: #9DA3B4; font-size: 9px; }\n   "
        " QPushButton#upcomingBannersTrackerButton {\n        background:"
        " rgba(20, 35, 65, 220);\n        color: #8FEFFF;\n        border:"
        " 1px solid rgba(0, 217, 255, 120);\n        border-radius: 7px;\n   "
        "     padding: 8px 12px;\n        font-size: 11px;\n       "
        " font-weight: 700;\n    }\n   "
        " QPushButton#upcomingBannersTrackerButton:hover { background:"
        " #173B5B; border: 1px solid #00D9FF; }\n   "
        " QFrame#upcomingBannerCard {\n        background: rgba(12, 16, 30,"
        " 235);\n        border: 1px solid rgba(0, 217, 255, 150);\n       "
        " border-radius: 16px;\n    }\n    QFrame#upcomingBannerCard:hover"
        " { border: 1px solid #6FEAFF; background: rgba(25, 27, 45, 248);"
        " }\n    QFrame#upcomingBannerPastCard {\n        background:"
        " rgba(12, 16, 30, 235);\n        border: 1px solid rgba(0, 217, 255,"
        " 150);\n        border-radius: 16px;\n    }\n   "
        ' QFrame#upcomingBannerPastCard[hovered="true"] {\n        border:'
        " 0;\n        background: rgba(25, 27, 45, 248);\n    }\n   "
        " QLabel#upcomingBannerImage {\n        background: transparent;\n  "
        "      color: #9DA3B4;\n        border: 0;\n        border-radius:"
        " 16px;\n    }\n    QFrame#upcomingBannerOverlay {\n       "
        " background: rgba(0, 0, 0, 155);\n        border: 1px solid rgba(0,"
        " 217, 255, 95);\n        border-radius: 6px;\n    }\n   "
        " QLabel#upcomingBannerBadge {\n        color: #0C0B10;\n       "
        " background: #00D9FF;\n        border-radius: 5px;\n        padding:"
        " 3px 7px;\n        font-size: 9px;\n        font-weight: 900;\n   "
        " }\n    QLabel#upcomingBannerName { color: #F5F5F5; font-size:"
        " 13px; font-weight: 900; }\n    QLabel#upcomingBannerDetails {"
        " color: #D5D9E4; font-size: 10px; font-weight: 700; }\n   "
        " QFrame#bannerImageContainer { background: #14131F; border: 2px"
        " solid rgba(212, 175, 55, 90); border-radius: 16px; }\n   "
        " QFrame#bannerDimOverlay { background: rgba(0, 0, 0, 105); border:"
        " 0; border-radius: 0; }\n    QFrame#bannerOverlay { background:"
        " transparent; border: 0; border-radius: 12px; }\n   "
        " QFrame#bannerHud { background: rgba(12, 11, 16, 242); border: 1px"
        " solid rgba(212, 175, 55, 100); border-radius: 8px; min-height:"
        " 56px; }\n    QLabel#bannerCharacterName { color: #FFF4D0;"
        " background: transparent; border: 0; border-radius: 0; font-family:"
        ' "Bahnschrift", "Segoe UI"; font-size: 16px; font-weight: 800;'
        " padding: 8px 12px; }\n    QLabel#currentBannerImage { background:"
        " #0D0D15; color: #AAA3B7; border: 0; border-radius: 8px; padding:"
        " 0px; }\n    QLabel#bannerCountdown { color: #00FFCC; background:"
        ' transparent; font-family: "Bahnschrift", "Segoe UI"; font-size:'
        " 15px; font-weight: 800; padding: 8px 12px; }\n    QFrame#topBanner"
        f" {{ background: transparent; border: 1px solid {wallpaper_accent};"
        " border-radius: 10px; }\n    QPushButton#resonatorTabButton {\n   "
        f"     background: {wallpaper_panel};\n        color: {TEXT};\n       "
        f" border: 1px solid {wallpaper_border};\n        border-radius:"
        " 8px;\n        padding: 8px 10px;\n        min-height: 30px;\n   "
        " }\n    QPushButton#resonatorTabButton:hover {\n       "
        f" background: {wallpaper_surface};\n        border-color:"
        f" {wallpaper_accent};\n    }}\n   "
        ' QPushButton#resonatorTabButton[active="true"] {\n       '
        f" background: {wallpaper_surface};\n        color:"
        f" {wallpaper_accent};\n        border: 1px solid"
        f" {wallpaper_accent};\n        font-weight: 800;\n    }}\n   "
        " QFrame#skillCard { background: #171E38; border: 1px solid #323D70;"
        " border-radius: 8px; }\n    QLabel#skillIcon { background:"
        " #242A5A; color: #FFFFFF; border: 1px solid #5D5CE8; border-radius:"
        " 7px; padding: 8px; min-width: 28px; font-size: 20px; }\n   "
        " QLabel#skillTitle { color: #DDBBFF; font-weight: 800; font-size:"
        " 14px; }\n    QLabel#skillNumber { background: #3D477A; color:"
        " #FFFFFF; border-radius: 5px; padding: 7px; min-width: 16px;"
        " font-size: 14px; font-weight: 800; }\n    QLabel#bannerPortrait {"
        " background: transparent; border: 0; }\n    QLabel#bannerName {"
        ' color: #FFFFFF; font-family: "Cinzel", "Bahnschrift", "Segoe UI";'
        " font-size: 30px; font-weight: 800; }\n    QLabel#bannerSubtitle {"
        f" color: {MUTED}; font-size: 14px; }}\n    QLabel#bannerBadge {{"
        f" color: {ACCENT}; background: rgba(62, 39, 92, 180); border: 1px"
        " solid rgba(217, 70, 239, 150); border-radius: 12px; padding: 4px"
        ' 10px; }\n    QLabel#bannerBadge[element="Aero"] { color: #E8FFF8;'
        " background: #145A4A; border: 1px solid #72E6C0; }\n   "
        ' QLabel#bannerBadge[element="Glacio"] { color: #E4F8FF; background:'
        " #285A78; border: 1px solid #82D8FF; }\n   "
        ' QLabel#bannerBadge[element="Electro"] { color: #F0E8FF;'
        " background: #49356F; border: 1px solid #B78CFF; }\n   "
        ' QLabel#bannerBadge[element="Fusion"] { color: #FFF0E8; background:'
        " #713D2C; border: 1px solid #FF8A65; }\n   "
        ' QLabel#bannerBadge[element="Havoc"] { color: #FFE8EE; background:'
        " #642C43; border: 1px solid #E85D75; }\n   "
        ' QLabel#bannerBadge[element="Spectro"] { color: #FFF8D6;'
        " background: #665522; border: 1px solid #FFD76A; }\n   "
        f" QLabel#bannerRarity {{ color: {GOLD}; font-size: 18px;"
        " letter-spacing: 2px; }\n    QLabel#bannerQuote { color: #E9D5FF;"
        ' font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 12px;'
        " font-style: italic; padding: 6px; }\n    QLabel#title { color:"
        f' {GOLD}; font-family: "Cinzel", "Bahnschrift", "Segoe UI";'
        " font-size: 18px; font-weight: 700; }\n    QLabel#muted,"
        f" QLabel#eyebrow {{ color: {MUTED}; }}\n    QLabel#metricValue {{"
        f' color: {ACCENT}; font-family: "Bahnschrift", "Segoe UI"; font-size:'
        " 22px; font-weight: 700; }\n    QLineEdit, QComboBox, QSpinBox,"
        " QDoubleSpinBox {\n        background: rgba(11, 9, 20, 205);\n     "
        f"   color: {TEXT};\n        border: 1px solid rgba(124, 58, 237,"
        " 105);\n        border-radius: 8px;\n        padding: 8px;\n       "
        f" selection-background-color: {BORDER};\n    }}\n    QLineEdit:hover,"
        " QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover { border:"
        " 1px solid rgba(217, 70, 239, 180); }\n    QLineEdit:focus,"
        " QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border:"
        f" 1px solid {ACCENT}; background: rgba(26, 21, 46, 235); }}\n   "
        f" QComboBox QAbstractItemView {{ background: {CARD}; color: {TEXT};"
        f" border: 1px solid {ACCENT}; selection-background-color: {HEADER};"
        " }\n    QPushButton {\n        background: qlineargradient(x1: 0,"
        " y1: 0, x2: 0, y2: 1,\n            stop: 0 #3A2861, stop: 1"
        f" {HEADER});\n        color: {TEXT};\n        border: 1px solid"
        " rgba(217, 70, 239, 170);\n        border-radius: 8px;\n       "
        " padding: 9px 14px;\n        font-weight: 600;\n    }\n   "
        " QPushButton:hover { background: #4B3278; color: #FFFFFF; border:"
        f" 1px solid {ACCENT}; }}\n    QPushButton:pressed {{ background:"
        f" #24163D; border: 1px solid {GOLD}; }}\n   "
        " QPushButton#primaryAction { background: qlineargradient(x1: 0, y1:"
        " 0, x2: 1, y2: 1, stop: 0 #6D3FA5, stop: 1 #2F2355); border: 1px"
        f" solid {ACCENT}; color: #FFFFFF; }}\n   "
        " QPushButton#primaryAction:hover { background: #7C3AED; }\n   "
        f" QPushButton:disabled {{ color: {MUTED}; background: {BG}; }}\n   "
        f" QPushButton#playerButton {{\n        background-color: {HEADER};\n "
        f"       color: {TEXT};\n        border: 1px solid rgba(217, 70, 239,"
        " 170);\n        border-radius: 6px;\n        padding: 6px 12px;\n   "
        "     font-weight: 700;\n    }\n    QPushButton#playerButton:hover"
        f" {{\n        background-color: {BORDER};\n        border: 1px solid"
        f" {ACCENT};\n    }}\n    QPushButton#playerButton:pressed {{\n       "
        f" background-color: #2E1F42;\n        border: 1px solid {GOLD};\n    "
        "    padding: 8px 12px 4px 12px;\n    }\n   "
        " QPushButton#playerButton:disabled {\n        background-color:"
        f" {BG};\n        color: {MUTED};\n        border: 1px solid rgba(217,"
        " 70, 239, 170);\n    }\n    QTabWidget::pane { border: 0; }\n   "
        f" QTabBar::tab {{ background: rgba(19, 16, 30, 220); color: {MUTED};"
        " border: 1px solid rgba(124, 58, 237, 110); padding: 10px 18px;"
        " margin-right: 4px; border-radius: 8px; }\n   "
        " QTabBar::tab:selected { background: qlineargradient(x1: 0, y1: 0,"
        f" x2: 1, y2: 1, stop: 0 #59317D, stop: 1 {HEADER}); color: #FFFFFF;"
        f" border: 1px solid {ACCENT}; }}\n    QTabBar::tab:hover {{"
        f" background: #30204E; color: {ACCENT}; border: 1px solid rgba(217,"
        " 70, 239, 190); }\n    QTableWidget { background: rgba(11, 9, 20,"
        f" 210); alternate-background-color: {CARD}; color: {TEXT}; border:"
        " 1px solid rgba(124, 58, 237, 110); border-radius: 8px;"
        f" gridline-color: {BORDER}; selection-background-color: {BORDER};"
        f" selection-color: {TEXT}; }}\n    QHeaderView::section {{"
        f" background: {HEADER}; color: {TEXT}; border: 0; border-right: 1px"
        f" solid {BORDER}; padding: 9px 8px; font-weight: 700; }}\n   "
        " QScrollBar:vertical, QScrollBar:horizontal { background: rgba(11,"
        " 9, 20, 180); border: 0; margin: 2px; }\n   "
        " QScrollBar::handle:vertical, QScrollBar::handle:horizontal {"
        f" background: {HEADER}; border: 1px solid {ACCENT}; border-radius:"
        " 5px; min-height: 28px; min-width: 28px; }\n   "
        f" QScrollBar::handle:hover {{ background: {BORDER}; }}\n   "
        " QScrollBar::add-line, QScrollBar::sub-line { background:"
        " transparent; border: 0; }\n    QSlider::groove:horizontal {"
        f" height: 6px; background: {BG}; border: 1px solid {BORDER};"
        " border-radius: 3px; }\n    QSlider::sub-page:horizontal {"
        f" background: {HEADER}; border-radius: 3px; }}\n   "
        " QSlider::handle:horizontal { width: 16px; margin: -6px 0;"
        f" background: {TEXT}; border: 2px solid {BORDER}; border-radius: 8px;"
        f" }}\n    QProgressBar {{ background: {BG}; border: 1px solid"
        f" {BORDER}; border-radius: 4px; text-align: center; color: {TEXT};"
        f" }}\n    QProgressBar::chunk {{ background: {HEADER}; border-radius:"
        f" 3px; }}\n    QSplitter::handle {{ background: {BORDER}; width: 1px;"
        f" }}\n    QFrame#card {{ background: {wallpaper_panel}; border-color:"
        f" {wallpaper_border}; }}\n    QFrame#appHeader {{ border-color:"
        f" {wallpaper_border}; }}\n    QPushButton {{ border-color:"
        f" {wallpaper_border}; }}\n    QPushButton:hover {{ border-color:"
        f" {wallpaper_accent}; }}\n    QLineEdit, QComboBox, QSpinBox,"
        f" QDoubleSpinBox {{ border-color: {wallpaper_border}; }}\n   "
        " QLineEdit:hover, QComboBox:hover, QSpinBox:hover,"
        f" QDoubleSpinBox:hover {{ border-color: {wallpaper_accent}; }}\n   "
        f" QLabel#metricValue {{ color: {wallpaper_accent}; }}\n   "
        " QFrame#card, QFrame#appHeader, QFrame#sidebar,"
        " QFrame#upcomingBannersSection {\n        background-color:"
        f" rgba({int(wallpaper_panel[1:3], 16)},"
        f" {int(wallpaper_panel[3:5], 16)}, {int(wallpaper_panel[5:7], 16)},"
        f" {panel_alpha});\n    }}\n    QPushButton#primaryAction,"
        " QPushButton#damageCalculateButton { border-color:"
        f" {selected_accent}; color: {selected_accent}; }}\n   "
        " QPushButton#primaryAction:hover,"
        " QPushButton#damageCalculateButton:hover { border-color:"
        f" {selected_accent}; }}\n    QLabel#metricValue,"
        " QLabel#damageOutputValue, QLabel#historyMetricValue { color:"
        f" {selected_accent}; }}\n    QFrame#damageFormulaBox {{\n       "
        f" background: {wallpaper_surface};\n        border: 1px solid"
        f" {wallpaper_border};\n        border-left: 3px solid"
        f" {wallpaper_accent};\n        border-radius: 7px;\n    }}\n   "
        f" QLabel#damageFormula {{ color: {wallpaper_muted}; font-family:"
        ' "Cascadia Mono", "Consolas", monospace; font-size: 11px; }\n   '
        " QFrame#damageInputGroup {\n        background:"
        f" {wallpaper_panel};\n        border: 1px solid {wallpaper_border};\n"
        "        border-radius: 8px;\n    }\n    QLabel#damageGroupTitle {"
        f" color: {wallpaper_accent}; font-size: 10px; font-weight: 900;"
        " letter-spacing: 1px; }\n    QLabel#damageInputLabel { color:"
        f" {TEXT}; font-size: 10px; font-weight: 700; }}\n   "
        f" QAbstractSpinBox#damageInput {{ background: {wallpaper_surface};"
        f" color: {TEXT}; border: 1px solid {wallpaper_border}; border-radius:"
        " 5px; padding: 4px 6px; min-width: 86px; }\n   "
        " QAbstractSpinBox#damageInput:focus { border-color:"
        f" {wallpaper_accent}; }}\n    QPushButton#damageCalculateButton {{\n "
        f"       background: {wallpaper_panel};\n        color:"
        f" {wallpaper_accent};\n        border: 1px solid"
        f" {wallpaper_accent};\n        border-radius: 7px;\n        padding:"
        " 10px;\n        font-size: 12px;\n        font-weight: 900;\n   "
        " }\n    QPushButton#damageCalculateButton:hover { background:"
        f" {wallpaper_surface}; border: 2px solid {wallpaper_accent}; }}\n   "
        " QFrame#damageOutputCard {\n        background:"
        f" {wallpaper_panel};\n        border: 1px solid {wallpaper_border};\n"
        "        border-radius: 8px;\n    }\n    QLabel#damageOutputTitle {"
        f" color: {wallpaper_muted}; font-size: 9px; font-weight: 900;"
        " letter-spacing: 1px; }\n    QLabel#damageOutputValue { color:"
        f' {wallpaper_accent}; font-family: "Cascadia Mono", "Consolas",'
        " monospace; font-size: 20px; font-weight: 900; }\n   "
        " QFrame#historyTeamSummary {\n        background:"
        f" {wallpaper_panel};\n        border: 1px solid {wallpaper_border};\n"
        "        border-radius: 10px;\n    }\n    QLabel#historyTeamMembers"
        f" {{\n        color: {TEXT};\n        background:"
        f" {wallpaper_surface};\n        border: 1px solid"
        f" {wallpaper_border};\n        border-radius: 8px;\n        padding:"
        " 14px 10px;\n        font-size: 13px;\n        font-weight: 700;\n  "
        "  }\n    QFrame#historyQuickMetric {\n        background:"
        f" {wallpaper_panel};\n        border: 1px solid {wallpaper_border};\n"
        "        border-radius: 8px;\n    }\n    QLabel#historyMetricCaption"
        f" {{ color: {wallpaper_muted}; font-size: 9px; font-weight: 900;"
        " letter-spacing: 1px; }\n    QLabel#historyMetricValue { color:"
        f" {wallpaper_accent}; font-size: 22px; font-weight: 900; }}\n   "
        f" QFrame#historyStatCard {{\n        background: {wallpaper_panel};\n"
        f"        border: 1px solid {wallpaper_border};\n       "
        " border-radius: 9px;\n    }\n    QFrame#historyStatCard:hover {"
        f" border-color: {wallpaper_accent}; background: {wallpaper_surface};"
        " }\n    QFrame#historyStatCard QLabel#metricValue { color:"
        f" {wallpaper_accent}; font-size: 20px; font-weight: 900; }}\n   "
        " QTableWidget#historyAuditTable, QTableWidget#historySavedTable {\n"
        f"        background: {wallpaper_surface};\n       "
        f" alternate-background-color: {wallpaper_panel};\n        color:"
        f" {TEXT};\n        border: 1px solid {wallpaper_border};\n       "
        f" gridline-color: {wallpaper_border};\n       "
        f" selection-background-color: {wallpaper_border};\n       "
        f" selection-color: {TEXT};\n    }}\n   "
        " QTableWidget#historyAuditTable::item:hover,"
        " QTableWidget#historySavedTable::item:hover {\n        background:"
        f" {wallpaper_surface};\n    }}\n    QMainWindow {{ background-color:"
        f" {wallpaper_surface}; }}\n    QWidget#appShell {{ background:"
        f" transparent; color: {TEXT}; }}\n    QFrame#sidebar {{"
        f" background-color: {wallpaper_panel}; border-right-color:"
        f" {wallpaper_border}; }}\n    QFrame#card, QFrame#appHeader {{"
        f" background-color: {wallpaper_panel}; border-color:"
        f" {wallpaper_border}; }}\n    QFrame#upcomingBannersSection,"
        " QFrame#upcomingBannerCard, QFrame#upcomingBannerPastCard {"
        f" background-color: {wallpaper_panel}; border-color:"
        f" {wallpaper_border}; }}\n    QFrame#bannerTimeline,"
        " QFrame#bannerImageContainer, QFrame#bannerHud { background-color:"
        f" {wallpaper_panel}; border-color: {wallpaper_border}; }}\n   "
        " QPushButton#nav, QPushButton#navActive { background-color:"
        f" {wallpaper_panel}; border-color: {wallpaper_border}; }}\n   "
        " QPushButton#nav:hover, QPushButton#navActive:hover {"
        f" background-color: {wallpaper_surface}; border-color:"
        f" {wallpaper_accent}; }}\n    QTabWidget#mainTabs,"
        " QTabWidget#mainTabs::pane { background: transparent; }\n   "
        " QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget"
        " { background: transparent; }\n    QLineEdit, QComboBox, QSpinBox,"
        f" QDoubleSpinBox, QTextEdit {{ background-color: {wallpaper_panel};"
        f" color: {TEXT}; border-color: {wallpaper_border}; }}\n   "
        f" QPushButton#primaryAction {{ background: {wallpaper_panel}; color:"
        f" {TEXT}; border-color: {wallpaper_accent}; }}\n   "
        f" QPushButton#primaryAction:hover {{ background: {wallpaper_surface};"
        f" color: {TEXT}; border: 2px solid {wallpaper_accent}; }}\n   "
        " QLineEdit:focus, QComboBox:focus, QSpinBox:focus,"
        f" QDoubleSpinBox:focus {{ background-color: {wallpaper_surface};"
        f" border-color: {wallpaper_accent}; }}\n    QLineEdit:hover {{"
        f" background-color: {wallpaper_surface}; border: 2px solid"
        f" {wallpaper_accent}; }}\n    QTableWidget {{ background-color:"
        f" {wallpaper_panel}; alternate-background-color: {wallpaper_surface};"
        f" border-color: {wallpaper_border}; }}\n    QHeaderView::section {{"
        f" background-color: {wallpaper_surface}; color: {TEXT}; border-color:"
        f" {wallpaper_border}; }}\n    QTabBar::tab {{ background-color:"
        f" {wallpaper_panel}; color: {wallpaper_muted}; border-color:"
        f" {wallpaper_border}; }}\n    QTabBar::tab:selected {{"
        f" background-color: {wallpaper_surface}; border-color:"
        f" {wallpaper_accent}; }}\n    QScrollBar:vertical,"
        f" QScrollBar:horizontal {{ background-color: {wallpaper_surface};"
        " }\n    QProgressBar, QSlider::groove:horizontal {"
        f" background-color: {wallpaper_surface}; border-color:"
        f" {wallpaper_border}; }}\n    QLabel#title, QLabel#bannerName,"
        " QLabel#bannerQuote, QLabel#bannerSubtitle,\n   "
        " QLabel#damageInputLabel, QLabel#damageFormula, QLabel#muted,"
        " QLabel#eyebrow,\n    QLabel#skillTitle, QLabel#skillNumber,"
        " QLabel#historyTeamMembers {\n        background: transparent;\n   "
        f"     opacity: 1.0;\n    }}\n    QLabel#title {{ color: {GOLD}; }}\n "
        "   QLabel#bannerName, QLabel#skillTitle { color: #FFFFFF; }\n   "
        " QLabel#bannerQuote { color: #F4EFFF; }\n   "
        " QLabel#bannerSubtitle, QLabel#muted, QLabel#eyebrow { color:"
        " #E1E5F0; }\n    QLabel#damageInputLabel, QLabel#damageFormula,"
        " QLabel#historyTeamMembers { color: #F2F0FF; }\n   "
        " QTabWidget#mainTabs QLabel {\n        color: #FFFFFF;\n       "
        " background: transparent;\n    }\n    QFrame#topBanner QLabel {\n "
        "       color: #FFFFFF;\n        background: transparent;\n    }\n  "
        '  QTabWidget#mainTabs QLabel#bannerBadge[element="Aero"] { color:'
        " #E8FFF8; }\n    QTabWidget#mainTabs"
        ' QLabel#bannerBadge[element="Glacio"] { color: #E4F8FF; }\n   '
        ' QTabWidget#mainTabs QLabel#bannerBadge[element="Electro"] { color:'
        " #F0E8FF; }\n    QTabWidget#mainTabs"
        ' QLabel#bannerBadge[element="Fusion"] { color: #FFF0E8; }\n   '
        ' QTabWidget#mainTabs QLabel#bannerBadge[element="Havoc"] { color:'
        " #FFE8EE; }\n    QTabWidget#mainTabs"
        ' QLabel#bannerBadge[element="Spectro"] { color: #FFF8D6; }\n   '
        " QFrame#card, QFrame#appHeader, QFrame#sidebar,"
        " QFrame#upcomingBannersSection {\n        background-color:"
        f" rgba({int(wallpaper_panel[1:3], 16)},"
        f" {int(wallpaper_panel[3:5], 16)}, {int(wallpaper_panel[5:7], 16)},"
        f" {panel_alpha});\n    }}\n    "
    )
