"""SettingsTab — Session defaults configuration widget.

Provides a two-column grid layout with:
  - RNG section (seeded RNG toggle and seed spinbox)
  - Combat Defaults (advantage mode, GWM/SS, crit settings)
  - Default AC / DC (target AC and save DC spinboxes)
  - Output mode (RAW/COMPARE toggle)
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
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont

from src.settings.models import AppSettings
from src.ui.toggle_bar import ToggleBar


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

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._dirty: bool = False
        self._last_saved: AppSettings = AppSettings()
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

        # GWM / Sharpshooter checkbox
        self._gwm_check = QCheckBox("GWM / Sharpshooter")
        self._gwm_check.toggled.connect(self._mark_dirty)
        layout.addWidget(self._gwm_check)

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
            self._gwm_check.setChecked(settings.default_gwm_sharpshooter)
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
        finally:
            self.blockSignals(False)

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
            default_gwm_sharpshooter=self._gwm_check.isChecked(),
            default_mode=mode_value,
            default_target_ac=self._target_ac_spin.value(),
            default_save_dc=self._save_dc_spin.value(),
        )

    def save(self) -> None:
        """Collect settings, emit settings_saved, reset dirty flag."""
        self._on_save_clicked()

    def discard(self) -> None:
        """Revert all widgets to the last-saved settings."""
        self.apply_settings(self._last_saved)
