"""Exercise character search and language changes with real Qt widgets."""

from __future__ import annotations

import sys
from unittest.mock import Mock

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QObject,
    QPoint,
    QSettings,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QLabel

from wuwa_calculator.infrastructure import catalog
from wuwa_calculator.ui import language as language_module
from wuwa_calculator.ui.panels import history_video_player
from wuwa_calculator.ui.panels import window as window_module
from wuwa_calculator.ui.rendering import (
    apply_alpha_mask,
    draw_centered,
    smooth_scaled,
    transparent_pixmap,
)
from wuwa_calculator.ui.tabs import (
    history_tab,
    home_tab,
    multimedia_tab,
    teams_tab,
)
from wuwa_calculator.ui.tabs import settings_tab as settings_module
from wuwa_calculator.ui.tabs.resonator_tab import ResonatorTab


@pytest.fixture(scope="module", name="qt_app")
def fixture_qt_app():
    """Create a headless Qt application for widget integration tests."""
    with pytest.MonkeyPatch.context() as patcher:
        patcher.setenv("QT_QPA_PLATFORM", "offscreen")
        patcher.setenv("QT_QPA_PLATFORMTHEME", "")
        patcher.setenv("QT_STYLE_OVERRIDE", "Fusion")
        app = QApplication.instance() or QApplication([])
        yield app


@pytest.fixture(name="ui_state")
def fixture_ui_state(qt_app, tmp_path, monkeypatch):
    """Isolate preferences, network replies, and Qt signal failures."""
    settings_path = tmp_path / "preferences.ini"

    def settings_factory(*_args, **_kwargs):
        return QSettings(str(settings_path), QSettings.Format.IniFormat)

    for module in (language_module, window_module, settings_module):
        monkeypatch.setattr(module, "QSettings", settings_factory)
    language_module.language_settings.cache_clear()
    manager = language_module.language_settings()
    # Home starts background network workers; these tests exercise search.
    monkeypatch.setattr(
        window_module.WuwaQtWindow, "_ensure_main_tab", lambda *_args: None
    )
    requests = []

    class PendingReply(QObject):
        """Inert network reply used to test widgets without downloads."""

        finished = Signal()

    def get_image(network, request):
        requests.append(request.url().toString())
        return PendingReply(network)

    monkeypatch.setattr(
        "wuwa_calculator.ui.tabs.resonator_tab.QNetworkAccessManager.get",
        get_image,
    )
    signal_errors = []
    monkeypatch.setattr(
        sys, "excepthook", lambda *_args: signal_errors.append(_args[1])
    )
    yield manager, settings_factory, requests
    for widget in qt_app.topLevelWidgets():
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qt_app.processEvents()
    language_module.language_settings.cache_clear()
    assert not signal_errors


def open_character(window, text):
    """Submit a character search through the real window button."""
    window.character_id_entry.setText(text)
    window.character_load_button.click()
    return window.tabs.currentWidget()


def test_search_augusta_opens_populated_tab(ui_state):
    """Verify search augusta opens populated tab."""
    _manager, _settings, requests = ui_state
    window = window_module.WuwaQtWindow()

    tab = open_character(window, "augusta")

    assert isinstance(tab, ResonatorTab)
    assert tab.current_id == "augusta"
    assert tab.character_name.text() == "Augusta"
    assert tab.element_box.currentText() == "Electro"
    assert tab.weapon_name.text() == "Thunderflare Dominion"
    assert tab.kit_layout.count() == len(catalog.character("augusta").skills)
    assert tab.kit_layout.count() > 0
    assert requests
    assert window.character_status.text() == ""

    window.character_id_entry.setText("  ÁUGUSTA  ")
    window.character_id_entry.returnPressed.emit()
    assert window.tabs.currentWidget() is tab
    assert list(window.character_tabs) == ["augusta"]
    assert window.character_open_order == ["augusta"]


def test_global_language_updates_open_tabs_without_resetting_stats(ui_state):
    """Verify global language updates open tabs without resetting stats."""
    manager, _settings, requests = ui_state
    window = window_module.WuwaQtWindow()
    settings = settings_module.SettingsTab(host=window)
    augusta = open_character(window, "augusta")
    suisui = open_character(window, "suisui")
    augusta.stat_labels["Base ATK"].setText("4321")
    augusta.damage_fields["attack_total"].setValue(4321)
    portuguese_passive = suisui.weapon_passive_text
    request_count = len(requests)

    settings.language_box.setCurrentText("EN")

    assert manager.code == "EN"
    assert language_module.LanguageSettings().code == "EN"
    for tab in (augusta, suisui):
        assert tab.language == "EN"
        assert tab.language_box.currentText() == "EN"
    assert suisui.weapon_passive_text != portuguese_passive
    assert "BASE ATK" in suisui.weapon_passive_text
    assert augusta.stat_labels["Base ATK"].text() == "4321"
    assert augusta.damage_fields["attack_total"].value() == 4321
    assert len(requests) == request_count
    assert window.tabs.currentWidget() is suisui

    augusta.language_box.setCurrentText("PT-BR")

    assert manager.code == "PT-BR"
    assert settings.language_box.currentText() == "PT-BR"
    assert suisui.language_box.currentText() == "PT-BR"
    assert suisui.weapon_passive_text == portuguese_passive


