#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pillow",
# ]
# ///
"""
Combine panel images into a single comic page with title and captions.

Usage:
    uv run combine.py \
      --title "Comic Title" \
      --panels panel-1.png panel-2.png panel-3.png panel-4.png \
      --captions "Caption 1" "Caption 2" "Caption 3" "Caption 4" \
      --output comic-page.png \
      --style funny
"""

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

PANEL_W = 800
ASPECT_RATIO = 16 / 9
PANEL_H = int(PANEL_W / ASPECT_RATIO)
GUTTER = 20
MARGIN = 40
TITLE_H = 120
CAPTION_H = 100
COLS = 2

STYLES = {
    "funny": {"bg": "#FFFFFF", "title_bg": "#FFD700", "title_fg": "#000000", "caption_fg": "#333333", "border": "#333333"},
    "dramatic": {"bg": "#1A1A2E", "title_bg": "#E94560", "title_fg": "#FFFFFF", "caption_fg": "#CCCCCC", "border": "#E94560"},
    "technical": {"bg": "#F0F0F0", "title_bg": "#2196F3", "title_fg": "#FFFFFF", "caption_fg": "#333333", "border": "#2196F3"},
    "absurd": {"bg": "#FF69B4", "title_bg": "#00FF00", "title_fg": "#FF00FF", "caption_fg": "#FFFFFF", "border": "#FFFF00"},
    "noir": {"bg": "#111111", "title_bg": "#222222", "title_fg": "#CCCCCC", "caption_fg": "#999999", "border": "#444444"},
}


def find_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load Impact, then Arial, then fall back to default."""
    candidates = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines: list[str] = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, width: int, font: ImageFont.FreeTypeFont, fill: str) -> None:
    """Draw text centered horizontally at the given y position."""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) // 2
    draw.text((x, y + (CAPTION_H - text_h) // 2), text, font=font, fill=fill)


def combine_panels(
    title: str,
    panel_paths: list[str],
    captions: list[str],
    output_path: str,
    style: str = "funny",
) -> None:
    """Combine panel images into a comic page."""
    theme = STYLES.get(style, STYLES["funny"])
    n_panels = len(panel_paths)
    rows = math.ceil(n_panels / COLS)

    cell_h = PANEL_H + CAPTION_H
    canvas_w = MARGIN * 2 + COLS * PANEL_W + (COLS - 1) * GUTTER
    canvas_h = MARGIN + TITLE_H + rows * cell_h + (rows - 1) * GUTTER + MARGIN

    img = Image.new("RGB", (canvas_w, canvas_h), theme["bg"])
    draw = ImageDraw.Draw(img)

    title_font = find_font(48)
    caption_font = find_font(20)

    # Title banner
    draw.rectangle([(0, 0), (canvas_w, TITLE_H)], fill=theme["title_bg"])
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_tw = title_bbox[2] - title_bbox[0]
    title_th = title_bbox[3] - title_bbox[1]
    draw.text(
        ((canvas_w - title_tw) // 2, (TITLE_H - title_th) // 2),
        title,
        font=title_font,
        fill=theme["title_fg"],
    )

    # Panels
    for i in range(n_panels):
        row = i // COLS
        col = i % COLS
        x = MARGIN + col * (PANEL_W + GUTTER)
        y = TITLE_H + MARGIN + row * (cell_h + GUTTER)

        # Load and resize panel
        try:
            panel = Image.open(panel_paths[i])
            panel = panel.resize((PANEL_W, PANEL_H), Image.LANCZOS)
        except (FileNotFoundError, OSError) as e:
            print(f"Warning: Could not load panel {panel_paths[i]}: {e}", file=sys.stderr)
            panel = Image.new("RGB", (PANEL_W, PANEL_H), "#888888")
            err_draw = ImageDraw.Draw(panel)
            err_draw.text((PANEL_W // 3, PANEL_H // 2), "Missing panel", fill="#FFFFFF", font=caption_font)

        # Border
        draw.rectangle(
            [(x - 2, y - 2), (x + PANEL_W + 2, y + PANEL_H + 2)],
            outline=theme["border"],
            width=3,
        )
        img.paste(panel, (x, y))

        # Caption
        if i < len(captions) and captions[i]:
            max_cap_w = PANEL_W - 16
            lines = wrap_text(draw, captions[i], caption_font, max_cap_w)
            line_height = draw.textbbox((0, 0), "Ag", font=caption_font)[3] + 4
            total_h = line_height * len(lines)
            start_y = y + PANEL_H + (CAPTION_H - total_h) // 2
            for j, line in enumerate(lines):
                lbbox = draw.textbbox((0, 0), line, font=caption_font)
                lw = lbbox[2] - lbbox[0]
                lx = x + (PANEL_W - lw) // 2
                ly = start_y + j * line_height
                draw.text((lx, ly), line, font=caption_font, fill=theme["caption_fg"])

    # Handle odd panel count — "THE END" card in last cell
    if n_panels % 2 == 1 and n_panels > 1:
        row = n_panels // COLS
        col = n_panels % COLS
        x = MARGIN + col * (PANEL_W + GUTTER)
        y = TITLE_H + MARGIN + row * (cell_h + GUTTER)
        end_font = find_font(36)
        end_text = "THE END"
        end_bbox = draw.textbbox((0, 0), end_text, font=end_font)
        end_tw = end_bbox[2] - end_bbox[0]
        end_th = end_bbox[3] - end_bbox[1]
        draw.rectangle(
            [(x - 2, y - 2), (x + PANEL_W + 2, y + PANEL_H + 2)],
            outline=theme["border"],
            width=3,
        )
        draw.text(
            (x + (PANEL_W - end_tw) // 2, y + (PANEL_H - end_th) // 2),
            end_text,
            font=end_font,
            fill=theme["caption_fg"],
        )

    # Save
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    img.save(output_path)
    print(f"Comic page saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Combine panel images into a comic page")
    parser.add_argument("--title", required=True, help="Comic title")
    parser.add_argument("--panels", required=True, nargs="+", help="Paths to panel images")
    parser.add_argument("--captions", required=True, nargs="+", help="Caption text for each panel")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument(
        "--style",
        choices=list(STYLES.keys()),
        default="funny",
        help="Visual style theme (default: funny)",
    )

    args = parser.parse_args()

    if len(args.captions) != len(args.panels):
        print(
            f"Error: Number of captions ({len(args.captions)}) must match panels ({len(args.panels)})",
            file=sys.stderr,
        )
        sys.exit(1)

    combine_panels(args.title, args.panels, args.captions, args.output, args.style)


if __name__ == "__main__":
    main()
