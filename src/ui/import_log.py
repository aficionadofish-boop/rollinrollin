"""ImportLogPanel — scrollable read-only log panel for import results.

Displays per-file import summaries with counts (imported, incomplete, failures)
and individual failure details.  Not a modal — embedded in the library tab layout.
"""
from __future__ import annotations

from PySide6.QtWidgets import QTextEdit

from src.parser.models import ParseFailure


class ImportLogPanel(QTextEdit):
    """Read-only scrollable log panel showing import results per file."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Import results will appear here...")
        self.setMinimumHeight(120)

    def log(self, message: str) -> None:
        """Append a single message line to the log."""
        self.append(message)
        self.ensureCursorVisible()

    def log_result(
        self,
        filename: str,
        success: int,
        incomplete: int,
        failures: list,
    ) -> None:
        """Format one file's import result into the log.

        Args:
            filename: Basename or full path of the source Markdown file.
            success: Total monsters parsed (including incomplete ones).
            incomplete: Count of monsters with incomplete=True.
            failures: list[ParseFailure] — monsters that could not be stored.
        """
        self.append(f"--- {filename} ---")
        self.append(
            f"  Imported: {success}  Incomplete: {incomplete}  Failures: {len(failures)}"
        )
        for f in failures:
            name_part = f" [{f.monster_name}]" if f.monster_name else ""
            self.append(f"  FAIL{name_part}: {f.reason}")
        self.ensureCursorVisible()

    def clear_log(self) -> None:
        """Clear all log content."""
        self.clear()
