"""Render promotional text (Arabic RTL, French, mixed) to transparent PNG layers.

Arabic needs two things that plain drawing does not give: contextual shaping
(letters join) and right-to-left ordering. Pillow does both when it is built
with libraqm (HarfBuzz + FriBiDi). If raqm is not usable on the machine we
fall back to arabic-reshaper + python-bidi, which gives correct results for
ordinary advertising copy.
"""

from __future__ import annotations

import functools
import logging
import os

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, features

from .config import POSITIONS

log = logging.getLogger("proads")

_ARABIC_RANGES = ((0x0600, 0x06FF), (0x0750, 0x077F), (0x08A0, 0x08FF), (0xFB50, 0xFDFF), (0xFE70, 0xFEFF))


def has_arabic(text: str) -> bool:
    return any(lo <= ord(ch) <= hi for ch in text for lo, hi in _ARABIC_RANGES)


@functools.lru_cache(maxsize=1)
def shaping_engine() -> str:
    """'raqm' (preferred) or 'fallback' (arabic-reshaper + python-bidi)."""
    if features.check("raqm"):
        return "raqm"
    try:
        import arabic_reshaper  # noqa: F401
        import bidi.algorithm  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "Arabic text cannot be shaped: Pillow has no raqm support and the fallback "
            "packages are missing. Run: pip install arabic-reshaper python-bidi"
        ) from e
    log.warning("Pillow has no raqm support; using arabic-reshaper + python-bidi fallback")
    return "fallback"


_FALLBACK_ARABIC_FONTS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
)


@functools.lru_cache(maxsize=16)
def _has_presentation_forms(path: str) -> bool:
    """Does the font map the pre-shaped Arabic letters that the fallback engine emits?"""
    font = ImageFont.truetype(path, 40, layout_engine=ImageFont.Layout.BASIC)
    missing = font.getmask("\uffff")
    glyph = font.getmask("\ufeb3")  # ARABIC LETTER SEEN, initial form
    return glyph.getbbox() is not None and (glyph.size != missing.size or bytes(glyph) != bytes(missing))


@functools.lru_cache(maxsize=64)
def _font(path: str, size: int, engine: str, arabic: bool = False) -> ImageFont.FreeTypeFont:
    if engine == "raqm":
        return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
    if arabic and not _has_presentation_forms(path):
        # Without raqm we need a font that contains pre-shaped Arabic glyphs.
        for candidate in _FALLBACK_ARABIC_FONTS:
            if os.path.isfile(candidate) and _has_presentation_forms(candidate):
                log.warning("raqm unavailable: drawing Arabic with %s instead of %s", candidate, path)
                path = candidate
                break
        else:
            raise RuntimeError(
                "Arabic text cannot be drawn correctly on this machine: Pillow has no raqm support "
                "and no fallback Arabic font was found. Install the system package 'libfribidi0' "
                "(the GitHub workflow does this) or 'fonts-dejavu-core'."
            )
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.BASIC)


@functools.lru_cache(maxsize=1)
def _reshaper():
    import arabic_reshaper
    # Many fonts (the bundled Tajawal included) have no separate "isolated form"
    # glyphs: a stand-alone letter is simply the base character.
    return arabic_reshaper.ArabicReshaper(configuration={"use_unshaped_instead_of_isolated": True})


class _Line:
    """One line of text, ready to be measured and drawn with the active engine."""

    def __init__(self, logical: str, font, engine: str, rtl: bool):
        self.font = font
        if engine == "raqm":
            self.text = logical
            self.kwargs = {"direction": "rtl" if rtl else "ltr", "language": "ar" if rtl else "fr"}
        else:
            if has_arabic(logical):
                from bidi.algorithm import get_display
                logical = get_display(_reshaper().reshape(logical), base_dir="R" if rtl else "L")
            self.text = logical
            self.kwargs = {}
        self.width = font.getlength(self.text, **self.kwargs)

    def draw(self, draw: ImageDraw.ImageDraw, x: float, y: float, anchor: str, fill, **extra):
        draw.text((x, y), self.text, font=self.font, fill=fill, anchor=anchor, **self.kwargs, **extra)


