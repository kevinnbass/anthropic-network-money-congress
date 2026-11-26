"""Shared visual primitives ported from the METR figure surface."""

from __future__ import annotations

import html
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable



BG = "#f7f4ee"
INK = "#191b1a"
MUTED = "#666960"
GRID = "#e3dfd5"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
RED = "#e34948"
GRAY = "#b2b4aa"


def esc(value: object) -> str:
    return html.escape(str(value), quote=False)


def money(value: float | str) -> str:
    number = float(value)
    if number >= 1_000_000:
        return f"${number / 1_000_000:,.1f}M" if number < 100_000_000 else f"${number / 1_000_000:,.0f}M"
    if number >= 1_000:
        return f"${number / 1_000:,.0f}K"
    return f"${number:,.0f}"


def wrap(value: object, width: int) -> list[str]:
    output: list[str] = []
    current = ""
    for word in str(value).split():
        if current and len(current) + len(word) + 1 > width:
            output.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        output.append(current)
    return output


def tspans(
    x: float,
    y: float,
    lines: Iterable[object],
    size: float,
    fill: str = INK,
    line_height: float | None = None,
    anchor: str = "start",
    weight: str = "normal",
) -> str:
    line_height = line_height or size * 1.2
    return "".join(
        f'<text x="{x:.1f}" y="{y + index * line_height:.1f}" font-size="{size}" '
        f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}">{esc(line)}</text>'
        for index, line in enumerate(lines)
    )


def legend(items: Iterable[tuple[str, str]]) -> str:
    return '<div class="legend">' + "".join(
        f'<span><i class="sw" style="background:{color}"></i>{esc(text)}</span>' for color, text in items
    ) + "</div>"


def card(title: str, body: str, color: str | None = None, size: int = 19) -> str:
    bar = f"border-left:6px solid {color};" if color else ""
    return (
        f'<div style="background:#efece4;border-radius:10px;padding:14px 18px;{bar}">'
        f'<div style="font-size:{size}px;font-weight:bold;line-height:1.25">{esc(title)}</div>'
        f'<div style="font-size:{size - 2}px;color:{MUTED};line-height:1.35;margin-top:6px">{esc(body)}</div></div>'
    )


def node(x: float, y: float, width: float, height: float, name: str, subtitle: str, color: str) -> str:
    title_size = min(24, max(13, int((width - 36) / max(1, 0.6 * len(name)))))
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="{color}" opacity="0.13"/>'
        f'<rect x="{x}" y="{y}" width="8" height="{height}" rx="3" fill="{color}"/>'
        + tspans(x + 22, y + 34, [name], title_size, INK, weight="bold")
        + tspans(x + 22, y + 62, wrap(subtitle, max(10, int(width / 9))), 17, MUTED, line_height=21)
    )


def flow(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    amount: float,
    label: str,
    color: str,
    base_px: float = 6.0,
    per_million_px: float = 1.4,
    dash: bool = False,
) -> str:
    width = base_px + max(0.0, float(amount)) / 1_000_000 * per_million_px
    middle = (x1 + x2) / 2
    dashed = ' stroke-dasharray="14 10"' if dash else ""
    return (
        f'<path d="M{x1},{y1} C{middle},{y1} {middle},{y2} {x2},{y2}" fill="none" '
        f'stroke="{color}" stroke-width="{width:.1f}" opacity="0.62"{dashed}/>'
        + tspans(middle, (y1 + y2) / 2 - width / 2 - 6, [label], 13, INK, anchor="middle", weight="bold")
    )


def strip_ids(text: str, prefixes: Iterable[str]) -> str:
    prefixes = list(prefixes)
    if not prefixes:
        return text
    choices = "|".join(re.escape(prefix) for prefix in sorted(prefixes, key=lambda value: (-len(value), value)))
    token = rf"(?:{choices})\d{{2,6}}(?:[–-](?:(?:{choices}))?\d{{2,6}})?"

    def clean(value: str) -> str:
        value = re.sub(rf"\s*\((?:{token}(?:[,;]\s*)?)+\)", "", value)
        value = re.sub(rf"\s*\b(?:rows?\s+|see\s+)?{token}(?:\s*[,;/]\s*{token})*\b", "", value)
        return value

    parts = re.split(r"(<[^>]+>)", text)
    return "".join(part if part.startswith("<") else clean(part) for part in parts)


def hidden_rows(ids: Iterable[str]) -> str:
    return "<!-- rows: " + " ".join(sorted(set(ids))) + " -->"


def shell(
    title: str,
    kicker: str,
    subtitle: str,
    body: str,
    footnote: str,
    width: int,
    height: int,
    extra_css: str = "",
) -> str:
    kicker = re.sub(r"^\s*Figure\s+\S+(?:\s*\([^)]*\))?\s*[·:—-]\s*", "", kicker)
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{esc(title)}</title><style>
*{{box-sizing:border-box}}html,body{{margin:0;width:{width}px;height:{height}px;background:{BG}}}
body{{padding:46px 60px 32px;font-family:Arial,Helvetica,sans-serif;color:{INK};display:flex;flex-direction:column}}
.kicker{{font-size:17px;letter-spacing:2.8px;text-transform:uppercase;color:{MUTED};font-weight:bold}}
h1{{font-size:48px;letter-spacing:-1.4px;margin:12px 0 10px;line-height:1.07}}
.subtitle{{font-size:23px;line-height:1.35;color:{MUTED};margin:0 0 16px;max-width:1900px}}
.legend{{display:flex;gap:28px;font-size:19px;color:{INK};margin:0 0 10px;flex-wrap:wrap}}
.legend span{{display:inline-flex;align-items:center;gap:9px}}.sw{{width:18px;height:18px;border-radius:4px;display:inline-block}}
.footnote{{margin-top:auto;border-top:1px solid #cdcfc6;padding-top:14px;font-size:16px;line-height:1.45;color:{MUTED}}}
.footnote b{{color:{INK}}}svg{{display:block;flex-shrink:0}}text{{font-family:Arial,Helvetica,sans-serif}}{extra_css}
</style></head><body><div class="kicker">{esc(kicker)}</div><h1>{title}</h1><p class="subtitle">{subtitle}</p>{body}<div class="footnote">{footnote}</div></body></html>'''


def render(stem: str, document: str, width: int, height: int, output: Path) -> tuple[Path, Path, Path]:
    output.mkdir(parents=True, exist_ok=True)
    html_path = output / f"{stem}.html"
    png_path = output / f"{stem}.png"
    jpg_path = output / f"{stem}.jpg"
    html_path.write_text(document, encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "casework.figures.capture",
        str(html_path),
        str(png_path),
        str(jpg_path),
        str(width),
        str(height),
    ]
    subprocess.run(command, cwd=Path(__file__).resolve().parents[2], check=True)
    return html_path, png_path, jpg_path
