"""Compose the published diagram image from the mermaid render.

Takes the title-less flowchart that mermaid-cli produces (`diagram_only.png`)
and bolts on a branded header band: the report title bottom-left with a cyan
accent bar, and the Nugget Scientific logo top-right. The result is written to
`assets/diagram.png`, which the site offers as a download and uses for the
social-share preview (og:image).

Why a separate compose step instead of a mermaid title: mermaid centers its
title and gives no control over a logo, so the header is painted here where we
can place both precisely. Run via `src/build.sh`, not directly.

Gotcha: the title font is resolved from a short candidate list so the build
works on macOS (Arial Bold) and Linux CI (DejaVu) alike; it falls back to PIL's
bundled default rather than failing the build.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Brand palette — kept in sync with the node colors in service_lifecycle.mmd.
NAVY = (12, 68, 124)    # #0C447C  title + main-flow text
CYAN = (53, 168, 220)   # nugget logo cyan, used for the accent bar
RULE = (220, 227, 234)  # subtle divider under the header

HEADER_HEIGHT = 720     # px, at the 3x render scale
PADDING = 90            # px breathing room inside the header band
TITLE = "Nugget Service Scheduling Flow"

# First font that exists wins; last entry is always available via PIL.
TITLE_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Debian/Ubuntu CI
    "DejaVuSans-Bold.ttf",  # PIL-bundled fallback
]

ROOT = Path(__file__).resolve().parent.parent
DIAGRAM_ONLY = ROOT / "src" / "diagram_only.png"
LOGO = ROOT / "assets" / "logo.png"
OUTPUT = ROOT / "assets" / "diagram.png"


def load_title_font(size: int) -> ImageFont.FreeTypeFont:
    """Return the first available bold sans-serif at the given size."""
    for candidate in TITLE_FONT_CANDIDATES:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def compose() -> None:
    diagram = Image.open(DIAGRAM_ONLY).convert("RGBA")
    logo = Image.open(LOGO).convert("RGBA")
    width, height = diagram.size

    canvas = Image.new("RGBA", (width, height + HEADER_HEIGHT), (255, 255, 255, 255))

    # Logo, top-right, scaled to fill the header band height.
    logo_h = HEADER_HEIGHT - 2 * PADDING
    logo_w = round(logo.width * logo_h / logo.height)
    logo_scaled = logo.resize((logo_w, logo_h), Image.LANCZOS)
    canvas.alpha_composite(logo_scaled, (width - PADDING - logo_w, (HEADER_HEIGHT - logo_h) // 2))

    # Title, left, vertically centered, with a cyan accent bar beneath it.
    draw = ImageDraw.Draw(canvas)
    font = load_title_font(188)
    box = draw.textbbox((0, 0), TITLE, font=font)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    tx, ty = PADDING - box[0], (HEADER_HEIGHT - text_h) // 2 - box[1]
    draw.text((tx, ty), TITLE, font=font, fill=NAVY)
    bar_y = ty + box[3] + 28
    draw.rectangle([PADDING, bar_y, PADDING + min(text_w, 760), bar_y + 12], fill=CYAN)

    # Divider, then the diagram below the header.
    draw.rectangle([0, HEADER_HEIGHT - 2, width, HEADER_HEIGHT + 1], fill=RULE)
    canvas.alpha_composite(diagram, (0, HEADER_HEIGHT))

    canvas.convert("RGB").save(OUTPUT, "PNG")
    print(f"wrote {OUTPUT} ({canvas.width}x{canvas.height})")


if __name__ == "__main__":
    compose()
