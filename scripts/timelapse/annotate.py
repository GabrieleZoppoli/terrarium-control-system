"""Simple numbered-dot annotation (shared style with the website)."""
import io

from PIL import Image, ImageDraw, ImageFont

RADIUS = 9
_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size=14):
    try:
        return ImageFont.truetype(_FONT, size)
    except OSError:
        return ImageFont.load_default()


def draw_dots(jpeg: bytes, items: list, show_pending=True) -> bytes:
    im = Image.open(io.BytesIO(jpeg)).convert("RGB")
    d = ImageDraw.Draw(im)
    f = font(14)
    for it in items:
        try:
            x, y = float(it["x"]), float(it["y"])
        except (KeyError, TypeError, ValueError):
            continue
        pending = show_pending and bool(it.get("needs_owner"))
        ring = (255, 140, 0) if pending else (0, 0, 0)
        d.ellipse([x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS], fill=(255, 255, 255),
                  outline=ring, width=3 if pending else 2)
        label = str(it.get("id", "")) + ("?" if pending else "")
        tx, ty = x + RADIUS + 3, y - RADIUS
        d.text((tx, ty), label, font=f, fill=(255, 255, 255), stroke_width=2,
               stroke_fill=(0, 0, 0))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=90)
    return b.getvalue()
