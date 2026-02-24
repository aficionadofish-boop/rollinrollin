# build/RollinRollin.spec
# PyInstaller spec file for RollinRollin — single-file windowed exe.
# Source: pyinstaller.org/en/stable/spec-files.html
# Build with: pyinstaller build/RollinRollin.spec  (from repo root)

import os
block_cipher = None

# SPECPATH is the directory containing this spec file (i.e. build/).
# Repo root is one level up from the spec file.
REPO_ROOT = os.path.dirname(SPECPATH)

a = Analysis(
    [os.path.join(REPO_ROOT, 'src', 'main.py')],
    pathex=[REPO_ROOT],     # repo root on PYTHONPATH so "src.*" imports resolve
    binaries=[],
    datas=[
        (os.path.join(REPO_ROOT, 'build', 'icon.ico'), '.'),  # bundle icon at root of frozen app
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.Qt3DCore',
        'PySide6.Qt3DRender',
        'PySide6.Qt3DInput',
        'PySide6.Qt3DLogic',
        'PySide6.Qt3DAnimation',
        'PySide6.Qt3DExtras',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtQuick3D',
        'PySide6.QtQuickControls2',
        'PySide6.QtCharts',
        'PySide6.QtDataVisualization',
        'PySide6.QtVirtualKeyboard',
        'PySide6.QtBluetooth',
        'PySide6.QtNfc',
        'PySide6.QtPositioning',
        'PySide6.QtSensors',
        'PySide6.QtSerialPort',
        'PySide6.QtTest',
        'PySide6.QtLocation',
        'PySide6.QtPdf',
        'PySide6.QtPdfWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='RollinRollin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX disabled: known to break onefile bootloader; causes segfaults
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # windowed mode — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(REPO_ROOT, 'build', 'icon.ico'),
    version=os.path.join(REPO_ROOT, 'build', 'version.txt'),
)