def test_settings_work_before_loading_any_character(ui_state):
    """Verify settings work before loading any character."""
    # Exercise rejection/reset internals without showing modal UI dialogs.
    # pylint: disable=protected-access
    manager, _settings, _requests = ui_state
    window = window_module.WuwaQtWindow()
    settings = settings_module.SettingsTab(host=window)
    settings.language_box.setCurrentText("EN")
    settings.opacity_slider.setValue(70)
    settings.background_box.setChecked(False)

    tab = open_character(window, "augusta")

    assert manager.code == "EN"
    assert tab.language == "EN"
    assert window.preferences.value("interface_opacity", type=int) == 70
    assert not window.preferences.value("background", type=bool)
    assert settings.confirm_exit_box.parent() is not None

    settings._clear_characters()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not window.character_tabs
    assert not window.character_open_order
    assert not window.character_sidebar_rows
    assert window.character_sidebar_layout.count() == 0

    settings._restore_defaults()
    assert manager.code == "PT-BR"
    assert settings.language_box.currentText() == "PT-BR"
    assert language_module.LanguageSettings().code == "PT-BR"
    assert settings.opacity_slider.value() == 85
    assert settings.background_box.isChecked()


def test_image_policy_paths_do_not_raise_name_errors(ui_state):
    """Verify image policy paths do not raise name errors."""
    # Exercise rejection/reset internals without showing modal UI dialogs.
    # pylint: disable=protected-access
    _manager, _settings, requests = ui_state
    tab = ResonatorTab(initial_id="augusta")
    target = QLabel()
    request_count = len(requests)

    tab._load_image("https://example.com/image.png", target, "missing")
    assert target.text() == "missing"
    tab._load_image("/outside/image.png", target, "missing")
    assert target.text() == "missing"
    assert len(requests) == request_count


def test_language_choice_is_canonical_and_saved_once(ui_state):
    """Verify language choice is canonical and saved once."""
    manager, settings_factory, _requests = ui_state
    changes = []
    manager.changed.connect(changes.append)

    manager.set_language("en")
    manager.set_language("EN")

    assert changes == ["EN"]
    assert settings_factory().value("ui/language") == "EN"
    assert language_module.LanguageSettings().code == "EN"


@pytest.mark.parametrize(
    "view_name", ["home", "teams", "history", "multimedia"]
)
def test_refactored_views_construct_without_network(
    ui_state, monkeypatch, view_name
):
    """Construct complete views after extracting workers and shared widgets."""
    _manager, _settings, _requests = ui_state
    monkeypatch.setattr(home_tab, "load_cached_banner", lambda: None)
    monkeypatch.setattr(
        home_tab.HomeTab, "_start_banner_refresh", lambda *_: None
    )
    monkeypatch.setattr(
        home_tab.HomeTab, "_start_catalog_refresh", lambda *_: None
    )
    monkeypatch.setattr(teams_tab, "load_teams", lambda: [])
    monkeypatch.setattr(history_tab, "load_teams", lambda: [])
    monkeypatch.setattr(history_tab, "history_records", lambda: [])
    if view_name == "multimedia":
        # Empty tabs must not import or initialize native multimedia.
        monkeypatch.setattr(
            history_video_player,
            "_multimedia_types",
            Mock(side_effect=AssertionError("Unexpected multimedia load")),
        )
    constructors = {
        "home": home_tab.HomeTab,
        "teams": teams_tab.TeamsTab,
        "history": history_tab.HistoryTab,
        "multimedia": multimedia_tab.MultimediaTab,
    }
    widget = constructors[view_name]()
    assert widget.layout() is not None


def test_shared_painting_preserves_scaling_centering_and_mask(qt_app):
    """Preserve transparent margins, aspect ratio, and artwork masks."""
    source = QPixmap(4, 2)
    source.fill(Qt.GlobalColor.red)
    scaled = smooth_scaled(source, 16, 16, Qt.AspectRatioMode.KeepAspectRatio)
    assert scaled.size() == QSize(16, 8)
    canvas = transparent_pixmap(QSize(16, 16))
    painter = QPainter(canvas)
    draw_centered(painter, scaled, 16, 16)
    painter.end()
    assert canvas.toImage().pixelColor(8, 8).red() == 255
    assert canvas.toImage().pixelColor(0, 0).alpha() == 0

    mask = transparent_pixmap(QSize(16, 16))
    painter = QPainter(mask)
    painter.fillRect(4, 4, 8, 8, Qt.GlobalColor.white)
    painter.end()
    target = QLabel()
    target.resize(16, 16)
    apply_alpha_mask(target, mask)
    qt_app.processEvents()
    assert target.mask().contains(QPoint(8, 8))
    assert not target.mask().contains(QPoint(0, 0))
