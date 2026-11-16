import pytest
from PIL import ImageFont, features

from proads import textrender
from proads.config import DEFAULTS
from proads.textrender import has_arabic, render_text

STYLE = DEFAULTS["style"]
ENGINES = ["fallback"] + (["raqm"] if features.check("raqm") else [])


@pytest.fixture(params=ENGINES)
def engine(request, monkeypatch):
    monkeypatch.setattr(textrender, "shaping_engine", lambda: request.param)
    return request.param


def ink_columns(img):
    """Sum of alpha per pixel column."""
    alpha = img.getchannel("A")
    w, h = alpha.size
    data = alpha.tobytes()
    return [sum(data[x + y * w] for y in range(h)) for x in range(w)]


def test_detects_arabic():
    assert has_arabic("بيت نوم")
    assert has_arabic("Prix 2950 د.ت")
    assert not has_arabic("Livraison gratuite")


def test_arabic_is_laid_out_right_to_left(engine):
    # Logical order: wide letter (seen) first, thin letter (alef) second.
    # Right-to-left rendering must therefore put the wide letter on the RIGHT.
    img, _ = render_text({"text": "x", "size": 120, "shadow": False}, "س ا", 1080, 1920, STYLE)
    cols = ink_columns(img)
    mid = len(cols) // 2
    assert sum(cols[mid:]) > 1.3 * sum(cols[:mid])


def test_latin_is_laid_out_left_to_right(engine):
    img, _ = render_text({"text": "x", "size": 120, "shadow": False}, "W l", 1080, 1920, STYLE)
    cols = ink_columns(img)
    mid = len(cols) // 2
    assert sum(cols[:mid]) > 1.3 * sum(cols[mid:])


def test_arabic_letters_are_joined(engine):
    # Contextual (joined) forms are narrower than the same letters drawn isolated.
    font = textrender._font(STYLE["font_bold"], 100, engine, True)
    joined = textrender._Line("بيت", font, engine, True).width
    isolated = sum(textrender._Line(ch, font, engine, True).width for ch in "بيت")
    assert joined < 0.8 * isolated


def test_engines_agree_on_arabic_width():
    if "raqm" not in ENGINES:
        pytest.skip("raqm not available")
    widths = []
    for eng in ("raqm", "fallback"):
        font = textrender._font(STYLE["font_bold"], 100, eng, True)
        widths.append(textrender._Line("التوصيل بلاش لكامل تونس", font, eng, True).width)
    assert abs(widths[0] - widths[1]) < 0.05 * widths[0]


def test_bundled_font_covers_arabic_and_french():
    font = ImageFont.truetype(STYLE["font_bold"], 80, layout_engine=ImageFont.Layout.BASIC)
    missing = font.getmask(chr(0xFFFF))  # what the font draws for a character it lacks
    for ch in "éèêàçùôîÉÀ" + "ابتثجحخدذرزسشصضطظعغفقكلمنهوي" + "0123456789":
        glyph = font.getmask(ch)
        assert glyph.getbbox() is not None, f"no glyph for {ch!r}"
        assert glyph.size != missing.size or bytes(glyph) != bytes(missing), f"font lacks {ch!r}"


def test_long_text_wraps_and_stays_inside_the_frame(engine):
    text = "عرض خاص على بيوت النوم والصالونات وموبل التلفزة وخزاين الصبابط مع التوصيل بلاش لكامل تونس"
    for w, h in ((1080, 1920), (1920, 1080), (270, 480)):
        img, (x, y) = render_text({"text": "x", "size": 80, "position": "bottom"}, text, w, h, STYLE)
        bbox = img.getchannel("A").getbbox()  # visible ink within the layer
        assert x + bbox[0] >= 0 and x + bbox[2] <= w
        assert y + bbox[1] >= 0 and y + bbox[3] <= h
    tall, _ = render_text({"text": "x", "size": 80}, text, 1080, 1920, STYLE)
    one, _ = render_text({"text": "x", "size": 80}, "عرض خاص", 1080, 1920, STYLE)
    assert tall.height > 1.8 * one.height, "long text must wrap onto several lines"


def test_box_and_position(engine):
    spec = {"text": "x", "size": 90, "position": {"x": 0.5, "y": 0.25}, "box": {"color": "#FF0000", "opacity": 1.0}}
    img, (x, y) = render_text(spec, "2950 د.ت", 1080, 1920, STYLE)
    assert abs((x + img.width / 2) - 540) <= 1
    assert abs((y + img.height / 2) - 480) <= 1
    r, g, b, a = img.getpixel((img.width // 2, img.height - round(90 * 0.35) - 6))  # inside the box padding
    assert (r, g, b, a) == (255, 0, 0, 255)
