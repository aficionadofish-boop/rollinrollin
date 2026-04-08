"""StorytellerTab — complete self-contained QWidget for the Storyteller System tab.

Supports World of Darkness Classic and Aberrant 1e dice systems.
All dice math delegates to StorytellerEngine. Gothic accent styling is scoped
to specific child widgets only — no QApplication.setStyleSheet() calls.
"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.persistence.service import PersistenceService
from src.storyteller.engine import StorytellerEngine
from src.storyteller.models import StorytellerPreset
from src.ui.toggle_bar import ToggleBar

# ---------------------------------------------------------------------------
# Gothic accent color constants (scoped to this tab's widgets only)
# ---------------------------------------------------------------------------
_GOTHIC_ACCENT = "#6B2D6B"
_GOTHIC_ACCENT_HOVER = "#7D3A7D"
_GOTHIC_BORDER = "#9B4D9B"
_GOTHIC_TEXT = "#E8D5E8"


class StorytellerTab(QWidget):
    """Complete Storyteller System dice roller tab.

    Receives only a PersistenceService at construction time.
    All dice math delegates to StorytellerEngine (Plan 01).
    """

    def __init__(self, persistence: PersistenceService, parent=None):
        super().__init__(parent)
        self._persistence = persistence
        self._engine = StorytellerEngine(random.Random())
        self._presets: list[StorytellerPreset] = []
        self._extended_total: int = 0  # running total for extended rolls
        self._load_presets()
        self._build_layout()

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_right_panel())
        splitter.setSizes([300, 600])

        root_layout.addWidget(splitter)

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Character name row ---
        char_row = QHBoxLayout()
        char_row.addWidget(QLabel("Character:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Character name\u2026")
        char_row.addWidget(self._name_edit)
        layout.addLayout(char_row)

        # --- System toggle ---
        self._system_toggle = ToggleBar(["WoD Classic", "Aberrant 1e"])
        self._system_toggle.value_changed.connect(self._on_system_changed)
        layout.addWidget(self._system_toggle)

        # --- WoD Classic panel ---
        self._wod_panel = QGroupBox("WoD Classic")
        wod_layout = QVBoxLayout(self._wod_panel)
        wod_layout.setSpacing(4)

        wod_pool_row = QHBoxLayout()
        wod_pool_row.addWidget(QLabel("Pool:"))
        self._wod_pool_spin = QSpinBox()
        self._wod_pool_spin.setMinimum(1)
        self._wod_pool_spin.setMaximum(30)
        self._wod_pool_spin.setValue(5)
        wod_pool_row.addWidget(self._wod_pool_spin)
        wod_layout.addLayout(wod_pool_row)

        wod_diff_row = QHBoxLayout()
        wod_diff_row.addWidget(QLabel("Difficulty:"))
        self._wod_diff_spin = QSpinBox()
        self._wod_diff_spin.setMinimum(2)
        self._wod_diff_spin.setMaximum(10)
        self._wod_diff_spin.setValue(6)
        wod_diff_row.addWidget(self._wod_diff_spin)
        wod_layout.addLayout(wod_diff_row)

        wod_reroll_row = QHBoxLayout()
        wod_reroll_row.addWidget(QLabel("Re-roll:"))
        self._wod_reroll_combo = QComboBox()
        self._wod_reroll_combo.addItems(["None", "8-again", "9-again"])
        wod_reroll_row.addWidget(self._wod_reroll_combo)
        wod_layout.addLayout(wod_reroll_row)

        self._wod_rote_check = QCheckBox("Rote Quality")
        wod_layout.addWidget(self._wod_rote_check)

        layout.addWidget(self._wod_panel)

        # --- Aberrant 1e panel ---
        self._aberrant_panel = QGroupBox("Aberrant 1e")
        ab_layout = QVBoxLayout(self._aberrant_panel)
        ab_layout.setSpacing(4)

        ab_pool_row = QHBoxLayout()
        ab_pool_row.addWidget(QLabel("Pool:"))
        self._ab_pool_spin = QSpinBox()
        self._ab_pool_spin.setMinimum(0)
        self._ab_pool_spin.setMaximum(30)
        self._ab_pool_spin.setValue(5)
        ab_pool_row.addWidget(self._ab_pool_spin)
        ab_layout.addLayout(ab_pool_row)

        ab_mega_row = QHBoxLayout()
        ab_mega_row.addWidget(QLabel("Mega Dice:"))
        self._ab_mega_spin = QSpinBox()
        self._ab_mega_spin.setMinimum(0)
        self._ab_mega_spin.setMaximum(20)
        self._ab_mega_spin.setValue(0)
        ab_mega_row.addWidget(self._ab_mega_spin)
        ab_layout.addLayout(ab_mega_row)

        ab_auto_row = QHBoxLayout()
        ab_auto_row.addWidget(QLabel("Auto Successes:"))
        self._ab_auto_spin = QSpinBox()
        self._ab_auto_spin.setMinimum(0)
        self._ab_auto_spin.setMaximum(20)
        self._ab_auto_spin.setValue(0)
        ab_auto_row.addWidget(self._ab_auto_spin)
        ab_layout.addLayout(ab_auto_row)

        ab_req_row = QHBoxLayout()
        ab_req_row.addWidget(QLabel("Successes Required:"))
        self._ab_req_spin = QSpinBox()
        self._ab_req_spin.setMinimum(1)
        self._ab_req_spin.setMaximum(30)
        self._ab_req_spin.setValue(1)
        ab_req_row.addWidget(self._ab_req_spin)
        ab_layout.addLayout(ab_req_row)

        ab_info = QLabel("Target number is always 7 (fixed)")
        ab_info.setEnabled(False)
        ab_layout.addWidget(ab_info)

        layout.addWidget(self._aberrant_panel)
        self._aberrant_panel.setVisible(False)

        # --- Roll button ---
        self._roll_btn = QPushButton("Roll")
        self._roll_btn.setStyleSheet(
            f"QPushButton {{ background-color: {_GOTHIC_ACCENT}; color: {_GOTHIC_TEXT}; "
            f"border: 1px solid {_GOTHIC_BORDER}; padding: 6px 16px; font-weight: bold; }} "
            f"QPushButton:hover {{ background-color: {_GOTHIC_ACCENT_HOVER}; }}"
        )
        self._roll_btn.clicked.connect(self._roll)
        layout.addWidget(self._roll_btn)

        # --- Extended roll row (WoD only) ---
        self._extended_row_widget = QWidget()
        ext_row = QHBoxLayout(self._extended_row_widget)
        ext_row.setContentsMargins(0, 0, 0, 0)
        self._extended_label = QLabel("Extended Total: 0")
        ext_row.addWidget(self._extended_label)
        ext_reset_btn = QPushButton("Reset")
        ext_reset_btn.clicked.connect(self._reset_extended)
        ext_row.addWidget(ext_reset_btn)
        layout.addWidget(self._extended_row_widget)

        # --- Preset row ---
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Presets:"))
        self._preset_combo = QComboBox()
        self._refresh_preset_combo()
        preset_row.addWidget(self._preset_combo)
        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self._on_load_preset)
        preset_row.addWidget(load_btn)
        layout.addLayout(preset_row)

        preset_save_row = QHBoxLayout()
        self._preset_name_edit = QLineEdit()
        self._preset_name_edit.setPlaceholderText("Preset name\u2026")
        preset_save_row.addWidget(self._preset_name_edit)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_preset)
        preset_save_row.addWidget(save_btn)
        layout.addLayout(preset_save_row)

        layout.addStretch()

        return panel

    def _build_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # --- Result display ---
        self._result_group = QGroupBox("Result")
        self._result_group.setStyleSheet(
            "QGroupBox { border: 1px solid #6B2D6B; border-radius: 4px; "
            "margin-top: 8px; } "
            "QGroupBox::title { color: #C090C0; }"
        )
        result_group_layout = QVBoxLayout(self._result_group)
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMinimumHeight(120)
        result_group_layout.addWidget(self._result_text)
        layout.addWidget(self._result_group)

        # --- Session log ---
        layout.addWidget(QLabel("Session Log"))
        self._log_text = QTextEdit()
        self._log_text.setReadOnly(True)
        layout.addWidget(self._log_text, stretch=1)

        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._log_text.clear)
        layout.addWidget(clear_btn)

        return panel

    # ------------------------------------------------------------------
    # System switching
    # ------------------------------------------------------------------

    def _on_system_changed(self, system_label: str) -> None:
        is_wod = system_label == "WoD Classic"
        self._wod_panel.setVisible(is_wod)
        self._extended_row_widget.setVisible(is_wod)
        self._aberrant_panel.setVisible(not is_wod)

    # ------------------------------------------------------------------
    # Roll logic
    # ------------------------------------------------------------------

    def _roll(self) -> None:
        character = self._name_edit.text().strip() or "Unknown"
        system = self._system_toggle.value()

        if system == "WoD Classic":
            self._roll_wod(character)
        else:
            self._roll_aberrant(character)

    def _roll_wod(self, character: str) -> None:
        pool = self._wod_pool_spin.value()
        difficulty = self._wod_diff_spin.value()
        reroll_idx = self._wod_reroll_combo.currentIndex()
        rote = self._wod_rote_check.isChecked()

        reroll_map = {0: None, 1: 8, 2: 9}
        reroll_threshold = reroll_map[reroll_idx]

        result = self._engine.roll_wod(
            pool=pool,
            difficulty=difficulty,
            reroll_threshold=reroll_threshold,
            rote_enabled=rote,
        )

        # --- Build header ---
        reroll_label = ""
        if reroll_threshold is not None:
            reroll_label = f" {reroll_threshold}-again"
        if rote:
            reroll_label += " rote"
        header = (
            f'<p style="margin:2px 0;">'
            f'<b>{character}</b> Pool {pool} diff {difficulty}{reroll_label}'
            f' \u2014 <b>{result.net_successes} net successes</b>'
            f'</p>'
        )

        # --- Build dice line ---
        # Separate original dice from re-roll batches by is_reroll flag
        original_dice = [d for d in result.dice if not d.is_reroll]
        reroll_dice = [d for d in result.dice if d.is_reroll]

        def _wod_die_span(d) -> str:
            if d.is_one and not d.is_success:
                color = "#CC3333"
            elif d.is_success and d.value == 10:
                color = "#00CC66"
            elif d.is_success:
                color = "#66BB66"
            elif d.is_reroll and not d.is_success and not d.is_one:
                color = "#AAAAFF"
            else:
                color = "#888888"
            return f'<span style="color:{color};">{d.value}</span>'

        orig_spans = " ".join(_wod_die_span(d) for d in original_dice)
        dice_html = orig_spans

        if reroll_dice:
            reroll_spans = " ".join(_wod_die_span(d) for d in reroll_dice)
            dice_html += (
                f' <span style="color:#888888;"> | re-rolled: </span>{reroll_spans}'
            )

        dice_line = f'<p style="margin:2px 0; font-family:monospace;">{dice_html}</p>'

        # --- Build verdict ---
        if result.is_botch:
            verdict_html = '<span style="color:#8B1A1A;font-weight:bold;">BOTCH</span>'
            verdict_str = verdict_html
        elif result.is_exceptional:
            verdict_html = (
                f'<span style="color:#D4AF37;font-weight:bold;">EXCEPTIONAL SUCCESS</span>'
                f' <span style="color:#CCCCCC;">({result.net_successes} successes)</span>'
            )
            verdict_str = verdict_html
        elif result.net_successes > 0:
            verdict_html = (
                f'<span style="color:#66BB66;">Success: {result.net_successes}</span>'
            )
            verdict_str = verdict_html
        else:
            verdict_html = '<span style="color:#888888;">Failure</span>'
            verdict_str = verdict_html

        verdict_line = f'<p style="margin:2px 0;">{verdict_html}</p>'

        # --- Update extended total ---
        self._extended_total += result.net_successes
        self._extended_label.setText(f"Extended Total: {self._extended_total}")

        # --- Insert into result display ---
        full_html = header + dice_line + verdict_line
        self._result_text.clear()
        self._insert_html(self._result_text, full_html)

        # --- Append to session log ---
        reroll_str = ""
        if reroll_threshold:
            reroll_str = f" {reroll_threshold}-again"
        if rote:
            reroll_str += " rote"
        config_str = f"WoD Pool {pool} diff {difficulty}{reroll_str}"
        self._append_log(character, config_str, verdict_str)

    def _roll_aberrant(self, character: str) -> None:
        pool = self._ab_pool_spin.value()
        mega_pool = self._ab_mega_spin.value()
        auto_sux = self._ab_auto_spin.value()
        required = self._ab_req_spin.value()

        result = self._engine.roll_aberrant(
            pool=pool,
            mega_pool=mega_pool,
            auto_successes=auto_sux,
            successes_required=required,
        )

        # --- Build header ---
        header = (
            f'<p style="margin:2px 0;">'
            f'<b>{character}</b> Pool {pool} + {mega_pool} mega + {auto_sux} auto'
            f' \u2014 <b>{result.total_successes} total successes</b> vs {required} req'
            f'</p>'
        )

        # --- Normal dice line ---
        def _normal_die_span(d) -> str:
            if d.is_one:
                color = "#CC3333"
            elif d.is_success:
                color = "#66BB66"
            else:
                color = "#888888"
            return f'<span style="color:{color};">{d.value}</span>'

        if result.normal_dice:
            normal_spans = " ".join(_normal_die_span(d) for d in result.normal_dice)
            normal_line = f'<p style="margin:2px 0; font-family:monospace;">{normal_spans}</p>'
        else:
            normal_line = ""

        # --- Mega dice line ---
        def _mega_die_span(md) -> str:
            if md.is_one:
                color = "#CC3333"
                label = str(md.value)
            elif md.sux_count == 3:
                color = "#FF88FF"
                label = f"10(3x)"
            elif md.sux_count == 2:
                color = "#8888FF"
                label = f"{md.value}(2x)"
            else:
                color = "#888888"
                label = str(md.value)
            return f'<span style="color:{color};">{label}</span>'

        if result.mega_dice:
            mega_spans = " ".join(_mega_die_span(md) for md in result.mega_dice)
            mega_line = (
                f'<p style="margin:2px 0; font-family:monospace;">'
                f'<span style="color:#AAAAAA;">Mega: </span>{mega_spans}</p>'
            )
        else:
            mega_line = ""

        # --- Auto successes line ---
        if result.auto_successes > 0:
            auto_line = (
                f'<p style="margin:2px 0;">'
                f'<span style="color:#B8A050;">+ {result.auto_successes} auto</span>'
                f'</p>'
            )
        else:
            auto_line = ""

        # --- Verdict ---
        if result.is_botch:
            verdict_html = '<span style="color:#8B1A1A;font-weight:bold;">BOTCH</span>'
        elif result.total_successes == 0:
            verdict_html = '<span style="color:#888888;">Failure</span>'
        else:
            tier = result.success_tier
            tier_map = {
                "1-4": "1-4 sux",
                "5-8": "5-8 sux",
                "9-12": "9-12 sux",
                "13-16": "13-16 sux",
            }
            tier_label = tier_map.get(tier, tier)
            verdict_html = (
                f'<span style="color:#66BB66;">Mega Tier: {tier_label}</span> '
                f'<span style="color:#CCCCCC;">({result.total_successes} successes)</span>'
            )

        verdict_line = f'<p style="margin:2px 0;">{verdict_html}</p>'

        # --- Insert into result display ---
        full_html = header + normal_line + mega_line + auto_line + verdict_line
        self._result_text.clear()
        self._insert_html(self._result_text, full_html)

        # --- Append to session log ---
        config_str = f"Aberrant Pool {pool}+{mega_pool}M+{auto_sux}A vs {required}"
        self._append_log(character, config_str, verdict_html)

    # ------------------------------------------------------------------
    # HTML insertion helpers
    # ------------------------------------------------------------------

    def _insert_html(self, text_edit: QTextEdit, html: str) -> None:
        """Insert HTML at end of text_edit using QTextCursor (never append())."""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertHtml(html)
        text_edit.setTextCursor(cursor)
        text_edit.verticalScrollBar().setValue(
            text_edit.verticalScrollBar().maximum()
        )

    def _append_log(self, character: str, config_str: str, verdict_str: str) -> None:
        """Append a roll summary line to the session log."""
        line = (
            f'<p style="margin:0;">'
            f'<span style="color:#AAAAAA;">[{character}]</span> '
            f'{config_str} <span style="color:#CCCCCC;">\u2192</span> {verdict_str}'
            f'</p>'
        )
        self._insert_html(self._log_text, line)

    # ------------------------------------------------------------------
    # Extended roll
    # ------------------------------------------------------------------

    def _reset_extended(self) -> None:
        self._extended_total = 0
        self._extended_label.setText("Extended Total: 0")

    # ------------------------------------------------------------------
    # Preset management
    # ------------------------------------------------------------------

    def _load_presets(self) -> None:
        raw = self._persistence.load_storyteller_presets()
        self._presets = [StorytellerPreset.from_dict(v) for v in raw.values()]
        # _refresh_preset_combo() is called after widgets are built

    def _refresh_preset_combo(self) -> None:
        if not hasattr(self, "_preset_combo"):
            return
        self._preset_combo.clear()
        self._preset_combo.addItem("")  # no selection as first item
        for preset in self._presets:
            self._preset_combo.addItem(preset.name)

    def _on_load_preset(self) -> None:
        name = self._preset_combo.currentText()
        if not name:
            return
        for preset in self._presets:
            if preset.name == name:
                self._restore_from_preset(preset)
                return

    def _restore_from_preset(self, preset: StorytellerPreset) -> None:
        """Restore all spinbox values from a StorytellerPreset."""
        # Switch system
        label = "Aberrant 1e" if preset.system == "aberrant" else "WoD Classic"
        self._system_toggle.set_value(label)

        # WoD fields
        self._wod_pool_spin.setValue(preset.pool)
        self._wod_diff_spin.setValue(preset.difficulty)

        # Map reroll_threshold back to combo index
        reroll_idx = {None: 0, 8: 1, 9: 2}.get(preset.reroll_threshold, 0)
        self._wod_reroll_combo.setCurrentIndex(reroll_idx)
        self._wod_rote_check.setChecked(preset.rote_enabled)

        # Aberrant fields
        self._ab_pool_spin.setValue(preset.pool)
        self._ab_mega_spin.setValue(preset.mega_pool)
        self._ab_auto_spin.setValue(preset.auto_successes)
        self._ab_req_spin.setValue(preset.successes_required)

    def _on_save_preset(self) -> None:
        name = self._preset_name_edit.text().strip()
        if not name:
            name = f"Preset {len(self._presets) + 1}"

        system = self.current_system()

        # Determine reroll threshold from combo index
        reroll_map = {0: None, 1: 8, 2: 9}
        reroll_threshold = reroll_map[self._wod_reroll_combo.currentIndex()]

        preset = StorytellerPreset(
            name=name,
            system=system,
            pool=self._wod_pool_spin.value() if system == "wod" else self._ab_pool_spin.value(),
            difficulty=self._wod_diff_spin.value(),
            reroll_threshold=reroll_threshold,
            rote_enabled=self._wod_rote_check.isChecked(),
            mega_pool=self._ab_mega_spin.value(),
            auto_successes=self._ab_auto_spin.value(),
            successes_required=self._ab_req_spin.value(),
        )

        # Replace existing with same name, or append
        for i, p in enumerate(self._presets):
            if p.name == name:
                self._presets[i] = preset
                break
        else:
            self._presets.append(preset)

        # Persist
        raw = {p.name: p.to_dict() for p in self._presets}
        self._persistence.save_storyteller_presets(raw)
        self._refresh_preset_combo()

    # ------------------------------------------------------------------
    # Public API (required by Plan 03)
    # ------------------------------------------------------------------

    def current_system(self) -> str:
        """Return 'wod' or 'aberrant'."""
        return "aberrant" if self._system_toggle.value() == "Aberrant 1e" else "wod"

    def current_config(self) -> dict:
        """Return all spinbox values for round-trip save/restore."""
        return {
            "wod_pool": self._wod_pool_spin.value(),
            "wod_difficulty": self._wod_diff_spin.value(),
            "wod_reroll": self._wod_reroll_combo.currentIndex(),
            "wod_rote": self._wod_rote_check.isChecked(),
            "ab_pool": self._ab_pool_spin.value(),
            "ab_mega": self._ab_mega_spin.value(),
            "ab_auto": self._ab_auto_spin.value(),
            "ab_required": self._ab_req_spin.value(),
            "character_name": self._name_edit.text(),
        }

    def restore_config(self, system: str, config: dict) -> None:
        """Restore toggle selection and all spinbox values from a saved config dict.

        ToggleBar.set_value(label) is the programmatic selection API — it also
        emits value_changed, which calls _on_system_changed() to show/hide panels.
        """
        label = "Aberrant 1e" if system == "aberrant" else "WoD Classic"
        self._system_toggle.set_value(label)
        # Restore spinboxes with .get() defaults so empty config is safe
        self._wod_pool_spin.setValue(config.get("wod_pool", 5))
        self._wod_diff_spin.setValue(config.get("wod_difficulty", 6))
        self._wod_reroll_combo.setCurrentIndex(config.get("wod_reroll", 0))
        self._wod_rote_check.setChecked(config.get("wod_rote", False))
        self._ab_pool_spin.setValue(config.get("ab_pool", 5))
        self._ab_mega_spin.setValue(config.get("ab_mega", 0))
        self._ab_auto_spin.setValue(config.get("ab_auto", 0))
        self._ab_req_spin.setValue(config.get("ab_required", 1))
        self._name_edit.setText(config.get("character_name", ""))
