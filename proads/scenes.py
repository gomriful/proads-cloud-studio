"""Render one scene (image / video / colour card + animated text) to a clip."""

from __future__ import annotations

import logging
from pathlib import Path

from PIL import Image, ImageColor, ImageFilter, ImageOps

from . import ffutil
from .config import expand_text, text_for_format
from .textrender import render_text

log = logging.getLogger("proads")

# Visually lossless intermediate; the single "real" encode happens at assembly.
INTERMEDIATE = ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "10", "-pix_fmt", "yuv420p", "-an"]
TO_YUV = "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p"


# --------------------------------------------------------------------------
# Backgrounds
# --------------------------------------------------------------------------

def _gradient(size: tuple[int, int], colors: list[str]) -> Image.Image:
    top = Image.new("RGB", size, ImageColor.getrgb(colors[0]))
    if len(colors) == 1:
        return top
    bottom = Image.new("RGB", size, ImageColor.getrgb(colors[1]))
    mask = Image.linear_gradient("L").resize(size, Image.BICUBIC)
    return Image.composite(bottom, top, mask)


def _canvas(img: Image.Image, size: tuple[int, int], fit: str) -> Image.Image:
    """Fill `size` with the photo: cropped ('cover') or whole on a blurred copy ('contain')."""
    if fit == "cover":
        return ImageOps.fit(img, size, Image.LANCZOS, centering=(0.5, 0.5))
    small = ImageOps.fit(img, (size[0] // 8, size[1] // 8), Image.BILINEAR)
    bg = small.filter(ImageFilter.GaussianBlur(6)).resize(size, Image.BICUBIC)
    bg = Image.eval(bg, lambda v: int(v * 0.6))
    fg = ImageOps.contain(img, size, Image.LANCZOS)
    bg.paste(fg, ((size[0] - fg.width) // 2, (size[1] - fg.height) // 2))
    return bg


def ken_burns_frames(img: Image.Image, width: int, height: int, n: int, motion: dict, fit: str):
    """Yield n RGB24 frames of a smooth zoom / pan over a still image.

    The camera path is evaluated with sub-pixel precision for every frame
    (bicubic resampling), which avoids the jitter of integer-rounded zooms.
    """
    kind = motion.get("type", "none")
    amount = float(motion.get("amount", 0.0))
    if kind == "none" or amount <= 0:
        frame = _canvas(img, (width, height), fit).tobytes()
        for _ in range(n):
            yield frame
        return

    s = 1.0 + amount
    cw, ch = round(width * s), round(height * s)
    canvas = _canvas(img, (cw, ch), fit)
    for i in range(n):
        p = i / max(1, n - 1)
        if kind in ("zoom_in", "zoom_out"):
            z = 1.0 + amount * (p if kind == "zoom_in" else 1.0 - p)
            vw, vh = cw / z, ch / z
            x0, y0 = (cw - vw) / 2, (ch - vh) / 2
        else:
            vw, vh = cw / s, ch / s
            x0, y0 = (cw - vw) / 2, (ch - vh) / 2
            if kind == "pan_left":
                x0 = (cw - vw) * (1 - p)
            elif kind == "pan_right":
                x0 = (cw - vw) * p
            elif kind == "pan_up":
                y0 = (ch - vh) * (1 - p)
            elif kind == "pan_down":
                y0 = (ch - vh) * p
        frame = canvas.transform(
            (width, height), Image.AFFINE,
            (vw / width, 0, x0, 0, vh / height, y0),
            resample=Image.BICUBIC,
        )
        yield frame.tobytes()


def _load_image(path: str) -> Image.Image:
    with Image.open(path) as im:
        return ImageOps.exif_transpose(im).convert("RGB")


# --------------------------------------------------------------------------
# Text overlay filter graph
# --------------------------------------------------------------------------

def _overlay_filters(k: int, prev: str, out: str, layer_size, xy, spec: dict, dur: float, unit: float) -> list[str]:
    """ffmpeg filters that animate PNG input k over the stream `prev`."""
    anim = spec["animation"]
    a_in, a_out = anim.get("in", "fade"), anim.get("out", "fade")
    start = float(spec.get("start", 0.3))
    has_end = spec.get("end") is not None
    end = min(float(spec["end"]), dur) if has_end else dur
    d = max(0.05, min(float(anim.get("duration", 0.5)), (end - start) / 2))
    off = round(70 * unit)  # slide distance in pixels

    p_in = f"clip((t-{start:.3f})/{d:.3f},0,1)"
    ease_in = f"(1-pow(1-{p_in},3))"
    p_out = f"clip((t-{end - d:.3f})/{d:.3f},0,1)"
    ease_out = f"pow({p_out},3)"

    pre = ["format=rgba"]
    if a_in == "zoom":
        # "pop": grow from 60% with a small overshoot (ease-out-back)
        back = f"(1+2.70158*pow({p_in}-1,3)+1.70158*pow({p_in}-1,2))"
        factor = f"(0.6+0.4*{back})"
        pre.append(f"scale=w='max(2,trunc(iw*{factor}/2)*2)':h='max(2,trunc(ih*{factor}/2)*2)':eval=frame")
    if a_in != "none":
        pre.append(f"fade=t=in:st={start:.3f}:d={d * 0.8:.3f}:alpha=1")
    if has_end and a_out != "none":
        pre.append(f"fade=t=out:st={end - d:.3f}:d={d:.3f}:alpha=1")

    dx, dy = [], []
    slide = {"slide_up": (dy, 1), "slide_down": (dy, -1), "slide_left": (dx, 1), "slide_right": (dx, -1)}
    if a_in in slide:
        axis, sign = slide[a_in]
        axis.append(f"{sign * off}*(1-{ease_in})")
    if has_end and a_out in slide:
        axis, sign = slide[a_out]
        axis.append(f"{-sign * off}*{ease_out}")

    cx = xy[0] + layer_size[0] / 2
    cy = xy[1] + layer_size[1] / 2
    x_expr = "+".join([f"{cx:.1f}-w/2", *dx])
    y_expr = "+".join([f"{cy:.1f}-h/2", *dy])
    return [
        f"[{k}:v]{','.join(pre)}[t{k}]",
        f"[{prev}][t{k}]overlay=x='{x_expr}':y='{y_expr}':format=gbrp:eval=frame:"
        f"enable='between(t,{start:.3f},{end:.3f})'[{out}]",
    ]


# --------------------------------------------------------------------------
# Scene rendering
# --------------------------------------------------------------------------

def render_scene(scene: dict, fmt: str, width: int, height: int, cfg: dict, work: Path, logs: Path) -> Path:
    fps = cfg["output"]["fps"]
    n = max(1, round(float(scene["duration"]) * fps))
    dur = n / fps
    unit = min(width, height) / 1080.0
    tag = f"{fmt}_{scene['id']}"
    out = work / f"{tag}.mp4"

    # --- text layers -------------------------------------------------------
    layers = []
    for j, raw_text in enumerate(scene.get("texts") or []):
        spec = text_for_format(raw_text, fmt)
        if spec.get("hidden"):
            continue
        text, _, empty = expand_text(spec["text"], cfg["business"])
        if text is None:
            log.info("  %s: text %d skipped (business.%s is empty)", scene["id"], j, ", ".join(empty))
            continue
        if float(spec.get("start", 0.3)) >= dur:
            continue
        img, xy = render_text(spec, text, width, height, cfg["style"])
        png = work / f"{tag}_text{j}.png"
        img.save(png)
        layers.append((png, img.size, xy, spec))

    # --- base video --------------------------------------------------------
    stype = scene["type"]
    frames = None
    if stype == "video":
        inputs = ["-ss", f"{float(scene.get('start', 0)):.3f}", "-i", scene["source"]]
        if scene["fit"] == "contain":
            base = (
                f"[0:v]fps={fps},split[bga][fga];"
                f"[bga]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
                f"boxblur=24:2,eq=brightness=-0.15[bg];"
                f"[fga]scale={width}:{height}:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2,"
            )
        else:
            base = f"[0:v]fps={fps},scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},"
        base += f"setsar=1,tpad=stop_mode=clone:stop_duration={dur:.3f},trim=duration={dur:.3f},setpts=PTS-STARTPTS,"
    else:
        inputs = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps), "-i", "pipe:0"]
        if stype == "image":
            frames = ken_burns_frames(_load_image(scene["source"]), width, height, n, scene["motion"], scene["fit"])
        else:
            frame = _gradient((width, height), scene["colors"]).tobytes()
            frames = (frame for _ in range(n))
        base = "[0:v]"
    if scene["dim"] > 0:
        base += f"drawbox=x=0:y=0:w=iw:h=ih:color=black@{scene['dim']:.3f}:t=fill,"
    graph = [base + "format=gbrp[b0]"]

    for k, (png, size, xy, spec) in enumerate(layers, start=1):
        inputs += ["-loop", "1", "-framerate", str(fps), "-t", f"{dur:.3f}", "-i", str(png)]
        graph += _overlay_filters(k, f"b{k - 1}", f"b{k}", size, xy, spec, dur, unit)
    graph.append(f"[b{len(layers)}]{TO_YUV}[vout]")

    args = [
        *inputs, "-filter_complex", ";".join(graph), "-map", "[vout]",
        "-frames:v", str(n), "-r", str(fps), *INTERMEDIATE,
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(out),
    ]
    ffutil.run_ffmpeg(args, logs / f"scene_{tag}.log", f"scene '{scene['id']}' ({fmt})", frames=frames)
    return out
