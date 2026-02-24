"""Generate a dice-themed .ico file for RollinRollin.

Run from repo root: python build/make_icon.py
Output: build/icon.ico (multi-resolution: 16, 32, 48, 64, 128, 256)
"""
import os
from PIL import Image, ImageDraw


def make_dice_icon(size: int) -> Image.Image:
    """Draw a d6 face with 6 pips at the given pixel size."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    margin = size // 10
    radius = size // 8
    outline_width = max(1, size // 30)

    # Rounded rectangle body — dark blue fill with lighter outline
    d.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=radius,
        fill=(60, 80, 160),
        outline=(200, 210, 255),
        width=outline_width,
    )

    # Six pip circles in standard d6 "six" layout (two columns of three)
    pip_r = max(1, size // 16)
    pip_color = (220, 230, 255)
    cx, cy = size // 2, size // 2
    step = size // 4

    pip_positions = [
        (cx - step, cy - step),  # top-left
        (cx + step, cy - step),  # top-right
        (cx - step, cy),         # mid-left
        (cx + step, cy),         # mid-right
        (cx - step, cy + step),  # bottom-left
        (cx + step, cy + step),  # bottom-right
    ]
    for px, py in pip_positions:
        d.ellipse([px - pip_r, py - pip_r, px + pip_r, py + pip_r], fill=pip_color)

    return img


def main() -> None:
    sizes = [16, 32, 48, 64, 128, 256]
    output_path = 'build/icon.ico'

    # Generate the master image at the largest size and let Pillow resize it to
    # each requested size when saving the multi-resolution ICO.
    master = make_dice_icon(256)
    master.save(
        output_path,
        format='ICO',
        sizes=[(s, s) for s in sizes],
    )

    size_bytes = os.path.getsize(output_path)
    print(f"icon.ico written to {output_path} ({size_bytes} bytes, resolutions: {sizes})")


if __name__ == '__main__':
    main()
