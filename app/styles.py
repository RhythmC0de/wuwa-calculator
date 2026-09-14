"""Global visual system for the PySide6 application."""

# * EDITAVEL: altere cores globais e regras QSS aqui; o wallpaper gera uma paleta complementar.
# ! Nao use #RRGGBBAA no QColor: _with_alpha produz o formato Qt #AARRGGBB.

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from pathlib import Path

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
DEFAULT_WALLPAPER = f"url({(PROJECT_ROOT / 'Assets' / 'app_background_reference.png').as_posix()})"


def _with_alpha(color: str, opacity: int) -> str:
    alpha = max(0, min(255, opacity))
    return f"#{alpha:02X}{color.lstrip('#')}"


def apply_glow(widget: QWidget, blur: float = 24.0, opacity: int = 180) -> None:
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


def apply_element_glow(widget: QWidget, element: str, blur: float = 24.0, opacity: int = 180) -> None:
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
    for widget in [root, *root.findChildren(QWidget)]:
        mode = widget.property("_glow_mode")
        if mode == "global":
            apply_glow(widget, float(widget.property("_glow_blur")), int(widget.property("_glow_opacity")))
        elif mode == "element":
            apply_element_glow(
                widget,
                str(widget.property("_glow_element")),
                float(widget.property("_glow_blur")),
                int(widget.property("_glow_opacity")),
            )


def _wallpaper_palette(wallpaper: str) -> tuple[str, str, str, str, str]:
    source = QUrl(wallpaper).toLocalFile() if wallpaper.startswith("file:") else wallpaper
    image = QImage(source or str(PROJECT_ROOT / "Assets" / "app_background_reference.png"))
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
    return surface.name(), panel.name(), border.name(), accent.name(), muted.name()


def _accent_preset(name: str) -> str:
    return {
        "Ciano Tethys": "#6FEAFF",
        "Dourado Sol": "#FFD76A",
        "Roxo Nécro": "#B78CFF",
        "Vermelho Alerta": "#FF6B6B",
    }.get(name, "#6FEAFF")


