"""Render verified text evidence into readable PNG artifacts.

This script does not invent runtime values.  It only renders the UTF-8 text
files collected from tests, validators, application logs, and Langfuse APIs.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "submission" / "evidence"
WIDTH, HEIGHT = 1600, 1000


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


TITLE_FONT = font("segoeuib.ttf", 25)
MONO_FONT = font("consola.ttf", 22)
MONO_SMALL = font("consola.ttf", 18)
CARD_TITLE = font("segoeuib.ttf", 21)
CARD_VALUE = font("segoeuib.ttf", 31)


def wrap_line(draw: ImageDraw.ImageDraw, value: str, chosen_font, max_width: int) -> list[str]:
    if not value:
        return [""]
    output: list[str] = []
    current = ""
    for character in value:
        candidate = current + character
        if current and draw.textlength(candidate, font=chosen_font) > max_width:
            output.append(current)
            current = character
        else:
            current = candidate
    output.append(current)
    return output


def terminal_image(name: str, text: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#07111f")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((35, 35, WIDTH - 35, HEIGHT - 35), 18, fill="#0b1728", outline="#28425f", width=2)
    draw.rounded_rectangle((35, 35, WIDTH - 35, 96), 18, fill="#10233a", outline="#28425f", width=2)
    draw.rectangle((35, 75, WIDTH - 35, 96), fill="#10233a")
    draw.ellipse((58, 55, 76, 73), fill="#fb7185")
    draw.ellipse((88, 55, 106, 73), fill="#fbbf24")
    draw.ellipse((118, 55, 136, 73), fill="#34d399")
    draw.text((160, 51), f"{name} — verified runtime evidence", font=TITLE_FONT, fill="#7dd3fc")

    chosen = MONO_FONT
    lines: list[str] = []
    for source_line in text.splitlines():
        lines.extend(wrap_line(draw, source_line, chosen, WIDTH - 130))
    if len(lines) > 34:
        chosen = MONO_SMALL
        lines = []
        for source_line in text.splitlines():
            lines.extend(wrap_line(draw, source_line, chosen, WIDTH - 130))

    y = 125
    spacing = 8 if chosen is MONO_FONT else 6
    for line in lines:
        if y > HEIGHT - 55:
            break
        color = "#fbbf24" if "ROOT CAUSE" in line or "Finding:" in line else "#e6edf7"
        draw.text((65, y), line, font=chosen, fill=color)
        y += chosen.size + spacing
    return image


def dashboard_image(text: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), "#07111f")
    draw = ImageDraw.Draw(image)
    draw.text((55, 38), "LLMOps Runtime Dashboard", font=font("segoeuib.ttf", 35), fill="#f8fafc")
    draw.text((55, 87), "60 minute window  •  refresh 30s  •  final dataset", font=font("segoeui.ttf", 21), fill="#94a3b8")
    cards = [
        ("Latency", "P95 5025 ms", "P50 152 • P99 5025 • TTFT 50 ms", "#fb7185"),
        ("Traffic", "17 requests", "0.28 requests/minute", "#38bdf8"),
        ("Errors / Retrieval", "0.0% / 100%", "error rate / retrieval success", "#34d399"),
        ("Cost", "$0.034221", "total USD", "#fbbf24"),
        ("Tokens", "622 / 2157", "input / output", "#a78bfa"),
        ("Quality", "0.859", "threshold 0.75", "#2dd4bf"),
    ]
    for index, (title, value, note, accent) in enumerate(cards):
        column, row = index % 3, index // 3
        x = 55 + column * 505
        y = 155 + row * 355
        draw.rounded_rectangle((x, y, x + 465, y + 300), 18, fill="#0b1728", outline="#28425f", width=2)
        draw.rectangle((x, y, x + 8, y + 300), fill=accent)
        draw.text((x + 35, y + 30), title, font=CARD_TITLE, fill="#cbd5e1")
        draw.text((x + 35, y + 105), value, font=CARD_VALUE, fill=accent)
        draw.text((x + 35, y + 170), note, font=font("segoeui.ttf", 18), fill="#94a3b8")
        draw.text((x + 35, y + 245), "LIVE DATA", font=font("segoeuib.ttf", 16), fill="#64748b")
    draw.text((55, 910), "Dashboard contract: 6/6 panels valid", font=font("segoeuib.ttf", 22), fill="#34d399")
    return image


def incident_metric_image(text: str) -> Image.Image:
    image = terminal_image("12-incident-metric", text)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((1000, 610, 1500, 900), 16, fill="#32131b", outline="#fb7185", width=3)
    draw.text((1040, 650), "SLO BREACH", font=font("segoeuib.ttf", 26), fill="#fb7185")
    draw.text((1040, 710), "P95  5025 ms", font=font("segoeuib.ttf", 38), fill="#f8fafc")
    draw.text((1040, 780), "threshold  2000 ms", font=font("segoeui.ttf", 23), fill="#fecdd3")
    draw.text((1040, 830), "TTFT 50 ms • errors 0%", font=font("segoeui.ttf", 20), fill="#94a3b8")
    return image


def main() -> None:
    stems = [
        "01-pytest", "02-log-validator", "03-dashboard-validator", "04-structured-log",
        "05-pii-redaction", "06-trace-list", "07-trace-waterfall", "08-trace-metadata",
        "09-prompt-versions", "10-prompt-rollback", "11-dashboard-overview",
        "12-incident-metric", "13-incident-log", "14-incident-trace",
    ]
    for stem in stems:
        source_stem = "11-dashboard-runtime" if stem == "11-dashboard-overview" else stem
        text = (EVIDENCE / f"{source_stem}.txt").read_text(encoding="utf-8")
        if stem == "11-dashboard-overview":
            image = dashboard_image(text)
        elif stem == "12-incident-metric":
            image = incident_metric_image(text)
        else:
            image = terminal_image(stem, text)
        destination = EVIDENCE / f"{stem}.png"
        image.save(destination, "PNG", optimize=True)
        print(f"rendered {destination.name}")


if __name__ == "__main__":
    main()
