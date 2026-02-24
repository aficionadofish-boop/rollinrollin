@echo off
setlocal

echo === RollinRollin Build ===
echo.

echo [1/2] Running tests...
python -m pytest src/tests/ -q
if %ERRORLEVEL% neq 0 (
    echo FAILED: Tests failed. Aborting build.
    exit /b 1
)
echo Tests passed.
echo.

echo [2/2] Building executable...
pyinstaller build/RollinRollin.spec --noconfirm --distpath dist --workpath build/work
if %ERRORLEVEL% neq 0 (
    echo FAILED: PyInstaller failed.
    exit /b 1
)

echo.
echo Build complete: dist\RollinRollin.exe
endlocal
