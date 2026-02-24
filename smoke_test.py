#!/usr/bin/env python3
"""Smoke test: launch RollinRollin.exe and verify it stays alive.

Run from repo root after a successful build:
    python smoke_test.py

Prerequisites: Run build.bat first to produce dist/RollinRollin.exe.
"""
import subprocess
import time
import sys
from pathlib import Path

EXE = Path(__file__).parent / 'dist' / 'RollinRollin.exe'
WAIT_SECONDS = 8


def main() -> None:
    if not EXE.exists():
        print(f"FAIL: {EXE} not found. Run build.bat first.")
        sys.exit(1)

    print(f"Launching {EXE.name}...")
    proc = subprocess.Popen(
        [str(EXE)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(WAIT_SECONDS)

    poll = proc.poll()
    if poll is not None:
        print(f"FAIL: Process exited after {WAIT_SECONDS}s with code {poll}")
        sys.exit(1)

    proc.terminate()
    proc.wait(timeout=5)
    print(f"PASS: RollinRollin.exe launched and ran for {WAIT_SECONDS}s without crashing.")


if __name__ == '__main__':
    main()
