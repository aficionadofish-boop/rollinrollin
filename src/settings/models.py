from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AppSettings:
    # RNG
    seeded_rng_enabled: bool = False
    seed_value: Optional[int] = None

    # Default combat toggles
    default_crit_enabled: bool = True
    default_crit_range: int = 20
    default_nat1_always_miss: bool = True
    default_nat20_always_hit: bool = True
    default_advantage_mode: str = "normal"   # "normal", "advantage", or "disadvantage"
    # Default output mode — "raw" or "compare"
    default_mode: str = "raw"

    # Default AC / DC
    default_target_ac: int = 15
    default_save_dc: int = 13

    # Sidebar
    sidebar_width: int = 350

    # Combat Tracker "Send to Saves" behavior
    ct_send_overrides_sidebar: bool = True

    # Theme
    theme_name: str = "dark"        # active preset: "dark", "default", "high_contrast"
    text_color: str = ""            # custom text color hex (empty = use preset)
    bg_color: str = ""              # custom background color hex (empty = use preset)
    accent_color: str = ""          # custom accent color hex (empty = use preset)
    sandbox_font: str = "Consolas"  # macro sandbox font family name

    # UI scaling
    ui_scale: int = 100              # percentage (75, 100, 125, 150) for overall UI size
