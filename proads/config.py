"""Configuration loading, defaults, placeholder expansion and validation."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from . import ffutil

FORMATS = {
    "vertical": (1080, 1920),    # 9:16  (Reels, TikTok, Stories)
    "horizontal": (1920, 1080),  # 16:9  (YouTube, Facebook feed, TV screens)
    "square": (1080, 1080),      # 1:1   (feed posts)
}

SCENE_TYPES = ("image", "video", "color")
FITS = ("cover", "contain")
MOTIONS = ("none", "zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down")
ANIMATIONS = ("none", "fade", "slide_up", "slide_down", "slide_left", "slide_right", "zoom")
WEIGHTS = ("regular", "bold", "black")
TRANSITIONS = (
    "cut", "fade", "fadeblack", "fadewhite", "dissolve",
    "slideleft", "slideright", "slideup", "slidedown",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    "smoothleft", "smoothright", "smoothup", "smoothdown",
    "circleopen", "circleclose", "radial", "zoomin", "pixelize", "hblur", "distance",
)
POSITIONS = {
    "top": (0.5, 0.11), "upper": (0.5, 0.27), "center": (0.5, 0.5),
    "lower": (0.5, 0.73), "bottom": (0.5, 0.88),
    "top_left": (0.27, 0.11), "top_right": (0.73, 0.11),
    "bottom_left": (0.27, 0.88), "bottom_right": (0.73, 0.88),
}

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
try:  # iPhone photos are often HEIC; supported when pillow-heif is installed
    import pillow_heif

    pillow_heif.register_heif_opener()
    IMAGE_EXT |= {".heic", ".heif"}
except ImportError:
    pass
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

DEFAULTS = {
    "output": {
        "formats": ["vertical", "horizontal"],
        "fps": 30, "crf": 18, "preset": "medium",
        "fade_in": 0.4, "fade_out": 0.6,
    },
    "style": {
        "text_color": "#FFFFFF", "accent_color": "#F2B134", "shadow": True,
        "font_regular": "assets/fonts/Tajawal-Regular.ttf",
        "font_bold": "assets/fonts/Tajawal-Bold.ttf",
        "font_black": "assets/fonts/Tajawal-Black.ttf",
    },
    "defaults": {
        "scene_duration": 4.0,
        "transition": {"type": "fade", "duration": 0.6},
        "motion": {"type": "zoom_in", "amount": 0.12},
        "text_animation": {"in": "slide_up", "out": "fade", "duration": 0.5},
    },
    "ducking": {"enabled": True, "threshold": 0.03, "ratio": 10, "attack_ms": 40, "release_ms": 600},
}


class ConfigError(Exception):
    """The configuration is unusable. `errors` lists every problem found."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("\n".join(f"- {e}" for e in errors))


