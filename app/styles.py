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
    "Aero": "#54C7E8",
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


def _wallpaper_palette(wallpaper: str) -> tuple[str, str, str]:
    source = QUrl(wallpaper).toLocalFile() if wallpaper.startswith("file:") else wallpaper
    image = QImage(source or str(PROJECT_ROOT / "Assets" / "app_background_reference.png"))
    if image.isNull():
        return CARD, BORDER, ACCENT

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
    surface = QColor(max(8, average.red() // 5), max(8, average.green() // 5), max(12, average.blue() // 5))
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
    return surface.name(), border.name(), accent.name()


def application_qss(show_background: bool = True, wallpaper: str = "") -> str:
    global CURRENT_GLOW_COLOR
    background_rule = f"background-color: {BG};"
    wallpaper_card, wallpaper_border, wallpaper_accent = (
        _wallpaper_palette(wallpaper) if show_background else (CARD, BORDER, ACCENT)
    )
    CURRENT_GLOW_COLOR = wallpaper_accent
    return f"""
    QMainWindow {{
        {background_rule}
        color: {TEXT};
    }}
    QWidget {{ background: transparent; color: {TEXT}; font-family: "Bahnschrift", "Segoe UI"; font-size: 13px; }}
    QLabel {{ background: transparent; }}
    QWidget#appShell {{ background: transparent; }}
    QFrame#sidebar {{ background: rgba(12, 16, 32, 224); border-right: 1px solid #202744; }}
    QTabWidget#mainTabs {{ background: transparent; border: 0; }}
    QTabWidget#mainTabs::pane {{ border: 0; background: transparent; }}
    QPushButton#nav, QPushButton#navActive {{ text-align: left; border: 0; padding: 10px; border-radius: 7px; }}
    QPushButton#nav {{ background: #161D39; color: #EDEAFF; }}
    QPushButton#nav:hover {{ background: #24265A; border: 1px solid #A855F7; }}
    QPushButton#navActive {{ background: #48209A; color: #FFFFFF; font-weight: 800; }}
    QPushButton#nav[element="Aero"], QPushButton#navActive[element="Aero"] {{ background: #164A5A; border: 1px solid #54C7E8; color: #D9F8FF; }}
    QPushButton#nav[element="Glacio"], QPushButton#navActive[element="Glacio"] {{ background: #285A78; border: 1px solid #82D8FF; color: #E4F8FF; }}
    QPushButton#nav[element="Electro"], QPushButton#navActive[element="Electro"] {{ background: #49356F; border: 1px solid #B78CFF; color: #F0E8FF; }}
    QPushButton#nav[element="Fusion"], QPushButton#navActive[element="Fusion"] {{ background: #713D2C; border: 1px solid #FF8A65; color: #FFF0E8; }}
    QPushButton#nav[element="Havoc"], QPushButton#navActive[element="Havoc"] {{ background: #642C43; border: 1px solid #E85D75; color: #FFE8EE; }}
    QPushButton#nav[element="Spectro"], QPushButton#navActive[element="Spectro"] {{ background: #665522; border: 1px solid #FFD76A; color: #FFF8D6; }}
    QPushButton#nav[element="Aero"]:hover, QPushButton#navActive[element="Aero"]:hover {{ background: #226B7D; }}
    QPushButton#nav[element="Glacio"]:hover, QPushButton#navActive[element="Glacio"]:hover {{ background: #397A9D; }}
    QPushButton#nav[element="Electro"]:hover, QPushButton#navActive[element="Electro"]:hover {{ background: #644B91; }}
    QPushButton#nav[element="Fusion"]:hover, QPushButton#navActive[element="Fusion"]:hover {{ background: #975039; }}
    QPushButton#nav[element="Havoc"]:hover, QPushButton#navActive[element="Havoc"]:hover {{ background: #873B58; }}
    QPushButton#nav[element="Spectro"]:hover, QPushButton#navActive[element="Spectro"]:hover {{ background: #87702D; }}
    QFrame#card {{
        background: rgba(15, 20, 40, 218);
        border: 1px solid rgba(168, 85, 247, 155);
        border-radius: 12px;
    }}
    QFrame#appHeader {{ background: rgba(13, 17, 34, 225); border: 1px solid rgba(57, 64, 113, 180); border-radius: 10px; }}
    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{ background: transparent; border: 0; }}
    QFrame#videoSurface {{ background: #080611; border: 1px solid rgba(217, 70, 239, 125); border-radius: 8px; }}
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
        background: rgba(20, 19, 31, 245);
        border: 1px solid rgba(255, 255, 255, 35);
        border-radius: 10px;
    }}
    QFrame#upcomingBannerCard:hover {{ border: 1px solid rgba(0, 217, 255, 180); background: rgba(25, 27, 45, 248); }}
    QFrame#upcomingBannerPastCard {{
        background: rgba(20, 19, 31, 245);
        border: 1px solid rgba(255, 255, 255, 45);
        border-radius: 8px;
    }}
    QFrame#upcomingBannerPastCard:hover {{ border: 1px solid rgba(0, 217, 255, 170); }}
    QLabel#upcomingBannerImage {{
        background: #191827;
        color: #9DA3B4;
        border: 1px solid rgba(255, 255, 255, 35);
        border-radius: 7px;
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
    QLabel#upcomingBannerDetails {{ color: #9DA3B4; font-size: 10px; font-weight: 700; }}
    QFrame#bannerImageContainer {{ background: #14131F; border: 2px solid rgba(212, 175, 55, 90); border-radius: 16px; }}
    QFrame#bannerDimOverlay {{ background: rgba(0, 0, 0, 105); border: 0; border-radius: 0; }}
    QFrame#bannerOverlay {{ background: transparent; border: 0; border-radius: 12px; }}
    QFrame#bannerHud {{ background: rgba(12, 11, 16, 242); border: 1px solid rgba(212, 175, 55, 100); border-radius: 8px; min-height: 56px; }}
    QLabel#bannerCharacterName {{ color: #FFF4D0; background: transparent; border: 0; border-radius: 0; font-family: "Bahnschrift", "Segoe UI"; font-size: 16px; font-weight: 800; padding: 8px 12px; }}
    QLabel#currentBannerImage {{ background: #0D0D15; color: #AAA3B7; border: 0; border-radius: 8px; padding: 0px; }}
    QLabel#bannerCountdown {{ color: #00FFCC; background: transparent; font-family: "Bahnschrift", "Segoe UI"; font-size: 15px; font-weight: 800; padding: 8px 12px; }}
    QFrame#topBanner {{ background: transparent; }}
    QFrame#skillCard {{ background: #171E38; border: 1px solid #323D70; border-radius: 8px; }}
    QLabel#skillIcon {{ background: #242A5A; color: #FFFFFF; border: 1px solid #5D5CE8; border-radius: 7px; padding: 8px; min-width: 28px; font-size: 20px; }}
    QLabel#skillTitle {{ color: #DDBBFF; font-weight: 800; font-size: 14px; }}
    QLabel#skillNumber {{ background: #3D477A; color: #FFFFFF; border-radius: 5px; padding: 7px; min-width: 16px; font-size: 14px; font-weight: 800; }}
    QLabel#bannerPortrait {{ background: transparent; border: 0; }}
    QLabel#bannerName {{ color: #FFFFFF; font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 30px; font-weight: 800; }}
    QLabel#bannerSubtitle {{ color: {MUTED}; font-size: 14px; }}
    QLabel#bannerBadge {{ color: {ACCENT}; background: rgba(62, 39, 92, 180); border: 1px solid rgba(217, 70, 239, 150); border-radius: 12px; padding: 4px 10px; }}
    QLabel#bannerBadge[element="Aero"] {{ color: #D9F8FF; background: #164A5A; border: 1px solid #54C7E8; }}
    QLabel#bannerBadge[element="Glacio"] {{ color: #E4F8FF; background: #285A78; border: 1px solid #82D8FF; }}
    QLabel#bannerBadge[element="Electro"] {{ color: #F0E8FF; background: #49356F; border: 1px solid #B78CFF; }}
    QLabel#bannerBadge[element="Fusion"] {{ color: #FFF0E8; background: #713D2C; border: 1px solid #FF8A65; }}
    QLabel#bannerBadge[element="Havoc"] {{ color: #FFE8EE; background: #642C43; border: 1px solid #E85D75; }}
    QLabel#bannerBadge[element="Spectro"] {{ color: #FFF8D6; background: #665522; border: 1px solid #FFD76A; }}
    QLabel#bannerRarity {{ color: {GOLD}; font-size: 18px; letter-spacing: 2px; }}
    QLabel#bannerQuote {{ color: #E9D5FF; font-family: "Cinzel", "Bahnschrift", "Segoe UI"; font-size: 15px; font-style: italic; padding: 16px; }}
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
    QFrame#card {{ background: {wallpaper_card}; border-color: {wallpaper_border}; }}
    QFrame#appHeader {{ border-color: {wallpaper_border}; }}
    QPushButton {{ border-color: {wallpaper_border}; }}
    QPushButton:hover {{ border-color: {wallpaper_accent}; }}
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ border-color: {wallpaper_border}; }}
    QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{ border-color: {wallpaper_accent}; }}
    QLabel#metricValue {{ color: {wallpaper_accent}; }}
    """