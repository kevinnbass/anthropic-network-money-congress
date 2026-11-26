"""Chromium capture helper, run with the repository's rendering venv."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        raise SystemExit("expected html png jpg width height")
    html_path, png_path, jpg_path = map(Path, argv[:3])
    width, height = map(int, argv[3:])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=2)
        page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        overflow = page.evaluate("({w:document.documentElement.scrollWidth,h:document.documentElement.scrollHeight})")
        if overflow["w"] > width or overflow["h"] > height:
            raise RuntimeError(f"content overflow {overflow} viewport={width}x{height}")
        footnote = page.locator(".footnote").bounding_box()
        if not footnote or footnote["y"] + footnote["height"] > height:
            raise RuntimeError(f"footnote overflow {footnote} viewport_height={height}")
        page.screenshot(path=str(png_path))
        browser.close()
    image = Image.open(png_path).convert("RGB")
    image.save(jpg_path, quality=94)
    print(f"rendered {html_path.stem} {image.size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