def application_qss(
    show_background: bool = True,
    wallpaper: str = "",
    interface_opacity: int = 85,
    accent_theme: str = "Ciano Tethys",
) -> str:
    global CURRENT_GLOW_COLOR
    background_rule = f"background-color: {BG};"
    wallpaper_surface, wallpaper_panel, wallpaper_border, wallpaper_accent, wallpaper_muted = (
        _wallpaper_palette(wallpaper) if show_background else (BG, CARD, BORDER, ACCENT, MUTED)
    )
    selected_accent = _accent_preset(accent_theme)
    CURRENT_GLOW_COLOR = selected_accent
    # Acrylic stays translucent while the setting changes its material intensity.
    panel_alpha = max(150, min(225, round(112 + interface_opacity * 1.13)))
    return f"""
    QMainWindow {{
        {background_rule}
        color: {TEXT};
    }}
    QWidget {{ background: transparent; color: {TEXT}; font-family: "Bahnschrift", "Segoe UI"; font-size: 13px; }}
    QLabel {{ background: transparent; }}
    QWidget#appShell {{ background: transparent; }}
    QFrame#sidebar {{ background: rgba(12, 16, 32, {panel_alpha}); border-right: 1px solid #202744; }}
    QTabWidget#mainTabs {{ background: transparent; border: 0; }}
    QTabWidget#mainTabs::pane {{ border: 0; background: transparent; }}
    QPushButton#nav, QPushButton#navActive {{ text-align: left; border: 0; padding: 10px; border-radius: 7px; }}
    QPushButton#nav {{ background: #161D39; color: #EDEAFF; }}
    QPushButton#nav:hover {{ background: #24265A; border: 1px solid #A855F7; }}
    QPushButton#navActive {{ background: #48209A; color: #FFFFFF; font-weight: 800; }}
    QPushButton#nav[element="Aero"], QPushButton#navActive[element="Aero"] {{ background: #145A4A; border: 1px solid #72E6C0; color: #E8FFF8; }}
    QPushButton#nav[element="Glacio"], QPushButton#navActive[element="Glacio"] {{ background: #285A78; border: 1px solid #82D8FF; color: #E4F8FF; }}
    QPushButton#nav[element="Electro"], QPushButton#navActive[element="Electro"] {{ background: #49356F; border: 1px solid #B78CFF; color: #F0E8FF; }}
    QPushButton#nav[element="Fusion"], QPushButton#navActive[element="Fusion"] {{ background: #713D2C; border: 1px solid #FF8A65; color: #FFF0E8; }}
    QPushButton#nav[element="Havoc"], QPushButton#navActive[element="Havoc"] {{ background: #642C43; border: 1px solid #E85D75; color: #FFE8EE; }}
    QPushButton#nav[element="Spectro"], QPushButton#navActive[element="Spectro"] {{ background: #665522; border: 1px solid #FFD76A; color: #FFF8D6; }}
    QPushButton#nav[element="Aero"]:hover, QPushButton#navActive[element="Aero"]:hover {{ background: #1E8068; }}
    QPushButton#nav[element="Glacio"]:hover, QPushButton#navActive[element="Glacio"]:hover {{ background: #397A9D; }}
    QPushButton#nav[element="Electro"]:hover, QPushButton#navActive[element="Electro"]:hover {{ background: #644B91; }}
    QPushButton#nav[element="Fusion"]:hover, QPushButton#navActive[element="Fusion"]:hover {{ background: #975039; }}
    QPushButton#nav[element="Havoc"]:hover, QPushButton#navActive[element="Havoc"]:hover {{ background: #873B58; }}
    QPushButton#nav[element="Spectro"]:hover, QPushButton#navActive[element="Spectro"]:hover {{ background: #87702D; }}
    QFrame#card {{
        background: rgba(15, 20, 40, {panel_alpha});
        border: 1px solid rgba(168, 85, 247, 155);
        border-radius: 12px;
    }}
    QFrame#appHeader {{ background: rgba(13, 17, 34, {panel_alpha}); border: 1px solid rgba(57, 64, 113, 180); border-radius: 10px; }}
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background: transparent; border: 0; }}
    QFrame#videoSurface {{ background: rgba(11, 13, 18, 235); border: 1px solid rgba(0, 217, 255, 70); border-radius: 8px; }}
    QFrame#mediaToolbar {{ background: rgba(8, 14, 27, 235); border: 1px solid rgba(0, 217, 255, 90); border-radius: 7px; }}
    QFrame#mediaSupportPanel {{ background: rgba(7, 15, 28, 185); border: 1px solid rgba(0, 217, 255, 70); border-radius: 8px; }}
    QFrame#mediaSupportPanel QFrame#card {{ background: transparent; border: 0; border-radius: 0; }}
    QLabel#videoHud {{ color: #8FF6FF; background: rgba(5, 12, 22, 205); border: 1px solid rgba(0, 217, 255, 100); border-radius: 5px; padding: 4px 9px; font-size: 10px; font-weight: 800; }}
    QPushButton#mediaControlButton, QPushButton#mediaBrowseButton, QPushButton#mediaPlayButton, QPushButton#mediaStopButton {{ background: rgba(20, 35, 55, 230); color: #DDFBFF; border: 1px solid rgba(0, 217, 255, 85); border-radius: 5px; min-height: 26px; font-weight: 800; }}
    QPushButton#mediaControlButton:hover, QPushButton#mediaBrowseButton:hover, QPushButton#mediaPlayButton:hover, QPushButton#mediaStopButton:hover {{ background: rgba(0, 110, 145, 220); border-color: #6FEAFF; }}
    QLabel#mediaTimeLabel, QLabel#mediaControlLabel {{ color: #B7DCE5; font-size: 10px; font-weight: 700; }}
    QSlider#playerProgress {{ min-height: 14px; }}
    QFrame#frequencyProtocolBar {{ background: rgba(11, 13, 18, 220); border: 1px solid rgba(0, 217, 255, 70); border-radius: 7px; }}
    QLabel#frequencyProtocolTitle {{ color: #6FEAFF; font-size: 12px; font-weight: 800; letter-spacing: 1px; }}
    QLabel#frequencyProtocolSubtitle {{ color: #8A99AD; font-size: 9px; margin-top: 4px; }}
    QLabel#frequencyProtocolBadge {{ color: #00D9FF; font-family: "Bahnschrift", "Segoe UI", sans-serif; font-size: 11px; border: 1px solid rgba(0, 217, 255, 76); border-radius: 5px; padding: 4px 10px; min-height: 28px; white-space: nowrap; }}
    QLabel#mediaSectionTitle {{ color: #F2F0FF; font-size: 13px; font-weight: 800; }}
    QLabel#mediaPanelDuration {{ color: #67D9FF; font-size: 12px; font-weight: 800; }}
    QFrame#eventRow {{ background: rgba(11, 13, 18, 190); border: 1px solid rgba(0, 217, 255, 50); border-radius: 7px; }}
    QFrame#eventRow[category="Skill"] {{ border-left: 3px solid #6FEAFF; }}
    QFrame#eventRow[category="Ultimate"] {{ border-left: 3px solid #C084FC; }}
    QFrame#eventRow[category="Buff"] {{ border-left: 3px solid #FFD76A; }}
    QFrame#eventRow[stripe="even"] {{ background: rgba(20, 29, 45, 205); }}
    QFrame#eventRow[active="true"] {{ background: rgba(72, 32, 154, 215); border-color: #B77CFF; }}
    QLabel#eventTimestamp {{ color: #C7C8EA; font-size: 11px; font-weight: 800; }}
    QLabel#eventIcon {{ color: #B77CFF; background: rgba(35, 38, 65, 210); border: 1px solid #6547A8; border-radius: 12px; font-size: 13px; }}
    QLabel#eventTitle {{ color: #F2F0FF; font-size: 11px; font-weight: 800; }}
    QLabel#eventDescription {{ color: #A8A8D5; font-size: 9px; }}
    QLabel#eventCategory {{ color: #6FEAFF; font-size: 8px; font-weight: 900; }}
    QFrame#eventRow[category="Ultimate"] QLabel#eventCategory {{ color: #C084FC; }}
    QFrame#eventRow[category="Buff"] QLabel#eventCategory {{ color: #FFD76A; }}
    QFrame#eventRow[active="true"] QLabel#eventTitle, QFrame#eventRow[active="true"] QLabel#eventDescription, QFrame#eventRow[active="true"] QLabel#eventTimestamp {{ color: #FFFFFF; }}
    QLabel#metricName, QLabel#optionLabel {{ color: {MUTED}; font-size: 9px; text-transform: uppercase; }}
    QLabel#metricValue {{ color: #F2F0FF; font-size: 13px; font-weight: 900; }}
    QComboBox#mediaOptionCombo {{ min-width: 104px; padding: 6px 8px; font-size: 11px; background: rgba(11, 16, 34, 210); border-color: rgba(103, 112, 168, 180); }}
    QLabel#dpsMetric {{ color: #8FF6FF; background: rgba(10, 28, 43, 225); border: 1px solid rgba(0, 217, 255, 105); border-radius: 6px; padding: 7px 9px; font-size: 10px; font-weight: 900; }}
    QPushButton#dpsAnalyzeButton {{ color: #06141C; background: #6FEAFF; border: 1px solid #B8F8FF; border-radius: 6px; padding: 7px 12px; font-weight: 900; }}
    QPushButton#dpsAnalyzeButton:hover {{ background: #B8F8FF; border-color: #FFFFFF; }}
    QPushButton#mediaQuickAction {{ background: rgba(11, 13, 18, 225); color: {TEXT}; border: 1px solid rgba(212, 175, 55, 150); border-radius: 6px; padding: 8px 7px; font-size: 11px; font-weight: 700; }}
    QPushButton#mediaQuickAction:hover {{ background: rgba(31, 35, 42, 235); border-color: #D4AF37; }}
    QFrame#currentBannerCard {{ background: transparent; border: 0; border-radius: 0; }}
    QFrame#bannerTimeline {{
        background: rgba(20, 19, 31, 188);
        border: 1px solid rgba(150, 180, 205, 95);
        border-radius: 10px;
    }}
    QLabel#bannerTimelineTitle {{ color: #F7D878; font-size: 18px; font-weight: 800; }}
    QLabel#bannerCurrentHighlight {{
        color: #FFFFFF;
        background: rgba(12, 16, 30, 225);
        border: 1px solid rgba(212, 175, 55, 165);
        border-radius: 6px;
        padding: 6px 12px;
        font-family: "Bahnschrift", "Segoe UI";
        font-size: 18px;
        font-weight: 800;
    }}
    QLabel#bannerTimelineSection {{ color: #D6D5E8; font-size: 11px; font-weight: 800; text-transform: uppercase; }}
    QFrame#bannerTimelinePast {{
        background: rgba(12, 12, 22, 150);
        border-right: 1px solid rgba(133, 143, 180, 100);
        border-radius: 6px;
        min-width: 332px;
    }}
    QFrame#bannerTimelineFuture {{ background: transparent; border: 0; }}
    QScrollArea#bannerTimelineScroll {{ background: transparent; border: 0; }}
    QFrame#bannerTimelineCard {{
        background: rgba(31, 30, 48, 225);
        border: 1px solid rgba(133, 143, 180, 125);
        border-radius: 7px;
    }}
    QFrame#bannerTimelineCard:hover {{
        border: 1px solid rgba(103, 232, 212, 190);
        background: rgba(40, 39, 62, 235);
    }}
    QFrame#bannerTimelinePastCard {{
        background: rgba(31, 30, 48, 190);
        border: 1px solid rgba(133, 143, 180, 105);
        border-radius: 6px;
    }}
    QFrame#bannerTimelinePastCard:hover {{
        border: 1px solid rgba(103, 232, 212, 170);
    }}
    QLabel#bannerTimelineThumb {{
        background: #0D0D15;
        color: #67E8D4;
        border: 1px solid rgba(212, 175, 55, 100);
        border-radius: 5px;
    }}
    QLabel#bannerTimelineName {{ color: #F3F1FF; font-size: 12px; font-weight: 800; }}
    QLabel#bannerTimelineTBA {{
        color: #8FF6FF;
        background: rgba(25, 34, 62, 215);
        border: 1px solid rgba(180, 119, 255, 190);
        border-radius: 5px;
        padding: 5px 8px;
        font-family: "Bahnschrift", "Segoe UI";
        font-size: 14px;
        font-weight: 900;
    }}
    QLabel#bannerTimelineRarity {{ color: #FFD76A; font-size: 12px; font-weight: 800; }}
    QLabel#bannerTimelineDate {{
        color: #7DEBFF;
        font-family: "Bahnschrift", "Segoe UI";
        font-size: 11px;
        font-weight: 800;
        background: rgba(22, 42, 62, 205);
        border: 1px solid rgba(103, 232, 212, 145);
        border-radius: 4px;
        padding: 3px 6px;
        text-shadow: 0 0 8px #35D9FF;
    }}
    QLabel#bannerTimelineTag {{ color: #67E8D4; font-size: 9px; font-weight: 800; }}
    QLabel#bannerTimelineEmpty {{ color: #A8A8D5; padding: 14px; }}
    QPushButton#bannerTimelineArrow {{
        background: rgba(52, 49, 76, 220);
        color: #F7D878;
        border: 1px solid rgba(103, 232, 212, 120);
        border-radius: 5px;
        font-size: 16px;
        font-weight: 800;
        padding: 0;
    }}
    QPushButton#bannerTimelineArrow:hover {{ background: #3F5270; color: #FFFFFF; }}
    QFrame#upcomingBannersSection {{
        background: rgba(12, 11, 16, 218);
        border: 1px solid rgba(255, 255, 255, 28);
        border-radius: 12px;
    }}
    QLabel#upcomingBannersTitle {{ color: #F5F5F5; font-size: 15px; font-weight: 900; }}
    QLabel#upcomingBannersSubtitle {{ color: #9DA3B4; font-size: 9px; }}
    QPushButton#upcomingBannersTrackerButton {{
        background: rgba(20, 35, 65, 220);
        color: #8FEFFF;
        border: 1px solid rgba(0, 217, 255, 120);
        border-radius: 7px;
        padding: 8px 12px;
        font-size: 11px;
        font-weight: 700;
    }}
    QPushButton#upcomingBannersTrackerButton:hover {{ background: #173B5B; border: 1px solid #00D9FF; }}
    QFrame#upcomingBannerCard {{
        background: rgba(12, 16, 30, 235);
        border: 1px solid rgba(0, 217, 255, 150);
        border-radius: 16px;
    }}
    QFrame#upcomingBannerCard:hover {{ border: 1px solid #6FEAFF; background: rgba(25, 27, 45, 248); }}
    QFrame#upcomingBannerPastCard {{
        background: rgba(12, 16, 30, 235);
        border: 1px solid rgba(0, 217, 255, 150);
        border-radius: 16px;
    }}
    QFrame#upcomingBannerPastCard[hovered="true"] {{
        border: 0;
        background: rgba(25, 27, 45, 248);
    }}
    QLabel#upcomingBannerImage {{
        background: transparent;
        color: #9DA3B4;
        border: 0;
        border-radius: 16px;
    }}
    QFrame#upcomingBannerOverlay {{
        background: rgba(0, 0, 0, 155);
        border: 1px solid rgba(0, 217, 255, 95);
        border-radius: 6px;
    }}
    QLabel#upcomingBannerBadge {{
        color: #0C0B10;
        background: #00D9FF;
        border-radius: 5px;
        padding: 3px 7px;
        font-size: 9px;
        font-weight: 900;
    }}
    QLabel#upcomingBannerName {{ color: #F5F5F5; font-size: 13px; font-weight: 900; }}
    QLabel#upcomingBannerDetails {{ color: #D5D9E4; font-size: 10px; font-weight: 700; }}
    QFrame#bannerImageContainer {{ background: #14131F; border: 2px solid rgba(212, 175, 55, 90); border-radius: 16px; }}
    QFrame#bannerDimOverlay {{ background: rgba(0, 0, 0, 105); border: 0; border-radius: 0; }}
    QFrame#bannerOverlay {{ background: transparent; border: 0; border-radius: 12px; }}
    QFrame#bannerHud {{ background: rgba(12, 11, 16, 242); border: 1px solid rgba(212, 175, 55, 100); border-radius: 8px; min-height: 56px; }}
    QLabel#bannerCharacterName {{ color: #FFF4D0; background: transparent; border: 0; border-radius: 0; font-family: "Bahnschrift", "Segoe UI"; font-size: 16px; font-weight: 800; padding: 8px 12px; }}
    QLabel#currentBannerImage {{ background: #0D0D15; color: #AAA3B7; border: 0; border-radius: 8px; padding: 0px; }}
    QLabel#bannerCountdown {{ color: #00FFCC; background: transparent; font-family: "Bahnschrift", "Segoe UI"; font-size: 15px; font-weight: 800; padding: 8px 12px; }}
    QFrame#topBanner {{ background: transparent; border: 1px solid {wallpaper_accent}; border-radius: 10px; }}
    QPushButton#resonatorTabButton {{
        background: {wallpaper_panel};
        color: {TEXT};
        border: 1px solid {wallpaper_border};
        border-radius: 8px;
        padding: 8px 10px;
        min-height: 30px;
    }}
    QPushButton#resonatorTabButton:hover {{
        background: {wallpaper_surface};
        border-color: {wallpaper_accent};
    }}
    QPushButton#resonatorTabButton[active="true"] {{
        background: {wallpaper_surface};
        color: {wallpaper_accent};
        border: 1px solid {wallpaper_accent};
        font-weight: 800;
    }}
    QFrame#skillCard {{ background: #171E38; border: 1px solid #323D70; border-radius: 8px; }}
    QLabel#skillIcon {{ background: #242A5A; color: #FFFFFF; border: 1px solid #5D5CE8; border-radius: 7px; padding: 8px; min-width: 28px; font-size: 20px; }}
    QLabel#skillTitle {{ color: #DDBBFF; font-weight: 800; font-size: 14px; }}
    QLabel#skillNumber {{ background: #3D477A; color: #FFFFFF; border-radius: 5px; padding: 7px; min-width: 16px; font-size: 14px; font-weight: 800; }}
    QLabel#bannerPortrait {{ background: transparent; border: 0; }}
    QLabel#bannerName {{ color: #FFFFFF; font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 30px; font-weight: 800; }}
    QLabel#bannerSubtitle {{ color: {MUTED}; font-size: 14px; }}
    QLabel#bannerBadge {{ color: {ACCENT}; background: rgba(62, 39, 92, 180); border: 1px solid rgba(217, 70, 239, 150); border-radius: 12px; padding: 4px 10px; }}
    QLabel#bannerBadge[element="Aero"] {{ color: #E8FFF8; background: #145A4A; border: 1px solid #72E6C0; }}
    QLabel#bannerBadge[element="Glacio"] {{ color: #E4F8FF; background: #285A78; border: 1px solid #82D8FF; }}
    QLabel#bannerBadge[element="Electro"] {{ color: #F0E8FF; background: #49356F; border: 1px solid #B78CFF; }}
    QLabel#bannerBadge[element="Fusion"] {{ color: #FFF0E8; background: #713D2C; border: 1px solid #FF8A65; }}
    QLabel#bannerBadge[element="Havoc"] {{ color: #FFE8EE; background: #642C43; border: 1px solid #E85D75; }}
    QLabel#bannerBadge[element="Spectro"] {{ color: #FFF8D6; background: #665522; border: 1px solid #FFD76A; }}
    QLabel#bannerRarity {{ color: {GOLD}; font-size: 18px; letter-spacing: 2px; }}
    QLabel#bannerQuote {{ color: #E9D5FF; font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 12px; font-style: italic; padding: 6px; }}
    QLabel#title {{ color: {GOLD}; font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 18px; font-weight: 700; }}
    QLabel#muted, QLabel#eyebrow {{ color: {MUTED}; }}
    QLabel#metricValue {{ color: {ACCENT}; font-family: "Bahnschrift", "Segoe UI"; font-size: 22px; font-weight: 700; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
        background: rgba(11, 9, 20, 205);
        color: {TEXT};
        border: 1px solid rgba(124, 58, 237, 105);
        border-radius: 8px;
        padding: 8px;
        selection-background-color: {BORDER};
    }}
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border: 1px solid rgba(217, 70, 239, 180); }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {ACCENT}; background: rgba(26, 21, 46, 235); }}
    QComboBox QAbstractItemView {{ background: {CARD}; color: {TEXT}; border: 1px solid {ACCENT}; selection-background-color: {HEADER}; }}
    QPushButton {{
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 #3A2861, stop: 1 {HEADER});
        color: {TEXT};
        border: 1px solid rgba(217, 70, 239, 170);
        border-radius: 8px;
        padding: 9px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: #4B3278; color: #FFFFFF; border: 1px solid {ACCENT}; }}
    QPushButton:pressed {{ background: #24163D; border: 1px solid {GOLD}; }}
    QPushButton#primaryAction {{ background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #6D3FA5, stop: 1 #2F2355); border: 1px solid {ACCENT}; color: #FFFFFF; }}
    QPushButton#primaryAction:hover {{ background: #7C3AED; }}
    QPushButton:disabled {{ color: {MUTED}; background: {BG}; }}
    QPushButton#playerButton {{
        background-color: {HEADER};
        color: {TEXT};
        border: 1px solid rgba(217, 70, 239, 170);
        border-radius: 6px;
        padding: 6px 12px;
        font-weight: 700;
    }}
    QPushButton#playerButton:hover {{
        background-color: {BORDER};
        border: 1px solid {ACCENT};
    }}
    QPushButton#playerButton:pressed {{
        background-color: #2E1F42;
        border: 1px solid {GOLD};
        padding: 8px 12px 4px 12px;
    }}
    QPushButton#playerButton:disabled {{
        background-color: {BG};
        color: {MUTED};
        border: 1px solid rgba(217, 70, 239, 170);
    }}
    QTabWidget::pane {{ border: 0; }}
    QTabBar::tab {{ background: rgba(19, 16, 30, 220); color: {MUTED}; border: 1px solid rgba(124, 58, 237, 110); padding: 10px 18px; margin-right: 4px; border-radius: 8px; }}
    QTabBar::tab:selected {{ background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #59317D, stop: 1 {HEADER}); color: #FFFFFF; border: 1px solid {ACCENT}; }}
    QTabBar::tab:hover {{ background: #30204E; color: {ACCENT}; border: 1px solid rgba(217, 70, 239, 190); }}
    QTableWidget {{ background: rgba(11, 9, 20, 210); alternate-background-color: {CARD}; color: {TEXT}; border: 1px solid rgba(124, 58, 237, 110); border-radius: 8px; gridline-color: {BORDER}; selection-background-color: {BORDER}; selection-color: {TEXT}; }}
    QHeaderView::section {{ background: {HEADER}; color: {TEXT}; border: 0; border-right: 1px solid {BORDER}; padding: 9px 8px; font-weight: 700; }}
    QScrollBar:vertical, QScrollBar:horizontal {{ background: rgba(11, 9, 20, 180); border: 0; margin: 2px; }}
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{ background: {HEADER}; border: 1px solid {ACCENT}; border-radius: 5px; min-height: 28px; min-width: 28px; }}
    QScrollBar::handle:hover {{ background: {BORDER}; }}
    QScrollBar::add-line, QScrollBar::sub-line {{ background: transparent; border: 0; }}
    QSlider::groove:horizontal {{ height: 6px; background: {BG}; border: 1px solid {BORDER}; border-radius: 3px; }}
    QSlider::sub-page:horizontal {{ background: {HEADER}; border-radius: 3px; }}
    QSlider::handle:horizontal {{ width: 16px; margin: -6px 0; background: {TEXT}; border: 2px solid {BORDER}; border-radius: 8px; }}
    QProgressBar {{ background: {BG}; border: 1px solid {BORDER}; border-radius: 4px; text-align: center; color: {TEXT}; }}
    QProgressBar::chunk {{ background: {HEADER}; border-radius: 3px; }}
    QSplitter::handle {{ background: {BORDER}; width: 1px; }}
    QFrame#card {{ background: {wallpaper_panel}; border-color: {wallpaper_border}; }}
    QFrame#appHeader {{ border-color: {wallpaper_border}; }}
    QPushButton {{ border-color: {wallpaper_border}; }}
    QPushButton:hover {{ border-color: {wallpaper_accent}; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ border-color: {wallpaper_border}; }}
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {wallpaper_accent}; }}
    QLabel#metricValue {{ color: {wallpaper_accent}; }}
    QFrame#card, QFrame#appHeader, QFrame#sidebar, QFrame#upcomingBannersSection {{
        background-color: rgba({int(wallpaper_panel[1:3], 16)}, {int(wallpaper_panel[3:5], 16)}, {int(wallpaper_panel[5:7], 16)}, {panel_alpha});
    }}
    QPushButton#primaryAction, QPushButton#damageCalculateButton {{ border-color: {selected_accent}; color: {selected_accent}; }}
    QPushButton#primaryAction:hover, QPushButton#damageCalculateButton:hover {{ border-color: {selected_accent}; }}
    QLabel#metricValue, QLabel#damageOutputValue, QLabel#historyMetricValue {{ color: {selected_accent}; }}
    QFrame#damageFormulaBox {{
        background: {wallpaper_surface};
        border: 1px solid {wallpaper_border};
        border-left: 3px solid {wallpaper_accent};
        border-radius: 7px;
    }}
    QLabel#damageFormula {{ color: {wallpaper_muted}; font-family: "Cascadia Mono", "Consolas", monospace; font-size: 11px; }}
    QFrame#damageInputGroup {{
        background: {wallpaper_panel};
        border: 1px solid {wallpaper_border};
        border-radius: 8px;
    }}
    QLabel#damageGroupTitle {{ color: {wallpaper_accent}; font-size: 10px; font-weight: 900; letter-spacing: 1px; }}
    QLabel#damageInputLabel {{ color: {TEXT}; font-size: 10px; font-weight: 700; }}
    QAbstractSpinBox#damageInput {{ background: {wallpaper_surface}; color: {TEXT}; border: 1px solid {wallpaper_border}; border-radius: 5px; padding: 4px 6px; min-width: 86px; }}
    QAbstractSpinBox#damageInput:focus {{ border-color: {wallpaper_accent}; }}
    QPushButton#damageCalculateButton {{
        background: {wallpaper_panel};
        color: {wallpaper_accent};
        border: 1px solid {wallpaper_accent};
        border-radius: 7px;
        padding: 10px;
        font-size: 12px;
        font-weight: 900;
    }}
    QPushButton#damageCalculateButton:hover {{ background: {wallpaper_surface}; border: 2px solid {wallpaper_accent}; }}
    QFrame#damageOutputCard {{
        background: {wallpaper_panel};
        border: 1px solid {wallpaper_border};
        border-radius: 8px;
    }}
    QLabel#damageOutputTitle {{ color: {wallpaper_muted}; font-size: 9px; font-weight: 900; letter-spacing: 1px; }}
    QLabel#damageOutputValue {{ color: {wallpaper_accent}; font-family: "Cascadia Mono", "Consolas", monospace; font-size: 20px; font-weight: 900; }}
    QFrame#historyTeamSummary {{
        background: {wallpaper_panel};
        border: 1px solid {wallpaper_border};
        border-radius: 10px;
    }}
    QLabel#historyTeamMembers {{
        color: {TEXT};
        background: {wallpaper_surface};
        border: 1px solid {wallpaper_border};
        border-radius: 8px;
        padding: 14px 10px;
        font-size: 13px;
        font-weight: 700;
    }}
    QFrame#historyQuickMetric {{
        background: {wallpaper_panel};
        border: 1px solid {wallpaper_border};
        border-radius: 8px;
    }}
    QLabel#historyMetricCaption {{ color: {wallpaper_muted}; font-size: 9px; font-weight: 900; letter-spacing: 1px; }}
    QLabel#historyMetricValue {{ color: {wallpaper_accent}; font-size: 22px; font-weight: 900; }}
    QFrame#historyStatCard {{
        background: {wallpaper_panel};
        border: 1px solid {wallpaper_border};
        border-radius: 9px;
    }}
    QFrame#historyStatCard:hover {{ border-color: {wallpaper_accent}; background: {wallpaper_surface}; }}
    QFrame#historyStatCard QLabel#metricValue {{ color: {wallpaper_accent}; font-size: 20px; font-weight: 900; }}
    QTableWidget#historyAuditTable, QTableWidget#historySavedTable {{
        background: {wallpaper_surface};
        alternate-background-color: {wallpaper_panel};
        color: {TEXT};
        border: 1px solid {wallpaper_border};
        gridline-color: {wallpaper_border};
        selection-background-color: {wallpaper_border};
        selection-color: {TEXT};
    }}
    QTableWidget#historyAuditTable::item:hover, QTableWidget#historySavedTable::item:hover {{
        background: {wallpaper_surface};
    }}
    QMainWindow {{ background-color: {wallpaper_surface}; }}
    QWidget#appShell {{ background: transparent; color: {TEXT}; }}
    QFrame#sidebar {{ background-color: {wallpaper_panel}; border-right-color: {wallpaper_border}; }}
    QFrame#card, QFrame#appHeader {{ background-color: {wallpaper_panel}; border-color: {wallpaper_border}; }}
    QFrame#upcomingBannersSection, QFrame#upcomingBannerCard, QFrame#upcomingBannerPastCard {{ background-color: {wallpaper_panel}; border-color: {wallpaper_border}; }}
    QFrame#bannerTimeline, QFrame#bannerImageContainer, QFrame#bannerHud {{ background-color: {wallpaper_panel}; border-color: {wallpaper_border}; }}
    QPushButton#nav, QPushButton#navActive {{ background-color: {wallpaper_panel}; border-color: {wallpaper_border}; }}
    QPushButton#nav:hover, QPushButton#navActive:hover {{ background-color: {wallpaper_surface}; border-color: {wallpaper_accent}; }}
    QTabWidget#mainTabs, QTabWidget#mainTabs::pane {{ background: transparent; }}
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background: transparent; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {{ background-color: {wallpaper_panel}; color: {TEXT}; border-color: {wallpaper_border}; }}
    QPushButton#primaryAction {{ background: {wallpaper_panel}; color: {TEXT}; border-color: {wallpaper_accent}; }}
    QPushButton#primaryAction:hover {{ background: {wallpaper_surface}; color: {TEXT}; border: 2px solid {wallpaper_accent}; }}
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ background-color: {wallpaper_surface}; border-color: {wallpaper_accent}; }}
    QLineEdit:hover {{ background-color: {wallpaper_surface}; border: 2px solid {wallpaper_accent}; }}
    QTableWidget {{ background-color: {wallpaper_panel}; alternate-background-color: {wallpaper_surface}; border-color: {wallpaper_border}; }}
    QHeaderView::section {{ background-color: {wallpaper_surface}; color: {TEXT}; border-color: {wallpaper_border}; }}
    QTabBar::tab {{ background-color: {wallpaper_panel}; color: {wallpaper_muted}; border-color: {wallpaper_border}; }}
    QTabBar::tab:selected {{ background-color: {wallpaper_surface}; border-color: {wallpaper_accent}; }}
    QScrollBar:vertical, QScrollBar:horizontal {{ background-color: {wallpaper_surface}; }}
    QProgressBar, QSlider::groove:horizontal {{ background-color: {wallpaper_surface}; border-color: {wallpaper_border}; }}
    QLabel#title, QLabel#bannerName, QLabel#bannerQuote, QLabel#bannerSubtitle,
    QLabel#damageInputLabel, QLabel#damageFormula, QLabel#muted, QLabel#eyebrow,
    QLabel#skillTitle, QLabel#skillNumber, QLabel#historyTeamMembers {{
        background: transparent;
        opacity: 1.0;
    }}
    QLabel#title {{ color: {GOLD}; }}
    QLabel#bannerName, QLabel#skillTitle {{ color: #FFFFFF; }}
    QLabel#bannerQuote {{ color: #F4EFFF; }}
    QLabel#bannerSubtitle, QLabel#muted, QLabel#eyebrow {{ color: #E1E5F0; }}
    QLabel#damageInputLabel, QLabel#damageFormula, QLabel#historyTeamMembers {{ color: #F2F0FF; }}
    QTabWidget#mainTabs QLabel {{
        color: #FFFFFF;
        background: transparent;
    }}
    QFrame#topBanner QLabel {{
        color: #FFFFFF;
        background: transparent;
    }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Aero"] {{ color: #E8FFF8; }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Glacio"] {{ color: #E4F8FF; }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Electro"] {{ color: #F0E8FF; }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Fusion"] {{ color: #FFF0E8; }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Havoc"] {{ color: #FFE8EE; }}
    QTabWidget#mainTabs QLabel#bannerBadge[element="Spectro"] {{ color: #FFF8D6; }}
    QFrame#card, QFrame#appHeader, QFrame#sidebar, QFrame#upcomingBannersSection {{
        background-color: rgba({int(wallpaper_panel[1:3], 16)}, {int(wallpaper_panel[3:5], 16)}, {int(wallpaper_panel[5:7], 16)}, {panel_alpha});
    }}
    """