from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


def _get_font(size: int, bold: bool = False) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    font_candidates = (
        ["arialbd.ttf", "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"]
        if bold
        else ["arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]
    )
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def render_slide(title: str, body: str, output_path: Path, size: tuple[int, int] = (1280, 720)) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    width, height = size

    # Background gradient fill (Dark Blue #0F172A to #1E293B)
    image = Image.new("RGB", size, color=(15, 23, 42))
    draw = ImageDraw.Draw(image)

    # Decorative header bar / pill
    pill_margin = 60
    draw.rounded_rectangle(
        [(pill_margin, 45), (pill_margin + 200, 85)],
        radius=12,
        fill=(13, 148, 136), # Teal accent
    )
    badge_font = _get_font(20, bold=True)
    draw.text((pill_margin + 25, 53), "COMUNICADO", fill=(255, 255, 255), font=badge_font)

    # Title text
    title_font = _get_font(42, bold=True)
    draw.text((pill_margin, 110), title, fill=(255, 255, 255), font=title_font)

    # Main Card Container for body text
    card_top = 180
    card_bottom = height - 80
    card_left = pill_margin
    card_right = width - pill_margin

    draw.rounded_rectangle(
        [(card_left, card_top), (card_right, card_bottom)],
        radius=20,
        fill=(30, 41, 59), # Slate 800
        outline=(51, 65, 85), # Slate 700 border
        width=2,
    )

    # Body text rendering inside card
    body_font = _get_font(28, bold=False)
    y_position = card_top + 40
    content_left = card_left + 40
    max_line_width = 65

    for paragraph in (body or "").splitlines() or [body]:
        wrapped = wrap(paragraph, width=max_line_width) or [""]
        for line in wrapped:
            if y_position + 40 > card_bottom - 20:
                break
            draw.text((content_left, y_position), line, fill=(226, 232, 240), font=body_font)
            y_position += 42
        y_position += 14
        if y_position + 40 > card_bottom - 20:
            break

    # Footer
    footer_font = _get_font(18, bold=False)
    draw.text((pill_margin, height - 50), "Sinalização Digital Local • TV Box PicoClaw", fill=(100, 116, 139), font=footer_font)

    image.save(output_path)
    return output_path