def _wrap(text: str, make_line, max_px: float) -> list[_Line]:
    lines: list[_Line] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            continue
        current = words[0]
        for word in words[1:]:
            if make_line(current + " " + word).width <= max_px:
                current += " " + word
            else:
                lines.append(make_line(current))
                current = word
        lines.append(make_line(current))
    return lines


def _rgba(color: str, opacity: float = 1.0) -> tuple[int, int, int, int]:
    r, g, b = ImageColor.getrgb(color)[:3]
    return (r, g, b, round(255 * max(0.0, min(1.0, opacity))))


def render_text(spec: dict, text: str, width: int, height: int, style: dict) -> tuple[Image.Image, tuple[int, int]]:
    """Render one text element for a width x height frame.

    Returns the RGBA layer and the (x, y) of its top-left corner in the frame.
    Sizes in the config are expressed for a 1080-pixel-wide vertical frame and
    scale automatically with the output resolution.
    """
    engine = shaping_engine()
    unit = min(width, height) / 1080.0
    rtl = has_arabic(text)
    font_path = style[f"font_{spec.get('weight', 'bold')}"]
    box = spec.get("box")
    pad = round((box.get("padding", 26) if box else 0) * unit)
    max_px = spec.get("max_width", 0.86) * width - 2 * pad

    size = max(8, round(spec.get("size", 64) * unit))
    while True:
        font = _font(font_path, size, engine, rtl)
        lines = _wrap(text, lambda s: _Line(s, font, engine, rtl), max_px)
        if not lines:
            raise ValueError("text is empty")
        if max(l.width for l in lines) <= max_px or size <= 12:
            break
        size = int(size * 0.93)  # a single word is too wide: shrink until it fits

    line_h = round(size * 1.38)
    block_w = round(max(l.width for l in lines))
    block_h = line_h * len(lines)
    stroke = spec.get("stroke") or {}
    stroke_w = round(stroke.get("width", 0) * unit)
    shadow = spec.get("shadow", style.get("shadow", True)) and not box
    margin = round(size * 0.35) + stroke_w  # room for shadow blur, stroke and glyph overhang

    img_w = block_w + 2 * (pad + margin)
    img_h = block_h + 2 * (pad + margin)
    layer = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))

    align = spec.get("align", "center")
    if align == "left":
        tx, anchor = margin + pad, "lm"
    elif align == "right":
        tx, anchor = img_w - margin - pad, "rm"
    else:
        tx, anchor = img_w / 2, "mm"

    def draw_lines(target: Image.Image, fill, dy: float = 0, **extra):
        d = ImageDraw.Draw(target)
        for i, line in enumerate(lines):
            line.draw(d, tx, margin + pad + line_h * (i + 0.5) + dy, anchor, fill, **extra)

    if box:
        radius = round(box.get("radius", 22) * unit)
        ImageDraw.Draw(layer).rounded_rectangle(
            (margin, margin, img_w - margin - 1, img_h - margin - 1),
            radius=radius,
            fill=_rgba(box.get("color", style["accent_color"]), box.get("opacity", 1.0)),
        )
    if shadow:
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        draw_lines(sh, (0, 0, 0, 190), dy=size * 0.05)
        layer = Image.alpha_composite(layer, sh.filter(ImageFilter.GaussianBlur(max(1.0, size * 0.07))))

    color = _rgba(spec.get("color", style["text_color"]))
    if stroke_w > 0:
        draw_lines(layer, color, stroke_width=stroke_w, stroke_fill=_rgba(stroke.get("color", "#000000")))
    else:
        draw_lines(layer, color)

    pos = spec.get("position", "center")
    fx, fy = POSITIONS[pos] if isinstance(pos, str) else (pos["x"], pos["y"])
    safe = round(0.02 * min(width, height)) - margin  # the transparent margin may leave the frame
    x = round(fx * width - img_w / 2)
    y = round(fy * height - img_h / 2)
    x = max(safe, min(x, width - img_w - safe)) if img_w + 2 * safe <= width else (width - img_w) // 2
    y = max(safe, min(y, height - img_h - safe)) if img_h + 2 * safe <= height else (height - img_h) // 2
    return layer, (x, y)