def load_config(path: str | Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ConfigError([f"Configuration file not found: {path}"])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfigError([f"{path} is not valid JSON: {e.msg} (line {e.lineno}, column {e.colno})"])
    if not isinstance(data, dict):
        raise ConfigError([f"{path}: the top level must be a JSON object {{...}}"])
    return data


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (override or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _is_num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def expand_text(template: str, business: dict) -> tuple[str | None, list[str], list[str]]:
    """Fill {placeholders} from the business block.

    Returns (text, unknown_keys, empty_keys). text is None when a referenced
    value is unknown or empty, so that e.g. a phone line is dropped rather than
    rendered blank when no phone number was provided.
    """
    unknown, empty = [], []
    for key in PLACEHOLDER_RE.findall(template):
        if key not in business:
            unknown.append(key)
        elif business[key] is None or str(business[key]).strip() == "":
            empty.append(key)
    if unknown or empty:
        return None, unknown, empty
    return PLACEHOLDER_RE.sub(lambda m: str(business[m.group(1)]), template), [], []


def text_for_format(text: dict, fmt: str) -> dict:
    """Apply an optional per-format override block ("vertical": {...})."""
    out = {k: v for k, v in text.items() if k not in FORMATS}
    if isinstance(text.get(fmt), dict):
        out = _merge(out, text[fmt])
    return out


def normalize(raw: dict) -> dict:
    """Return a copy of the config with every default filled in."""
    cfg = copy.deepcopy(raw)
    cfg["business"] = cfg.get("business") or {}
    cfg["output"] = _merge(DEFAULTS["output"], cfg.get("output") or {})
    cfg["style"] = _merge(DEFAULTS["style"], cfg.get("style") or {})
    cfg["defaults"] = _merge(DEFAULTS["defaults"], cfg.get("defaults") or {})
    audio = cfg.get("audio") or {}
    audio["ducking"] = _merge(DEFAULTS["ducking"], audio.get("ducking") or {})
    for key in ("music", "voiceover"):
        if audio.get(key) and not audio[key].get("path"):
            audio[key] = None
    cfg["audio"] = audio
    d = cfg["defaults"]
    scenes = cfg.get("scenes") or []
    for i, sc in enumerate(scenes):
        sc.setdefault("id", f"scene{i + 1}")
        sc.setdefault("duration", d["scene_duration"])
        sc.setdefault("fit", "cover")
        sc.setdefault("dim", 0.0)
        sc["transition"] = _merge(d["transition"], sc.get("transition") or {})
        default_motion = d["motion"] if sc.get("type") == "image" else {"type": "none", "amount": 0.0}
        sc["motion"] = _merge(default_motion, sc.get("motion") or {})
        for t in sc.get("texts") or []:
            t["animation"] = _merge(d["text_animation"], t.get("animation") or {})
    cfg["scenes"] = scenes
    cfg.setdefault("project", "advertisement")
    cfg["output"].setdefault("basename", re.sub(r"[^A-Za-z0-9_-]+", "_", str(cfg["project"])).strip("_") or "ad")
    return cfg


def transition_duration(scene: dict, fps: int) -> float:
    tr = scene["transition"]
    return 1.0 / fps if tr["type"] == "cut" else float(tr["duration"])


def timeline(cfg: dict) -> tuple[list[float], float]:
    """Start time of every scene on the final timeline, and the total duration.

    Each scene overlaps the previous one by the duration of its transition.
    """
    fps = cfg["output"]["fps"]
    starts, t = [], 0.0
    for i, sc in enumerate(cfg["scenes"]):
        if i > 0:
            t -= transition_duration(sc, fps)
        starts.append(t)
        t += float(sc["duration"])
    return starts, t


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------

def _check_color(errors, where, value):
    if not isinstance(value, str) or not COLOR_RE.match(value):
        errors.append(f"{where}: colour must look like \"#RRGGBB\", got {value!r}")


def _check_text(errors, warnings, where, text, business, formats):
    if not isinstance(text, dict):
        errors.append(f"{where}: each text must be an object {{...}}")
        return
    if not isinstance(text.get("text"), str) or not text["text"].strip():
        errors.append(f"{where}: \"text\" is required and must be a non-empty string")
    else:
        _, unknown, empty = expand_text(text["text"], business)
        for key in unknown:
            errors.append(f"{where}: placeholder {{{key}}} is not defined in \"business\"")
        for key in empty:
            warnings.append(f"{where}: business.{key} is empty, so this text line will be skipped")
    for fmt in ["_base", *formats]:
        t = text if fmt == "_base" else text_for_format(text, fmt)
        w = where if fmt == "_base" else f"{where} ({fmt})"
        pos = t.get("position", "center")
        if isinstance(pos, str):
            if pos not in POSITIONS:
                errors.append(f"{w}: unknown position {pos!r}. Use one of {', '.join(POSITIONS)} or {{\"x\": 0.5, \"y\": 0.5}}")
        elif not (isinstance(pos, dict) and _is_num(pos.get("x")) and _is_num(pos.get("y"))
                  and 0 <= pos["x"] <= 1 and 0 <= pos["y"] <= 1):
            errors.append(f"{w}: position must be a name or {{\"x\": 0..1, \"y\": 0..1}}")
        if "size" in t and not (_is_num(t["size"]) and 8 <= t["size"] <= 400):
            errors.append(f"{w}: size must be a number between 8 and 400")
        if "max_width" in t and not (_is_num(t["max_width"]) and 0.1 <= t["max_width"] <= 1):
            errors.append(f"{w}: max_width must be between 0.1 and 1")
    if text.get("weight", "bold") not in WEIGHTS:
        errors.append(f"{where}: weight must be one of {', '.join(WEIGHTS)}")
    if text.get("align", "center") not in ("left", "center", "right"):
        errors.append(f"{where}: align must be left, center or right")
    if "color" in text:
        _check_color(errors, f"{where}.color", text["color"])
    box = text.get("box")
    if box is not None:
        if not isinstance(box, dict):
            errors.append(f"{where}.box must be an object")
        elif "color" in box:
            _check_color(errors, f"{where}.box.color", box["color"])
    anim = text.get("animation") or {}
    for side in ("in", "out"):
        if anim.get(side, "fade") not in ANIMATIONS:
            errors.append(f"{where}.animation.{side}: unknown animation {anim.get(side)!r}. Use one of {', '.join(ANIMATIONS)}")
    for key in ("start", "end"):
        if text.get(key) is not None and not (_is_num(text[key]) and text[key] >= 0):
            errors.append(f"{where}.{key} must be a number of seconds >= 0")
    if _is_num(text.get("start")) and _is_num(text.get("end")) and text["end"] <= text["start"]:
        errors.append(f"{where}: end must be greater than start")


def _check_media(errors, warnings, where, path, kind, need_seconds=None):
    p = Path(path)
    if not p.is_file():
        errors.append(f"{where}: file not found: {path}")
        return
    if kind == "image":
        try:
            from PIL import Image
            with Image.open(p) as im:
                im.verify()
        except Exception as e:  # Pillow raises many different types
            errors.append(f"{where}: {path} is not a readable image ({e})")
        return
    try:
        info = ffutil.probe(p)
    except ffutil.FFmpegError as e:
        errors.append(f"{where}: {e}")
        return
    if ffutil.stream_of(info, kind) is None:
        errors.append(f"{where}: {path} contains no {kind} stream")
    elif need_seconds and 0 < ffutil.duration_of(info) < need_seconds - 0.05:
        warnings.append(
            f"{where}: {path} lasts {ffutil.duration_of(info):.1f}s but the scene needs "
            f"{need_seconds:.1f}s; the last frame will be frozen"
        )


def validate(raw: dict, check_media: bool = True) -> tuple[list[str], list[str]]:
    """Check a raw config. Returns (errors, warnings); never raises."""
    errors: list[str] = []
    warnings: list[str] = []

    for key in ("business", "output", "style", "defaults", "audio"):
        if key in raw and raw[key] is not None and not isinstance(raw[key], dict):
            errors.append(f"\"{key}\" must be an object {{...}}")
    scenes = raw.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        errors.append("\"scenes\" is required and must be a non-empty list")
    elif not all(isinstance(s, dict) for s in scenes):
        errors.append("every entry of \"scenes\" must be an object {...}")
    if errors:
        return errors, warnings

    cfg = normalize(raw)
    business, out = cfg["business"], cfg["output"]

    if not str(business.get("name") or "").strip():
        errors.append("business.name is required")
    if not str(business.get("phone") or "").strip():
        warnings.append("business.phone is empty: no phone number will appear in the advertisement")

    formats = out["formats"]
    if not isinstance(formats, list) or not formats:
        errors.append("output.formats must be a non-empty list")
        formats = []
    for f in formats:
        if f not in FORMATS:
            errors.append(f"output.formats: unknown format {f!r}. Use {', '.join(FORMATS)}")
    formats = [f for f in formats if f in FORMATS]
    if not (isinstance(out["fps"], int) and 12 <= out["fps"] <= 60):
        errors.append("output.fps must be a whole number between 12 and 60")
        out["fps"] = 30
    if not (_is_num(out["crf"]) and 0 <= out["crf"] <= 40):
        errors.append("output.crf must be between 0 and 40 (18 is high quality)")

    style = cfg["style"]
    for key in ("text_color", "accent_color"):
        _check_color(errors, f"style.{key}", style[key])
    for key in ("font_regular", "font_bold", "font_black"):
        if not Path(style[key]).is_file():
            errors.append(f"style.{key}: font file not found: {style[key]}")

    seen_ids = set()
    for i, sc in enumerate(cfg["scenes"]):
        where = f"scenes[{i}] ({sc['id']})"
        if sc["id"] in seen_ids:
            errors.append(f"{where}: duplicate scene id")
        seen_ids.add(sc["id"])
        stype = sc.get("type")
        if stype not in SCENE_TYPES:
            errors.append(f"{where}: type must be one of {', '.join(SCENE_TYPES)}, got {stype!r}")
            continue
        dur = sc["duration"]
        if not (_is_num(dur) and 0.5 <= dur <= 120):
            errors.append(f"{where}: duration must be between 0.5 and 120 seconds")
            continue
        if sc["fit"] not in FITS:
            errors.append(f"{where}: fit must be cover or contain")
        if not (_is_num(sc["dim"]) and 0 <= sc["dim"] <= 0.95):
            errors.append(f"{where}: dim must be between 0 and 0.95")
        if sc["motion"].get("type") not in MOTIONS:
            errors.append(f"{where}: motion.type must be one of {', '.join(MOTIONS)}")
        amount = sc["motion"].get("amount", 0)
        if not (_is_num(amount) and 0 <= amount <= 0.5):
            errors.append(f"{where}: motion.amount must be between 0 and 0.5")
        tr = sc["transition"]
        if tr.get("type") not in TRANSITIONS:
            errors.append(f"{where}: transition.type {tr.get('type')!r} is unknown. Use one of {', '.join(TRANSITIONS)}")
        elif not (_is_num(tr.get("duration")) and 0 < tr["duration"] <= 3):
            errors.append(f"{where}: transition.duration must be between 0 and 3 seconds")
        elif i > 0 and tr["type"] != "cut":
            prev = cfg["scenes"][i - 1].get("duration")
            shortest = min(dur, prev) if _is_num(prev) else dur
            if tr["duration"] >= shortest / 2:
                errors.append(
                    f"{where}: transition ({tr['duration']}s) must be shorter than half of the "
                    f"shortest neighbouring scene ({shortest}s)"
                )
        if stype == "color":
            colors = sc.get("colors")
            if not (isinstance(colors, list) and 1 <= len(colors) <= 2):
                errors.append(f"{where}: a color scene needs \"colors\": [\"#RRGGBB\"] or two colours for a gradient")
            else:
                for c in colors:
                    _check_color(errors, f"{where}.colors", c)
        else:
            src = sc.get("source")
            if not isinstance(src, str) or not src:
                errors.append(f"{where}: \"source\" (path to the {stype} file) is required")
            else:
                if stype == "image" and Path(src).suffix.lower() not in IMAGE_EXT:
                    errors.append(f"{where}: {src} is not a supported image type ({', '.join(sorted(IMAGE_EXT))})")
                elif check_media:
                    _check_media(errors, warnings, where, src, stype, need_seconds=dur if stype == "video" else None)
            if stype == "video" and not (_is_num(sc.get("start", 0)) and sc.get("start", 0) >= 0):
                errors.append(f"{where}: start must be a number of seconds >= 0")
        texts = sc.get("texts") or []
        if not isinstance(texts, list):
            errors.append(f"{where}: texts must be a list")
            continue
        for j, t in enumerate(texts):
            _check_text(errors, warnings, f"{where}.texts[{j}]", t, business, formats)
            if isinstance(t, dict) and _is_num(t.get("start")) and t["start"] >= dur:
                errors.append(f"{where}.texts[{j}]: start ({t['start']}s) is after the end of the scene ({dur}s)")

    audio = cfg["audio"]
    for key in ("music", "voiceover"):
        item = audio.get(key)
        if item is None:
            continue
        if not isinstance(item, dict):
            errors.append(f"audio.{key} must be an object with a \"path\"")
            continue
        vol = item.get("volume", 1.0)
        if not (_is_num(vol) and 0 <= vol <= 4):
            errors.append(f"audio.{key}.volume must be between 0 and 4")
        if check_media:
            _check_media(errors, warnings, f"audio.{key}", item["path"], "audio")
    duck = audio["ducking"]
    if not (_is_num(duck["threshold"]) and 0.001 <= duck["threshold"] <= 1):
        errors.append("audio.ducking.threshold must be between 0.001 and 1")
    if not (_is_num(duck["ratio"]) and 1 <= duck["ratio"] <= 20):
        errors.append("audio.ducking.ratio must be between 1 and 20")
    if not audio.get("music") and not audio.get("voiceover"):
        warnings.append("no music and no voice-over configured: the video will have a silent audio track")

    if not errors:
        _, total = timeline(cfg)
        vo = audio.get("voiceover")
        if vo and check_media:
            try:
                vo_end = float(vo.get("start", 0)) + ffutil.duration_of(ffutil.probe(vo["path"]))
                if vo_end > total + 0.05:
                    warnings.append(
                        f"the voice-over ends at {vo_end:.1f}s but the video lasts {total:.1f}s; "
                        "the narration will be cut. Lengthen the scenes or shorten the recording"
                    )
            except ffutil.FFmpegError:
                pass
    return errors, warnings
