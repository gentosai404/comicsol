#!/usr/bin/env python3
"""Deterministic panel lettering for Comic Sol."""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from comic_sol import atomic_write_bytes, read_json


ROOT = Path(__file__).resolve().parents[1]
FONT_PATH = ROOT / "assets/fonts/NotoSans-Regular.ttf"
ANCHORS = (
    "top-left",
    "top-center",
    "top-right",
    "middle-right",
    "bottom-right",
    "bottom-center",
    "bottom-left",
    "middle-left",
)


def normalize_content(text: str) -> str:
    """Normalize authored text without changing punctuation, emoji, or newlines."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = unicodedata.normalize("NFC", text)
    normalized = "".join(
        " " if unicodedata.category(character) == "Cc" and character != "\n" else character
        for character in normalized
    )
    lines = [re.sub(r"[^\S\n]+", " ", line).strip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def normalized_word_count(text: str) -> int:
    """Count whitespace-separated words after deterministic normalization."""
    return len(normalize_content(text).split())


def _known_character(character_bible: list[dict], speaker: object) -> bool:
    if not isinstance(speaker, str) or not speaker:
        return False
    return any(
        isinstance(character, dict)
        and speaker in {character.get("id"), character.get("name")}
        for character in character_bible
    )


def _wrap_lines(
    draw: ImageDraw.ImageDraw,
    content: str,
    font: ImageFont.FreeTypeFont,
    maximum_width: int,
) -> tuple[str, ...]:
    lines: list[str] = []
    for paragraph in content.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        if draw.textbbox((0, 0), current, font=font, stroke_width=0)[2] > maximum_width:
            return ()
        for word in words[1:]:
            candidate = f"{current} {word}"
            bounds = draw.textbbox((0, 0), candidate, font=font, stroke_width=0)
            if bounds[2] - bounds[0] <= maximum_width:
                current = candidate
            else:
                lines.append(current)
                current = word
                if draw.textbbox((0, 0), current, font=font, stroke_width=0)[2] > maximum_width:
                    return ()
        lines.append(current)
    return tuple(lines)


def _line_metrics(
    draw: ImageDraw.ImageDraw,
    lines: tuple[str, ...],
    font: ImageFont.FreeTypeFont,
    spacing: int = 6,
) -> tuple[int, int]:
    widths: list[int] = []
    heights: list[int] = []
    for line in lines:
        sample = line or "Ag"
        left, top, right, bottom = draw.textbbox((0, 0), sample, font=font)
        widths.append(right - left if line else 0)
        heights.append(bottom - top)
    return max(widths, default=0), sum(heights) + spacing * max(0, len(lines) - 1)


def _anchor_rect(anchor: str, width: int, height: int) -> dict[str, int]:
    inset_x = max(4, round(width * 0.04))
    inset_y = max(4, round(height * 0.04))
    box_width = min(width - 2 * inset_x, max(1, round(width * 0.42)))
    box_height = min(height - 2 * inset_y, max(1, round(height * 0.30)))
    horizontal = {
        "left": inset_x,
        "center": (width - box_width) // 2,
        "right": width - inset_x - box_width,
    }
    vertical = {
        "top": inset_y,
        "middle": (height - box_height) // 2,
        "bottom": height - inset_y - box_height,
    }
    vertical_name, horizontal_name = anchor.split("-", 1)
    return {
        "x": horizontal[horizontal_name],
        "y": vertical[vertical_name],
        "width": box_width,
        "height": box_height,
    }


def _overlap(first: dict[str, int], second: dict[str, int]) -> bool:
    return not (
        first["x"] + first["width"] <= second["x"]
        or second["x"] + second["width"] <= first["x"]
        or first["y"] + first["height"] <= second["y"]
        or second["y"] + second["height"] <= first["y"]
    )


def _item_font_and_lines(
    draw: ImageDraw.ImageDraw,
    item: dict,
    rect: dict[str, int],
) -> tuple[ImageFont.FreeTypeFont, tuple[str, ...]]:
    kind = item.get("kind")
    padding = 24 if kind == "dialogue" else 20 if kind == "caption" else 8
    start_size = 64 if kind == "sfx" else 42
    content = normalize_content(item.get("content", ""))
    for size in range(start_size, 23, -2):
        font = ImageFont.truetype(str(FONT_PATH), size)
        lines = _wrap_lines(draw, content, font, max(1, rect["width"] - 2 * padding))
        if not lines:
            continue
        text_width, text_height = _line_metrics(draw, lines, font)
        if text_width <= rect["width"] - 2 * padding and text_height <= rect["height"] - 2 * padding:
            return font, lines
    item_id = item.get("id", "unknown")
    raise ValueError(f"text item {item_id} does not fit inside the panel")


def render_text_item(
    draw: ImageDraw.ImageDraw,
    item: dict,
    rect: dict,
    font: ImageFont.FreeTypeFont,
    character_bible: list[dict],
) -> None:
    """Draw one validated text item inside an explicit bounded rectangle."""
    kind = item.get("kind")
    content = normalize_content(item.get("content", ""))
    if not content:
        raise ValueError(f"text item {item.get('id', 'unknown')} has empty content")
    if kind not in {"dialogue", "caption", "sfx"}:
        raise ValueError(f"text item {item.get('id', 'unknown')} has unknown kind")
    if kind == "dialogue" and not _known_character(character_bible, item.get("speaker")):
        raise ValueError(f"unknown dialogue character: {item.get('speaker')}")

    image_width, image_height = draw._image.size
    x0 = max(0, int(rect["x"]))
    y0 = max(0, int(rect["y"]))
    x1 = min(image_width - 1, x0 + max(1, int(rect["width"])))
    y1 = min(image_height - 1, y0 + max(1, int(rect["height"])))
    bounded = {"x": x0, "y": y0, "width": x1 - x0, "height": y1 - y0}
    padding = 24 if kind == "dialogue" else 20 if kind == "caption" else 8
    lines = _wrap_lines(draw, content, font, max(1, bounded["width"] - 2 * padding))
    if not lines:
        raise ValueError(f"text item {item.get('id', 'unknown')} cannot be wrapped")
    text_width, text_height = _line_metrics(draw, lines, font)
    text_x = x0 + max(padding, (bounded["width"] - text_width) // 2)
    text_y = y0 + max(padding, (bounded["height"] - text_height) // 2)
    rendered = "\n".join(lines)

    if kind == "dialogue":
        tail = item.get("tail_target")
        if isinstance(tail, list) and len(tail) == 2 and all(isinstance(value, (int, float)) for value in tail):
            target_x = min(image_width - 1, max(0, round(float(tail[0]) * image_width)))
            target_y = min(image_height - 1, max(0, round(float(tail[1]) * image_height)))
            origin = ((x0 + x1) // 2, (y0 + y1) // 2)
            draw.line((origin, (target_x, target_y)), fill=(15, 15, 15, 255), width=5)
        draw.rounded_rectangle(
            (x0, y0, x1, y1), radius=max(12, min(bounded["width"], bounded["height"]) // 8),
            fill=(255, 255, 255, 255), outline=(15, 15, 15, 255), width=3,
        )
        draw.multiline_text((text_x, text_y), rendered, font=font, fill=(10, 10, 10, 255), spacing=6, align="center")
    elif kind == "caption":
        draw.rounded_rectangle(
            (x0, y0, x1, y1), radius=8,
            fill=(8, 10, 14, 190), outline=(245, 245, 245, 230), width=2,
        )
        draw.multiline_text((text_x, text_y), rendered, font=font, fill=(255, 255, 255, 255), spacing=6, align="center")
    else:
        center_x = (x0 + x1) // 2
        center_y = (y0 + y1) // 2
        impact = min(bounded["width"], bounded["height"]) // 5
        draw.polygon(
            ((center_x, center_y - impact), (center_x + impact, center_y),
             (center_x, center_y + impact), (center_x - impact, center_y)),
            fill=(20, 20, 20, 220), outline=(255, 255, 255, 255),
        )
        draw.multiline_text(
            (text_x, text_y), rendered, font=font, fill=(12, 12, 12, 255),
            spacing=4, align="center", stroke_width=6, stroke_fill=(255, 255, 255, 255),
        )


def letter_panel(
    output_path: str,
    panel_width: int,
    panel_height: int,
    text_items: list[dict],
    character_bible: list[dict],
) -> dict:
    """Letter an existing panel atomically and return a compact output summary."""
    if not isinstance(panel_width, int) or not isinstance(panel_height, int) or panel_width <= 0 or panel_height <= 0:
        raise ValueError("panel dimensions must be positive integers")
    if not isinstance(text_items, list) or not isinstance(character_bible, list):
        raise TypeError("text_items and character_bible must be lists")
    path = Path(output_path)
    try:
        with Image.open(path) as source:
            base = ImageOps.exif_transpose(source).convert("RGBA")
            if base.size != (panel_width, panel_height):
                base = ImageOps.fit(base, (panel_width, panel_height), method=Image.Resampling.LANCZOS)
    except OSError as error:
        raise ValueError(f"panel is not a readable image: {path}") from error

    ordered = sorted(
        (dict(item) for item in text_items),
        key=lambda item: (item.get("priority", 0), str(item.get("id", ""))),
    )
    for item in ordered:
        if item.get("kind") == "dialogue" and not _known_character(character_bible, item.get("speaker")):
            raise ValueError(f"unknown dialogue character: {item.get('speaker')}")
        content = normalize_content(item.get("content", ""))
        limit = {"dialogue": 32, "caption": 45, "sfx": 3}.get(item.get("kind"))
        if limit is None:
            raise ValueError(f"text item {item.get('id', 'unknown')} has unknown kind")
        if not content or normalized_word_count(content) > limit:
            raise ValueError(f"text item {item.get('id', 'unknown')} exceeds its content limit")
        item["content"] = content

    canvas = base.copy()
    draw = ImageDraw.Draw(canvas, "RGBA")
    occupied: list[dict[str, int]] = []
    for item in ordered:
        requested = "top-left" if item.get("kind") == "caption" else item.get("anchor", "top-left")
        if requested not in ANCHORS:
            raise ValueError(f"text item {item.get('id', 'unknown')} has unknown anchor")
        start = ANCHORS.index(requested)
        rect = None
        for offset in range(len(ANCHORS)):
            candidate = _anchor_rect(ANCHORS[(start + offset) % len(ANCHORS)], panel_width, panel_height)
            if not any(_overlap(candidate, prior) for prior in occupied):
                rect = candidate
                break
        if rect is None:
            raise ValueError(f"text item {item.get('id', 'unknown')} has no non-overlapping placement")
        font, _ = _item_font_and_lines(draw, item, rect)
        render_text_item(draw, item, rect, font, character_bible)
        occupied.append(rect)

    encoded = io.BytesIO()
    canvas.convert("RGB").save(encoded, format="PNG", optimize=False, compress_level=9)
    atomic_write_bytes(path, encoded.getvalue())
    word_count = sum(normalized_word_count(item["content"]) for item in ordered)
    return {
        "font_used": str(FONT_PATH),
        "lettered_path": str(path),
        "text_count": len(ordered),
        "word_count": word_count,
    }


def letter_project(project_dir: Path) -> list[Path]:
    """Letter every accepted project panel using its editable storyboard text."""
    project_dir = Path(project_dir)
    storyboard = read_json(project_dir / "plan/storyboard.json")
    bible = read_json(project_dir / "plan/character-bible.json").get("characters", [])
    panels = [
        panel
        for page in storyboard.get("pages", [])
        for panel in page.get("panels", [])
    ]
    outputs: list[Path] = []
    for panel in panels:
        panel_id = panel["id"]
        source = project_dir / f"panels/clean/{panel_id}.png"
        destination = project_dir / f"panels/{panel_id}/lettered.png"
        atomic_write_bytes(destination, source.read_bytes())
        with Image.open(source) as image:
            width, height = image.size
        letter_panel(str(destination), width, height, panel.get("text", []), bible)
        outputs.append(destination)
    return outputs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="letter_panels.py")
    parser.add_argument("panel_dir", type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--font", type=Path, default=FONT_PATH)
    return parser


def main(argv: list[str] | None = None) -> int:
    global FONT_PATH
    arguments = _build_parser().parse_args(argv)
    FONT_PATH = arguments.font
    try:
        arguments.output_root.mkdir(parents=True, exist_ok=True)
        results = []
        for record_path in sorted(arguments.panel_dir.glob("*.json")):
            record = json.loads(record_path.read_text("utf-8"))
            panel_id = record.get("panel_id", record_path.stem)
            source = arguments.panel_dir / f"{panel_id}.png"
            if not source.is_file():
                raise ValueError(f"missing panel PNG for {panel_id}")
            destination = arguments.output_root / f"{panel_id}.png"
            atomic_write_bytes(destination, source.read_bytes())
            with Image.open(source) as image:
                width, height = image.size
            results.append(letter_panel(
                str(destination), width, height,
                record.get("text_items", []), record.get("character_bible", []),
            ))
        print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
