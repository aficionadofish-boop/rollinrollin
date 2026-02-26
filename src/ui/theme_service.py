"""ThemeService — centralized stylesheet management for RollinRollin.

Provides three preset stylesheets (Dark, Default, High Contrast) and a custom
color template builder. Drives app-wide theming via QApplication.setStyleSheet().
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# Preset stylesheet strings
# ---------------------------------------------------------------------------

_DARK_STYLESHEET = """
QWidget {
    background-color: #2B2B2B;
    color: #E0E0E0;
}
QMainWindow {
    background-color: #2B2B2B;
}
QTabWidget::pane {
    border: 1px solid #555555;
    background-color: #2B2B2B;
}
QTabBar::tab {
    background-color: #353535;
    color: #CCCCCC;
    padding: 6px 14px;
    border: 1px solid #555555;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #2B2B2B;
    color: #FFFFFF;
}
QTabBar::tab:hover:!selected {
    background-color: #3C3C3C;
}
QPushButton {
    background-color: #3C3C3C;
    color: #E0E0E0;
    border: 1px solid #555555;
    padding: 4px 12px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #4A4A4A;
    border-color: #777777;
}
QPushButton:pressed {
    background-color: #333333;
}
QPushButton:disabled {
    background-color: #2F2F2F;
    color: #666666;
    border-color: #444444;
}
QPushButton:checked {
    border: 2px solid #4DA6FF;
    color: #4DA6FF;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #1E1E1E;
    color: #E0E0E0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 2px 4px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #4DA6FF;
}
QComboBox::drop-down {
    border-left: 1px solid #555555;
    background-color: #3C3C3C;
}
QComboBox QAbstractItemView {
    background-color: #1E1E1E;
    color: #E0E0E0;
    selection-background-color: #4DA6FF;
    selection-color: #FFFFFF;
    border: 1px solid #555555;
}
QGroupBox {
    border: 1px solid #555555;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    color: #E0E0E0;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 4px;
    color: #CCCCCC;
}
QScrollArea {
    border: 1px solid #444444;
    background-color: #2B2B2B;
}
QScrollBar:vertical {
    background-color: #2B2B2B;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #555555;
    min-height: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #777777;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #2B2B2B;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #555555;
    min-width: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #777777;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    border: 1px solid #555555;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #4DA6FF;
    color: #FFFFFF;
}
QListWidget::item:hover:!selected {
    background-color: #353535;
}
QSplitter::handle {
    background-color: #444444;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QFrame[frameShape="6"] {
    background-color: #323232;
    border: 1px solid #444444;
    border-radius: 4px;
}
QCheckBox {
    color: #E0E0E0;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #555555;
    border-radius: 2px;
    background-color: #1E1E1E;
}
QCheckBox::indicator:checked {
    background-color: #4DA6FF;
    border-color: #4DA6FF;
}
QLabel {
    background-color: transparent;
    color: #E0E0E0;
}
QToolTip {
    background-color: #3C3C3C;
    color: #E0E0E0;
    border: 1px solid #555555;
    padding: 4px;
}
QMenu {
    background-color: #2B2B2B;
    color: #E0E0E0;
    border: 1px solid #555555;
}
QMenu::item:selected {
    background-color: #4DA6FF;
    color: #FFFFFF;
}
QInputDialog, QMessageBox {
    background-color: #2B2B2B;
    color: #E0E0E0;
}
QHeaderView {
    background-color: #2B2B2B;
    color: #E0E0E0;
    border: none;
}
QHeaderView::section {
    background-color: #353535;
    color: #CCCCCC;
    border: 1px solid #444444;
    padding: 4px 6px;
}
QHeaderView::section:hover {
    background-color: #3C3C3C;
}
QTableView {
    background-color: #1E1E1E;
    color: #E0E0E0;
    gridline-color: #444444;
    border: 1px solid #555555;
    selection-background-color: #4DA6FF;
    selection-color: #FFFFFF;
}
QTableView::item:alternate {
    background-color: #252525;
}
"""

_DEFAULT_STYLESHEET = """
QWidget {
    background-color: #F5F5F5;
    color: #1A1A1A;
}
QMainWindow {
    background-color: #F5F5F5;
}
QTabWidget::pane {
    border: 1px solid #CCCCCC;
    background-color: #F5F5F5;
}
QTabBar::tab {
    background-color: #E8E8E8;
    color: #333333;
    padding: 6px 14px;
    border: 1px solid #CCCCCC;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #F5F5F5;
    color: #1A1A1A;
}
QTabBar::tab:hover:!selected {
    background-color: #DCDCDC;
}
QPushButton {
    background-color: #E0E0E0;
    color: #1A1A1A;
    border: 1px solid #BBBBBB;
    padding: 4px 12px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #D0D0D0;
    border-color: #999999;
}
QPushButton:pressed {
    background-color: #C4C4C4;
}
QPushButton:disabled {
    background-color: #ECECEC;
    color: #AAAAAA;
    border-color: #D0D0D0;
}
QPushButton:checked {
    border: 2px solid #2979FF;
    color: #2979FF;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #CCCCCC;
    border-radius: 3px;
    padding: 2px 4px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #2979FF;
}
QComboBox::drop-down {
    border-left: 1px solid #CCCCCC;
    background-color: #E0E0E0;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #1A1A1A;
    selection-background-color: #2979FF;
    selection-color: #FFFFFF;
    border: 1px solid #CCCCCC;
}
QGroupBox {
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    color: #1A1A1A;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 4px;
    color: #333333;
}
QScrollArea {
    border: 1px solid #DDDDDD;
    background-color: #F5F5F5;
}
QScrollBar:vertical {
    background-color: #F5F5F5;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #BBBBBB;
    min-height: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #999999;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #F5F5F5;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #BBBBBB;
    min-width: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #999999;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #FFFFFF;
    color: #1A1A1A;
    border: 1px solid #CCCCCC;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #2979FF;
    color: #FFFFFF;
}
QListWidget::item:hover:!selected {
    background-color: #EBEBEB;
}
QSplitter::handle {
    background-color: #CCCCCC;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QFrame[frameShape="6"] {
    background-color: #EEEEEE;
    border: 1px solid #DDDDDD;
    border-radius: 4px;
}
QCheckBox {
    color: #1A1A1A;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 1px solid #BBBBBB;
    border-radius: 2px;
    background-color: #FFFFFF;
}
QCheckBox::indicator:checked {
    background-color: #2979FF;
    border-color: #2979FF;
}
QLabel {
    background-color: transparent;
    color: #1A1A1A;
}
QToolTip {
    background-color: #E8E8E8;
    color: #1A1A1A;
    border: 1px solid #CCCCCC;
    padding: 4px;
}
QMenu {
    background-color: #F5F5F5;
    color: #1A1A1A;
    border: 1px solid #CCCCCC;
}
QMenu::item:selected {
    background-color: #2979FF;
    color: #FFFFFF;
}
QInputDialog, QMessageBox {
    background-color: #F5F5F5;
    color: #1A1A1A;
}
QHeaderView {
    background-color: #F5F5F5;
    color: #1A1A1A;
    border: none;
}
QHeaderView::section {
    background-color: #E8E8E8;
    color: #333333;
    border: 1px solid #DDDDDD;
    padding: 4px 6px;
}
QHeaderView::section:hover {
    background-color: #DCDCDC;
}
QTableView {
    background-color: #FFFFFF;
    color: #1A1A1A;
    gridline-color: #DDDDDD;
    border: 1px solid #CCCCCC;
    selection-background-color: #2979FF;
    selection-color: #FFFFFF;
}
QTableView::item:alternate {
    background-color: #F0F0F0;
}
"""

_HIGH_CONTRAST_STYLESHEET = """
QWidget {
    background-color: #000000;
    color: #FFFFFF;
}
QMainWindow {
    background-color: #000000;
}
QTabWidget::pane {
    border: 2px solid #FFFFFF;
    background-color: #000000;
}
QTabBar::tab {
    background-color: #000000;
    color: #FFFFFF;
    padding: 6px 14px;
    border: 2px solid #FFFFFF;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #1A1A1A;
    color: #FFD700;
}
QTabBar::tab:hover:!selected {
    background-color: #1A1A1A;
}
QPushButton {
    background-color: #000000;
    color: #FFFFFF;
    border: 2px solid #FFFFFF;
    padding: 4px 12px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #1A1A1A;
    border-color: #FFD700;
    color: #FFD700;
}
QPushButton:pressed {
    background-color: #1A1A1A;
}
QPushButton:disabled {
    background-color: #000000;
    color: #555555;
    border-color: #555555;
}
QPushButton:checked {
    border: 2px solid #FFD700;
    color: #FFD700;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {
    background-color: #0A0A0A;
    color: #FFFFFF;
    border: 2px solid #FFFFFF;
    border-radius: 3px;
    padding: 2px 4px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {
    border-color: #FFD700;
}
QComboBox::drop-down {
    border-left: 2px solid #FFFFFF;
    background-color: #0A0A0A;
}
QComboBox QAbstractItemView {
    background-color: #0A0A0A;
    color: #FFFFFF;
    selection-background-color: #FFD700;
    selection-color: #000000;
    border: 2px solid #FFFFFF;
}
QGroupBox {
    border: 2px solid #FFFFFF;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    color: #FFFFFF;
}
QGroupBox::title {
    subcontrol-origin: margin;
    padding: 0 4px;
    color: #FFD700;
}
QScrollArea {
    border: 2px solid #FFFFFF;
    background-color: #000000;
}
QScrollBar:vertical {
    background-color: #000000;
    width: 12px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #FFFFFF;
    min-height: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical:hover {
    background-color: #FFD700;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: #000000;
    height: 12px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #FFFFFF;
    min-width: 20px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #FFD700;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QListWidget {
    background-color: #0A0A0A;
    color: #FFFFFF;
    border: 2px solid #FFFFFF;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #FFD700;
    color: #000000;
}
QListWidget::item:hover:!selected {
    background-color: #1A1A1A;
}
QSplitter::handle {
    background-color: #FFFFFF;
}
QSplitter::handle:horizontal {
    width: 3px;
}
QSplitter::handle:vertical {
    height: 3px;
}
QFrame[frameShape="6"] {
    background-color: #0A0A0A;
    border: 2px solid #FFFFFF;
    border-radius: 4px;
}
QCheckBox {
    color: #FFFFFF;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 14px;
    height: 14px;
    border: 2px solid #FFFFFF;
    border-radius: 2px;
    background-color: #0A0A0A;
}
QCheckBox::indicator:checked {
    background-color: #FFD700;
    border-color: #FFD700;
}
QLabel {
    background-color: transparent;
    color: #FFFFFF;
}
QToolTip {
    background-color: #0A0A0A;
    color: #FFFFFF;
    border: 2px solid #FFD700;
    padding: 4px;
}
QMenu {
    background-color: #000000;
    color: #FFFFFF;
    border: 2px solid #FFFFFF;
}
QMenu::item:selected {
    background-color: #FFD700;
    color: #000000;
}
QInputDialog, QMessageBox {
    background-color: #000000;
    color: #FFFFFF;
}
QHeaderView {
    background-color: #000000;
    color: #FFFFFF;
    border: none;
}
QHeaderView::section {
    background-color: #0A0A0A;
    color: #FFFFFF;
    border: 2px solid #FFFFFF;
    padding: 4px 6px;
}
QHeaderView::section:hover {
    background-color: #1A1A1A;
    color: #FFD700;
}
QTableView {
    background-color: #0A0A0A;
    color: #FFFFFF;
    gridline-color: #FFFFFF;
    border: 2px solid #FFFFFF;
    selection-background-color: #FFD700;
    selection-color: #000000;
}
QTableView::item:alternate {
    background-color: #111111;
}
"""

# Custom template — placeholders: {bg}, {text}, {accent}, {input_bg}, {border}
_CUSTOM_TEMPLATE = """
QWidget {{
    background-color: {bg};
    color: {text};
}}
QMainWindow {{
    background-color: {bg};
}}
QTabWidget::pane {{
    border: 1px solid {border};
    background-color: {bg};
}}
QTabBar::tab {{
    background-color: {input_bg};
    color: {text};
    padding: 6px 14px;
    border: 1px solid {border};
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}}
QTabBar::tab:selected {{
    background-color: {bg};
    color: {text};
}}
QTabBar::tab:hover:!selected {{
    background-color: {input_bg};
}}
QPushButton {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    padding: 4px 12px;
    border-radius: 3px;
}}
QPushButton:hover {{
    border-color: {accent};
}}
QPushButton:pressed {{
    background-color: {bg};
}}
QPushButton:disabled {{
    color: {border};
    border-color: {border};
}}
QPushButton:checked {{
    border: 2px solid {accent};
    color: {accent};
}}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 3px;
    padding: 2px 4px;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {accent};
}}
QComboBox::drop-down {{
    border-left: 1px solid {border};
    background-color: {input_bg};
}}
QComboBox QAbstractItemView {{
    background-color: {input_bg};
    color: {text};
    selection-background-color: {accent};
    selection-color: #FFFFFF;
    border: 1px solid {border};
}}
QGroupBox {{
    border: 1px solid {border};
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    color: {text};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    padding: 0 4px;
    color: {text};
}}
QScrollArea {{
    border: 1px solid {border};
    background-color: {bg};
}}
QScrollBar:vertical {{
    background-color: {bg};
    width: 12px;
    border: none;
}}
QScrollBar::handle:vertical {{
    background-color: {border};
    min-height: 20px;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background-color: {bg};
    height: 12px;
    border: none;
}}
QScrollBar::handle:horizontal {{
    background-color: {border};
    min-width: 20px;
    border-radius: 4px;
    margin: 2px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}
QListWidget {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    border-radius: 3px;
}}
QListWidget::item:selected {{
    background-color: {accent};
    color: #FFFFFF;
}}
QFrame[frameShape="6"] {{
    background-color: {input_bg};
    border: 1px solid {border};
    border-radius: 4px;
}}
QCheckBox {{
    color: {text};
    spacing: 6px;
}}
QCheckBox::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {border};
    border-radius: 2px;
    background-color: {input_bg};
}}
QCheckBox::indicator:checked {{
    background-color: {accent};
    border-color: {accent};
}}
QLabel {{
    background-color: transparent;
    color: {text};
}}
QToolTip {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    padding: 4px;
}}
QMenu {{
    background-color: {bg};
    color: {text};
    border: 1px solid {border};
}}
QMenu::item:selected {{
    background-color: {accent};
    color: #FFFFFF;
}}
QInputDialog, QMessageBox {{
    background-color: {bg};
    color: {text};
}}
QHeaderView {{
    background-color: {bg};
    color: {text};
    border: none;
}}
QHeaderView::section {{
    background-color: {input_bg};
    color: {text};
    border: 1px solid {border};
    padding: 4px 6px;
}}
QTableView {{
    background-color: {input_bg};
    color: {text};
    gridline-color: {border};
    border: 1px solid {border};
    selection-background-color: {accent};
    selection-color: #FFFFFF;
}}
"""


# ---------------------------------------------------------------------------
# Helper functions for custom color derivation
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert #RRGGBB hex string to (r, g, b) tuple."""
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) to #RRGGBB hex string."""
    return f"#{r:02X}{g:02X}{b:02X}"


