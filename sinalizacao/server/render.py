from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont


def render_slide(title: str, body: str, output_path: Path, size: tuple[int, int] = (1280, 720)) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", size, color=(16, 24, 40))
    draw = ImageDraw.Draw(image)

    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()

    margin = 64
    draw.text((margin, margin), title, fill=(255, 255, 255), font=title_font)

    y_position = margin + 80
    for paragraph in body.splitlines() or [body]:
        for line in wrap(paragraph, width=44) or [""]:
            draw.text((margin, y_position), line, fill=(220, 230, 245), font=body_font)
            y_position += 28
        y_position += 10

    image.save(output_path)
    return output_path
