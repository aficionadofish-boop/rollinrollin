import pytest
from pathlib import Path
from src.workspace.setup import WorkspaceManager, WORKSPACE_SUBFOLDERS


def test_initialize_creates_all_subfolders(tmp_path):
    wm = WorkspaceManager(tmp_path)
    created = wm.initialize()
    assert set(created) == set(WORKSPACE_SUBFOLDERS)
    for name in WORKSPACE_SUBFOLDERS:
        assert (tmp_path / name).is_dir(), f"subfolder {name} not created"


def test_initialize_idempotent(tmp_path):
    wm = WorkspaceManager(tmp_path)
    wm.initialize()             # first call creates all
    created_second = wm.initialize()   # second call creates none
    assert created_second == [], "initialize() should return empty list when subfolders already exist"


def test_initialize_partial(tmp_path):
    # Pre-create 2 of 4 subfolders
    (tmp_path / "monsters").mkdir()
    (tmp_path / "lists").mkdir()
    wm = WorkspaceManager(tmp_path)
    created = wm.initialize()
    assert set(created) == {"encounters", "exports"}


def test_validate_existing_path(tmp_path):
    wm = WorkspaceManager(tmp_path)
    assert wm.validate() is True


def test_validate_missing_path(tmp_path):
    missing = tmp_path / "does_not_exist"
    wm = WorkspaceManager(missing)
    assert wm.validate() is False


def test_get_subfolder_valid(tmp_path):
    wm = WorkspaceManager(tmp_path)
    p = wm.get_subfolder("monsters")
    assert p == tmp_path / "monsters"


def test_get_subfolder_invalid(tmp_path):
    wm = WorkspaceManager(tmp_path)
    with pytest.raises(ValueError, match="Unknown workspace subfolder"):
        wm.get_subfolder("secrets")
