"""Shared pytest fixtures for the rollinrollin test suite.

The qapp fixture provides a session-scoped QApplication instance required by
Qt model/view tests (MonsterTableModel, MonsterFilterProxyModel, etc.).
It is session-scoped so that only one QApplication is created per pytest run.
"""
import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    """Return (or create) a QApplication instance for the test session."""
    app = QApplication.instance() or QApplication([])
    yield app
