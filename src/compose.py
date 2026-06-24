"""Compose the published diagram image from the mermaid render.

Takes the title-less flowchart that mermaid-cli produces (`diagram_only.png`)
and wraps it in two branded bands:

  * a header (top): the report title bottom-left with a cyan accent bar, and
    the Nugget Scientific logo top-right;
  * an ownership legend (bottom): one outlined swatch per owning role, matching
    the per-node BORDER colors in the diagram (border = owner, fill = phase).

The result is written to `assets/diagram.png`, which the site offers as a
download and uses for the social-share preview (og:image).

Why a separate compose step: mermaid centers its title, gives no control over a
logo, and has no concept of a footer legend, so both bands are painted here
where we can place everything precisely. Run via `src/build.sh`.

Gotcha: fonts are resolved from short candidate lists so the build works on
macOS (Arial/Helvetica) and Linux CI (DejaVu) alike, falling back to PIL's
bundled default rather than failing the build.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Brand palette — kept in sync with the node colors in service_lifecycle.mmd.
NAVY = (12, 68, 124)    # #0C447C  title + main-flow text
CYAN = (53, 168, 220)   # nugget logo cyan, used for the accent bar
RULE = (220, 227, 234)  # subtle dividers
INK = (31, 45, 61)      # legend label text

# Owner -> border color. Must match the `style ... stroke:` lines in the .mmd.
OWNERS = [
    ("Dispatcher / Scheduler", (30, 111, 176)),       # #1E6FB0
    ("Field Engineer", (14, 138, 110)),               # #0E8A6E
    ("Sales", (217, 105, 12)),                        # #D9690C
    ("SME", (192, 57, 43)),                           # #C0392B
    ("Procurement / Parts", (126, 63, 168)),          # #7E3FA8
    ("Account Mgr / Service Lead", (181, 39, 126)),   # #B5277E
    ("Client", (91, 107, 123)),                       # #5B6B7B
]

HEADER_HEIGHT = 720     # px, at the 3x render scale
FOOTER_HEIGHT = 520     # px, ownership legend band
PADDING = 90            # px breathing room inside both bands
TITLE = "Nugget Service Scheduling Flow"
FOOTER_LABEL = "PROCESS OWNERSHIP"

# First font that exists wins; last entry is always available via PIL.
BOLD_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",     # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Debian/Ubuntu CI
    "DejaVuSans-Bold.ttf",                                    # PIL-bundled fallback
]
BODY_FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",          # macOS
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",       # Debian/Ubuntu CI
    "DejaVuSans.ttf",                                         # PIL-bundled fallback
]

ROOT = Path(__file__).resolve().parent.parent
DIAGRAM_ONLY = ROOT / "src" / "diagram_only.png"
LOGO = ROOT / "assets" / "logo.png"
OUTPUT = ROOT / "assets" / "diagram.png"


def load_font(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    """Return the first available font from candidates at the given size."""
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_header(canvas: Image.Image, draw: ImageDraw.ImageDraw, width: int) -> None:
    """Title (bottom-left, with cyan accent) and logo (top-right)."""
    logo = Image.open(LOGO).convert("RGBA")
    logo_h = HEADER_HEIGHT - 2 * PADDING
    logo_w = round(logo.width * logo_h / logo.height)
    logo_scaled = logo.resize((logo_w, logo_h), Image.LANCZOS)
    canvas.alpha_composite(logo_scaled, (width - PADDING - logo_w, (HEADER_HEIGHT - logo_h) // 2))

    font = load_font(BOLD_FONT_CANDIDATES, 188)
    box = draw.textbbox((0, 0), TITLE, font=font)
    text_w, text_h = box[2] - box[0], box[3] - box[1]
    tx, ty = PADDING - box[0], (HEADER_HEIGHT - text_h) // 2 - box[1]
    draw.text((tx, ty), TITLE, font=font, fill=NAVY)
    bar_y = ty + box[3] + 28
    draw.rectangle([PADDING, bar_y, PADDING + min(text_w, 760), bar_y + 12], fill=CYAN)

    draw.rectangle([0, HEADER_HEIGHT - 2, width, HEADER_HEIGHT + 1], fill=RULE)


def draw_owner_legend(draw: ImageDraw.ImageDraw, width: int, top: int) -> None:
    """Horizontal ownership key: an outlined swatch (border = owner) per role."""
    draw.rectangle([0, top, width, top + 3], fill=RULE)
    center_y = top + FOOTER_HEIGHT // 2

    # Section label on the left.
    label_font = load_font(BOLD_FONT_CANDIDATES, 70)
    lb = draw.textbbox((0, 0), FOOTER_LABEL, font=label_font)
    draw.text((PADDING - lb[0], center_y - (lb[3] - lb[1]) // 2 - lb[1]),
              FOOTER_LABEL, font=label_font, fill=NAVY)
    x = PADDING + (lb[2] - lb[0]) + 120

    # Measure each item so the row can be spread evenly across the width.
    item_font = load_font(BODY_FONT_CANDIDATES, 62)
    swatch, gap_swatch_text = 66, 24
    measured = []
    for name, color in OWNERS:
        tb = draw.textbbox((0, 0), name, font=item_font)
        item_w = swatch + gap_swatch_text + (tb[2] - tb[0])
        measured.append((name, color, tb, item_w))

    total = sum(item_w for *_, item_w in measured)
    available = (width - PADDING) - x
    gap = max(70, (available - total) / (len(measured) - 1)) if len(measured) > 1 else 70

    for name, color, tb, item_w in measured:
        sy = center_y - swatch // 2
        # Outlined swatch (white fill, thick owner-color border) mirrors the node borders.
        draw.rounded_rectangle([x, sy, x + swatch, sy + swatch],
                               radius=13, fill=(255, 255, 255), outline=color, width=8)
        tx = x + swatch + gap_swatch_text
        draw.text((tx - tb[0], center_y - (tb[3] - tb[1]) // 2 - tb[1]), name, font=item_font, fill=INK)
        x += item_w + gap


def compose() -> None:
    diagram = Image.open(DIAGRAM_ONLY).convert("RGBA")
    width, height = diagram.size

    canvas = Image.new("RGBA", (width, HEADER_HEIGHT + height + FOOTER_HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(canvas)

    draw_header(canvas, draw, width)
    canvas.alpha_composite(diagram, (0, HEADER_HEIGHT))
    draw_owner_legend(draw, width, HEADER_HEIGHT + height)

    canvas.convert("RGB").save(OUTPUT, "PNG")
    print(f"wrote {OUTPUT} ({canvas.width}x{canvas.height})")


if __name__ == "__main__":
    compose()
