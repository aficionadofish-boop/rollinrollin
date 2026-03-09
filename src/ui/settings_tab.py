"""SettingsTab — Session defaults configuration widget.

Provides a two-column grid layout with:
  - RNG section (seeded RNG toggle and seed spinbox)
  - Combat Defaults (advantage mode, crit settings)
  - Default AC / DC (target AC and save DC spinboxes)
  - Output mode (RAW/COMPARE toggle)
  - Theming (preset dropdown + custom color pickers)
  - Sandbox Font (curated monospace font dropdown)
  - Save button with dirty tracking

Emits settings_saved(AppSettings) when user clicks Save.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QCheckBox,
    QSpinBox,
    QComboBox,
    QMessageBox,
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont, QColor

from src.settings.models import AppSettings
from src.ui.toggle_bar import ToggleBar

# Curated monospace fonts for sandbox editor
_SANDBOX_FONTS = ["Consolas", "Cascadia Code", "Courier New", "Lucida Console", "Cascadia Mono"]


class SettingsTab(QWidget):
    """Settings tab widget with two-column grid layout.

    Public API
    ----------
    settings_saved : Signal(AppSettings)
        Emitted when user clicks Save with the collected AppSettings.
    apply_settings(settings)
        Set all widget values from an AppSettings instance; resets dirty flag.
    is_dirty() -> bool
        Returns True if user has made changes since last save/apply.
    current_settings() -> AppSettings
        Collect current widget values into an AppSettings.
    save()
        Collect settings, emit settings_saved, reset dirty flag.
    discard()
        Revert to last-saved settings.
    """

    settings_saved = Signal(object)
    flush_requested = Signal(str)
    clear_all_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dirty: bool = False
        self._last_saved: AppSettings = AppSettings()

        # Theme state — mirrors what is currently reflected in the UI
        self._current_theme_name: str = "dark"
        self._text_color: str = ""    # empty = use preset default
        self._bg_color: str = ""
        self._accent_color: str = ""

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(8)

        # Header label
        header = QLabel("Session Defaults")
        header_font = QFont(header.font())
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        outer.addWidget(header)

        # Two-column grid
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(8)

        # Row 1, col 0: RNG group
        grid.addWidget(self._build_rng_group(), 0, 0)

        # Row 1, col 1: Combat Defaults group
        grid.addWidget(self._build_combat_defaults_group(), 0, 1)

        # Row 2, col 0: Default AC / DC group
        grid.addWidget(self._build_ac_dc_group(), 1, 0)

        # Row 2, col 1: Output group
        grid.addWidget(self._build_output_group(), 1, 1)

        outer.addWidget(grid_widget)

        # Theming group — below the grid
        outer.addWidget(self._build_theming_group())

        # Data Management flush section
        outer.addWidget(self._build_data_flush_group())

        # Save button — spans bottom row
        self._save_btn = QPushButton("Save Settings")
        self._save_btn.setEnabled(False)
        self._save_btn.setStyleSheet(
            "QPushButton:enabled { background-color: #4DA6FF; color: #000000; font-weight: bold; }"
        )
        self._save_btn.clicked.connect(self._on_save_clicked)
        outer.addWidget(self._save_btn)

        # Push content to the top
        outer.addStretch()

    def _build_rng_group(self) -> QGroupBox:
        group = QGroupBox("RNG")
        layout = QVBoxLayout(group)

        # Enable seeded RNG checkbox
        self._seed_enable_check = QCheckBox("Enable Seeded RNG")
        layout.addWidget(self._seed_enable_check)

        # Seed value spinbox
        seed_row = QHBoxLayout()
        seed_label = QLabel("Seed Value:")
        self._seed_spin = QSpinBox()
        self._seed_spin.setRange(0, 0x7FFFFFFF)
        self._seed_spin.setValue(0)
        self._seed_spin.setEnabled(False)  # disabled until seeded RNG is checked
        seed_row.addWidget(seed_label)
        seed_row.addWidget(self._seed_spin)
        layout.addLayout(seed_row)

        layout.addStretch()

        # Wire signals
        self._seed_enable_check.toggled.connect(self._seed_spin.setEnabled)
        self._seed_enable_check.toggled.connect(self._mark_dirty)
        self._seed_spin.valueChanged.connect(self._mark_dirty)

        return group

    def _build_combat_defaults_group(self) -> QGroupBox:
        group = QGroupBox("Combat Defaults")
        layout = QVBoxLayout(group)

        # Advantage mode toggle
        adv_row = QHBoxLayout()
        adv_label = QLabel("Advantage:")
        self._adv_bar = ToggleBar(
            ["Normal", "Advantage", "Disadvantage"], default="Normal"
        )
        self._adv_bar.value_changed.connect(self._mark_dirty)
        adv_row.addWidget(adv_label)
        adv_row.addWidget(self._adv_bar)
        layout.addLayout(adv_row)

        # Crit enabled checkbox
        self._crit_check = QCheckBox("Crit Enabled")
        self._crit_check.setChecked(True)
        self._crit_check.toggled.connect(self._mark_dirty)
        layout.addWidget(self._crit_check)

        # Crit range spinbox
        crit_range_row = QHBoxLayout()
        crit_range_label = QLabel("Crit Range:")
        self._crit_range_spin = QSpinBox()
        self._crit_range_spin.setRange(18, 20)
        self._crit_range_spin.setValue(20)
        self._crit_range_spin.valueChanged.connect(self._mark_dirty)
        crit_range_row.addWidget(crit_range_label)
        crit_range_row.addWidget(self._crit_range_spin)
        layout.addLayout(crit_range_row)

        # Nat-1 always miss
        self._nat1_check = QCheckBox("Nat-1 Always Miss")
        self._nat1_check.setChecked(True)
        self._nat1_check.toggled.connect(self._mark_dirty)
        layout.addWidget(self._nat1_check)

        # Nat-20 always hit
        self._nat20_check = QCheckBox("Nat-20 Always Hit")
        self._nat20_check.setChecked(True)
        self._nat20_check.toggled.connect(self._mark_dirty)
        layout.addWidget(self._nat20_check)

        # Combat Tracker "Send to Saves" behavior
        self._ct_override_cb = QCheckBox("Combat Tracker 'Send to Saves' overrides sidebar selection")
        self._ct_override_cb.setChecked(True)
        self._ct_override_cb.setToolTip(
            "When checked, CT selection replaces sidebar checkboxes. "
            "When unchecked, sidebar is authoritative."
        )
        self._ct_override_cb.stateChanged.connect(self._mark_dirty)
        layout.addWidget(self._ct_override_cb)

        return group

    def _build_ac_dc_group(self) -> QGroupBox:
        group = QGroupBox("Default AC / DC")
        layout = QVBoxLayout(group)

        # Target AC
        ac_row = QHBoxLayout()
        ac_label = QLabel("Target AC:")
        self._target_ac_spin = QSpinBox()
        self._target_ac_spin.setRange(1, 30)
        self._target_ac_spin.setValue(15)
        self._target_ac_spin.valueChanged.connect(self._mark_dirty)
        ac_row.addWidget(ac_label)
        ac_row.addWidget(self._target_ac_spin)
        layout.addLayout(ac_row)

        # Save DC
        dc_row = QHBoxLayout()
        dc_label = QLabel("Save DC:")
        self._save_dc_spin = QSpinBox()
        self._save_dc_spin.setRange(1, 30)
        self._save_dc_spin.setValue(13)
        self._save_dc_spin.valueChanged.connect(self._mark_dirty)
        dc_row.addWidget(dc_label)
        dc_row.addWidget(self._save_dc_spin)
        layout.addLayout(dc_row)

        layout.addStretch()

        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Output")
        layout = QVBoxLayout(group)

        mode_row = QHBoxLayout()
        mode_label = QLabel("Mode:")
        self._mode_bar = ToggleBar(["RAW", "COMPARE"], default="RAW")
        self._mode_bar.value_changed.connect(self._mark_dirty)
        mode_row.addWidget(mode_label)
        mode_row.addWidget(self._mode_bar)
        layout.addLayout(mode_row)

        layout.addStretch()

        return group

    def _build_theming_group(self) -> QGroupBox:
        """Build the Theming group: preset dropdown, color pickers, sandbox font."""
        group = QGroupBox("Theming")
        layout = QVBoxLayout(group)

        # --- Theme preset dropdown ---
        preset_row = QHBoxLayout()
        preset_label = QLabel("Theme Preset:")
        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Dark", "dark")
        self._theme_combo.addItem("Default (Light)", "default")
        self._theme_combo.addItem("High Contrast", "high_contrast")
        preset_row.addWidget(preset_label)
        preset_row.addWidget(self._theme_combo)
        preset_row.addStretch()
        layout.addLayout(preset_row)

        # --- Custom color picker row ---
        color_row = QHBoxLayout()

        self._text_color_btn = QPushButton("Text Color")
        self._text_color_btn.setToolTip("Override the preset text color")
        self._text_color_btn.clicked.connect(self._pick_text_color)
        color_row.addWidget(self._text_color_btn)

        self._bg_color_btn = QPushButton("Background Color")
        self._bg_color_btn.setToolTip("Override the preset background color")
        self._bg_color_btn.clicked.connect(self._pick_bg_color)
        color_row.addWidget(self._bg_color_btn)

        self._accent_color_btn = QPushButton("Accent Color")
        self._accent_color_btn.setToolTip("Override the preset accent color")
        self._accent_color_btn.clicked.connect(self._pick_accent_color)
        color_row.addWidget(self._accent_color_btn)

        reset_btn = QPushButton("Reset to Preset")
        reset_btn.setToolTip("Clear all custom colors and reapply the current preset")
        reset_btn.clicked.connect(self._reset_to_preset)
        color_row.addWidget(reset_btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        # --- Sandbox font dropdown ---
        font_row = QHBoxLayout()
        font_label = QLabel("Sandbox Font:")
        self._font_combo = QComboBox()
        self._populate_font_combo()
        font_row.addWidget(font_label)
        font_row.addWidget(self._font_combo)
        font_row.addStretch()
        layout.addLayout(font_row)

        # --- UI Scale dropdown ---
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("UI Scale:"))
        self._scale_combo = QComboBox()
        for pct in (75, 100, 125, 150):
            self._scale_combo.addItem(f"{pct}%", pct)
        self._scale_combo.setCurrentIndex(1)  # default 100%
        self._scale_combo.setToolTip("Scale overall UI size")
        self._scale_combo.currentIndexChanged.connect(self._mark_dirty)
        scale_row.addWidget(self._scale_combo)
        scale_row.addStretch()
        layout.addLayout(scale_row)

        # Wire signals — connect AFTER widgets are created
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        self._font_combo.currentTextChanged.connect(self._mark_dirty)

        # Initialize color button previews
        self._update_color_button_previews()

        return group

    def _populate_font_combo(self) -> None:
        """Add only installed fonts from the curated list; fallback to Courier New."""
        from PySide6.QtGui import QFontDatabase
        available = set(QFontDatabase.families())
        for font in _SANDBOX_FONTS:
            if font in available:
                self._font_combo.addItem(font)
        if self._font_combo.count() == 0:
            self._font_combo.addItem("Courier New")  # universal fallback

    def _build_data_flush_group(self) -> QGroupBox:
        group = QGroupBox("Data Management")
        layout = QVBoxLayout(group)

        self._flush_labels: dict[str, QLabel] = {}
        self._flush_btns: dict[str, QPushButton] = {}

        _CATEGORIES = [
            ("loaded_monsters", "Loaded Monsters"),
            ("encounters", "Encounters"),
            ("modified_monsters", "Modified Monsters"),
            ("macros", "Macros"),
        ]

        for category_key, display_name in _CATEGORIES:
            row = QHBoxLayout()
            label = QLabel(f"{display_name}: -- entries")
            btn = QPushButton(f"Flush {display_name}")
            self._flush_labels[category_key] = label
            self._flush_btns[category_key] = btn
            # Use default args to capture loop variables by value
            btn.clicked.connect(
                lambda checked=False, cat=category_key, dn=display_name: self._on_flush(cat, dn)
            )
            row.addWidget(label)
            row.addWidget(btn)
            layout.addLayout(row)

        clear_all_btn = QPushButton("Clear All Data")
        clear_all_btn.clicked.connect(self._on_clear_all)
        layout.addWidget(clear_all_btn)

        return group

    def _on_flush(self, category: str, display_name: str) -> None:
        """Show confirmation dialog and emit flush_requested if confirmed."""
        reply = QMessageBox.question(
            self,
            "Flush Data",
            f"Flush all {display_name} data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.flush_requested.emit(category)

    def _on_clear_all(self) -> None:
        """Show confirmation dialog and emit clear_all_requested if confirmed."""
        reply = QMessageBox.question(
            self,
            "Clear All Data",
            "Clear ALL persistent data? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_all_requested.emit()

    # ------------------------------------------------------------------
    # Theming slot handlers
    # ------------------------------------------------------------------

    def _on_theme_changed(self, index: int) -> None:
        """Apply theme immediately on dropdown change (user decision: no Apply button)."""
        theme_names = ["dark", "default", "high_contrast"]
        if index < 0 or index >= len(theme_names):
            return
        self._current_theme_name = theme_names[index]
        # Clear custom colors when switching presets (clean slate)
        self._text_color = ""
        self._bg_color = ""
        self._accent_color = ""
        self._update_color_button_previews()
        self._apply_theme_live()
        self._mark_dirty()

    def _pick_text_color(self) -> None:
        """Open QColorDialog for text color; apply live on selection."""
        from PySide6.QtWidgets import QColorDialog
        current = self._text_color or self._get_preset_default("text")
        color = QColorDialog.getColor(QColor(current), self, "Text Color")
        if color.isValid():
            self._text_color = color.name()
            self._update_color_button_previews()
            self._apply_theme_live()
            self._mark_dirty()

    def _pick_bg_color(self) -> None:
        """Open QColorDialog for background color; apply live on selection."""
        from PySide6.QtWidgets import QColorDialog
        current = self._bg_color or self._get_preset_default("bg")
        color = QColorDialog.getColor(QColor(current), self, "Background Color")
        if color.isValid():
            self._bg_color = color.name()
            self._update_color_button_previews()
            self._apply_theme_live()
            self._mark_dirty()

    def _pick_accent_color(self) -> None:
        """Open QColorDialog for accent color; apply live on selection."""
        from PySide6.QtWidgets import QColorDialog
        current = self._accent_color or self._get_preset_default("accent")
        color = QColorDialog.getColor(QColor(current), self, "Accent Color")
        if color.isValid():
            self._accent_color = color.name()
            self._update_color_button_previews()
            self._apply_theme_live()
            self._mark_dirty()

    def _reset_to_preset(self) -> None:
        """Clear all custom color overrides and reapply the current preset."""
        self._text_color = ""
        self._bg_color = ""
        self._accent_color = ""
        self._update_color_button_previews()
        self._apply_theme_live()
        self._mark_dirty()

    def _apply_theme_live(self) -> None:
        """Apply the current theme selection immediately without saving."""
        from src.ui.theme_service import ThemeService
        ts = ThemeService()
        # Build a temporary AppSettings with current UI values
        temp = AppSettings(
            theme_name=self._current_theme_name,
            text_color=self._text_color,
            bg_color=self._bg_color,
            accent_color=self._accent_color,
        )
        ts.apply(temp)

    def _get_preset_default(self, channel: str) -> str:
        """Get the default color for a channel from the current preset."""
        from src.ui.theme_service import ThemeService
        ts = ThemeService()
        defaults = ts._get_preset_defaults(self._current_theme_name)
        return defaults.get(channel, "#888888")

    def _update_color_button_previews(self) -> None:
        """Update color picker button backgrounds to show current color state."""
        # Show the effective color (custom if set, else preset default)
        text_color = self._text_color or self._get_preset_default("text")
        bg_color = self._bg_color or self._get_preset_default("bg")
        accent_color = self._accent_color or self._get_preset_default("accent")

        # Use contrasting text colors for readability on the preview swatch
        def _contrast(hex_color: str) -> str:
            """Return black or white depending on luminance of hex_color."""
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#FFFFFF"

        self._text_color_btn.setStyleSheet(
            f"background-color: {text_color}; color: {_contrast(text_color)}; "
            f"border: 1px solid #888888;"
        )
        self._bg_color_btn.setStyleSheet(
            f"background-color: {bg_color}; color: {_contrast(bg_color)}; "
            f"border: 1px solid #888888;"
        )
        self._accent_color_btn.setStyleSheet(
            f"background-color: {accent_color}; color: {_contrast(accent_color)}; "
            f"border: 1px solid #888888;"
        )

    # ------------------------------------------------------------------
    # Dirty tracking
    # ------------------------------------------------------------------

    def _mark_dirty(self, *args) -> None:
        """Mark settings as modified and enable the Save button."""
        self._dirty = True
        self._save_btn.setEnabled(True)

    # ------------------------------------------------------------------
    # Save button handler
    # ------------------------------------------------------------------

    def _on_save_clicked(self) -> None:
        """Collect settings, store as last-saved, emit signal, reset dirty."""
        settings = self.current_settings()
        self._last_saved = settings
        self.settings_saved.emit(settings)
        self._dirty = False
        self._save_btn.setEnabled(False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply_settings(self, settings: AppSettings) -> None:
        """Set all widget values from an AppSettings instance; resets dirty flag."""
        # Block signals to prevent _mark_dirty from firing during apply
        self.blockSignals(True)
        try:
            # RNG
            self._seed_enable_check.setChecked(settings.seeded_rng_enabled)
            if settings.seed_value is not None:
                self._seed_spin.setValue(settings.seed_value)
            else:
                self._seed_spin.setValue(0)
            self._seed_spin.setEnabled(settings.seeded_rng_enabled)

            # Combat defaults
            adv_label = settings.default_advantage_mode.capitalize()
            # "normal" -> "Normal", "advantage" -> "Advantage", "disadvantage" -> "Disadvantage"
            self._adv_bar.set_value(adv_label)
            self._crit_check.setChecked(settings.default_crit_enabled)
            self._crit_range_spin.setValue(settings.default_crit_range)
            self._nat1_check.setChecked(settings.default_nat1_always_miss)
            self._nat20_check.setChecked(settings.default_nat20_always_hit)

            # AC / DC
            self._target_ac_spin.setValue(settings.default_target_ac)
            self._save_dc_spin.setValue(settings.default_save_dc)

            # Output mode
            mode_label = "RAW" if settings.default_mode == "raw" else "COMPARE"
            self._mode_bar.set_value(mode_label)

            # Combat Tracker "Send to Saves" override
            self._ct_override_cb.setChecked(settings.ct_send_overrides_sidebar)

            # Theme — block combo signals to prevent _on_theme_changed firing
            self._theme_combo.blockSignals(True)
            try:
                theme_map = {"dark": 0, "default": 1, "high_contrast": 2}
                idx = theme_map.get(settings.theme_name, 0)
                self._theme_combo.setCurrentIndex(idx)
                self._current_theme_name = settings.theme_name
            finally:
                self._theme_combo.blockSignals(False)

            # Custom colors
            self._text_color = settings.text_color
            self._bg_color = settings.bg_color
            self._accent_color = settings.accent_color

            # Sandbox font
            font_idx = self._font_combo.findText(settings.sandbox_font)
            if font_idx >= 0:
                self._font_combo.setCurrentIndex(font_idx)
            # else: leave at first available font

            # UI scale
            scale_val = getattr(settings, "ui_scale", 100)
            idx = self._scale_combo.findData(scale_val)
            if idx >= 0:
                self._scale_combo.setCurrentIndex(idx)
        finally:
            self.blockSignals(False)

        # Update color previews after unblocking
        self._update_color_button_previews()

        # Reset dirty state after applying
        self._dirty = False
        self._save_btn.setEnabled(False)
        self._last_saved = settings

    def is_dirty(self) -> bool:
        """Return True if user has made unsaved changes."""
        return self._dirty

    def current_settings(self) -> AppSettings:
        """Collect current widget values into an AppSettings instance."""
        adv_value = self._adv_bar.value().lower()  # "Normal" -> "normal"
        seed_val = self._seed_spin.value() if self._seed_enable_check.isChecked() else None
        mode_value = "raw" if self._mode_bar.value() == "RAW" else "compare"

        return AppSettings(
            seeded_rng_enabled=self._seed_enable_check.isChecked(),
            seed_value=seed_val,
            default_crit_enabled=self._crit_check.isChecked(),
            default_crit_range=self._crit_range_spin.value(),
            default_nat1_always_miss=self._nat1_check.isChecked(),
            default_nat20_always_hit=self._nat20_check.isChecked(),
            default_advantage_mode=adv_value,
            default_mode=mode_value,
            default_target_ac=self._target_ac_spin.value(),
            default_save_dc=self._save_dc_spin.value(),
            ct_send_overrides_sidebar=self._ct_override_cb.isChecked(),
            # Theme fields
            theme_name=self._current_theme_name,
            text_color=self._text_color,
            bg_color=self._bg_color,
            accent_color=self._accent_color,
            # Sandbox font
            sandbox_font=self._font_combo.currentText(),
            # UI scale
            ui_scale=self._scale_combo.currentData(),
        )

    def save(self) -> None:
        """Collect settings, emit settings_saved, reset dirty flag."""
        self._on_save_clicked()

    def discard(self) -> None:
        """Revert all widgets to the last-saved settings."""
        self.apply_settings(self._last_saved)

    def refresh_counts(self, counts: dict[str, int]) -> None:
        """Update flush label texts with current entry counts.

        Parameters
        ----------
        counts:
            Mapping of category key -> entry count.
        """
        for category_key, label in self._flush_labels.items():
            count = counts.get(category_key, 0)
            display_name = category_key.replace("_", " ").title()
            noun = "entry" if count == 1 else "entries"
            label.setText(f"{display_name}: {count} {noun}")
