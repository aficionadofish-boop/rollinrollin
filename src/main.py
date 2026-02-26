"""RollinRollin — application entry point."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.ui.app import MainWindow
from src.ui.theme_service import ThemeService
from src.settings.models import AppSettings


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


def main() -> None:
    app = QApplication(sys.argv)
    # Apply the default dark theme at startup before MainWindow loads persisted settings.
    # MainWindow._apply_settings() will re-apply with the correct saved theme once loaded.
    theme_service = ThemeService()
    app.setStyleSheet(theme_service.build_stylesheet(AppSettings()))

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