def _darken(hex_color: str) -> str:
    """Darken a hex color by shifting each channel ~15% toward 0."""
    r, g, b = _hex_to_rgb(hex_color)
    factor = 0.85
    return _rgb_to_hex(int(r * factor), int(g * factor), int(b * factor))


def _midtone(hex1: str, hex2: str) -> str:
    """Return the average (midtone) of two hex colors."""
    r1, g1, b1 = _hex_to_rgb(hex1)
    r2, g2, b2 = _hex_to_rgb(hex2)
    return _rgb_to_hex((r1 + r2) // 2, (g1 + g2) // 2, (b1 + b2) // 2)


# ---------------------------------------------------------------------------
# ThemeService
# ---------------------------------------------------------------------------

class ThemeService:
    """Single source of truth for all app-wide stylesheets.

    Provides three preset stylesheets and a custom color template builder.
    Call apply() to immediately recolor the entire Qt application.
    """

    _PRESETS: dict[str, str] = {
        "dark": _DARK_STYLESHEET,
        "default": _DEFAULT_STYLESHEET,
        "high_contrast": _HIGH_CONTRAST_STYLESHEET,
    }

    def build_stylesheet(self, settings) -> str:
        """Build the full app stylesheet from AppSettings.

        Returns a preset stylesheet when no custom colors are set.
        Falls back to the custom template with color substitution otherwise.
        """
        has_custom = bool(
            settings.text_color or settings.bg_color or settings.accent_color
        )
        if settings.theme_name in self._PRESETS and not has_custom:
            return self._PRESETS[settings.theme_name]

        # Custom colors: format template with user colors, falling back to preset defaults
        base = self._get_preset_defaults(settings.theme_name)
        bg = settings.bg_color or base["bg"]
        text = settings.text_color or base["text"]
        accent = settings.accent_color or base["accent"]
        input_bg = _darken(bg) if settings.bg_color else base["input_bg"]
        border = (
            _midtone(bg, text)
            if (settings.bg_color or settings.text_color)
            else base["border"]
        )
        return _CUSTOM_TEMPLATE.format(
            bg=bg,
            text=text,
            accent=accent,
            input_bg=input_bg,
            border=border,
        )

    def apply(self, settings) -> None:
        """Apply the stylesheet derived from settings to the running QApplication."""
        from PySide6.QtWidgets import QApplication
        stylesheet = self.build_stylesheet(settings)
        QApplication.instance().setStyleSheet(stylesheet)

    def get_accent_color(self, settings) -> str:
        """Return the effective accent color for the current theme/settings."""
        if settings.accent_color:
            return settings.accent_color
        return self._get_preset_defaults(settings.theme_name)["accent"]

    def get_theme_service(self) -> "ThemeService":
        """Return self (convenience accessor when accessed via MainWindow)."""
        return self

    def _get_preset_defaults(self, theme_name: str) -> dict:
        """Return the base color dict for a given preset name."""
        defaults = {
            "dark": {
                "bg": "#2B2B2B",
                "text": "#E0E0E0",
                "accent": "#4DA6FF",
                "input_bg": "#1E1E1E",
                "border": "#555555",
            },
            "default": {
                "bg": "#F5F5F5",
                "text": "#1A1A1A",
                "accent": "#2979FF",
                "input_bg": "#FFFFFF",
                "border": "#CCCCCC",
            },
            "high_contrast": {
                "bg": "#000000",
                "text": "#FFFFFF",
                "accent": "#FFD700",
                "input_bg": "#0A0A0A",
                "border": "#FFFFFF",
            },
        }
        return defaults.get(theme_name, defaults["dark"])
