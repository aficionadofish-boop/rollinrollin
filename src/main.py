"""RollinRollin — application entry point."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.app import MainWindow


def _resolve_icon_path() -> str:
    """Return the absolute path to icon.ico.

    When running frozen (PyInstaller onefile), sys._MEIPASS points to the
    temporary extraction directory where bundled datas land.  When running
    from source the icon lives in build/icon.ico relative to the repo root.
    """
    if getattr(sys, 'frozen', False):
        # Frozen: icon.ico was added to datas as ('.', '.') — it lands at
        # the root of the _MEIPASS extraction directory.
        return os.path.join(sys._MEIPASS, 'icon.ico')  # type: ignore[attr-defined]
    # Development: icon.ico lives in build/ next to src/
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(repo_root, 'build', 'icon.ico')

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


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyleSheet(_DARK_STYLESHEET)

    # Set application icon so the taskbar button and title bar show the
    # dice icon.  Must be set on QApplication (not just MainWindow) so the
    # taskbar button inherits it even when the window is not yet shown.
    icon_path = _resolve_icon_path()
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
