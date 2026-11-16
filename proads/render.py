"""Orchestration: scenes -> transitions -> audio mix -> final MP4 -> verification."""

from __future__ import annotations

import json
import logging
import os
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import ffutil
from .config import FORMATS, ConfigError, normalize, timeline, transition_duration, validate
from .scenes import render_scene

log = logging.getLogger("proads")

SAMPLE_RATE = 48000
_AFORMAT = f"aresample={SAMPLE_RATE},aformat=sample_fmts=fltp:channel_layouts=stereo"


def frame_size(fmt: str, scale: float = 1.0) -> tuple[int, int]:
    w, h = FORMATS[fmt]
    return max(2, round(w * scale / 2) * 2), max(2, round(h * scale / 2) * 2)


def audio_graph(audio: dict, first_input: int, total: float) -> tuple[list[str], list[str]]:
    """Build the ffmpeg inputs and filters that produce the [aout] stream.

    Music is looped to the length of the video and automatically lowered
    ("ducked") by a side-chain compressor whenever the narration is speaking.
    """
    music, voice, duck = audio.get("music"), audio.get("voiceover"), audio["ducking"]
    inputs: list[str] = []
    graph: list[str] = []
    idx = first_input

    if music:
        if music.get("loop", True):
            inputs += ["-stream_loop", "-1"]
        inputs += ["-i", music["path"]]
        fade_in = float(music.get("fade_in", 0.8))
        fade_out = min(float(music.get("fade_out", 1.5)), total / 2)
        graph.append(
            f"[{idx}:a]{_AFORMAT},volume={float(music.get('volume', 0.6)):.3f},apad,atrim=0:{total:.3f},"
            f"afade=t=in:st=0:d={fade_in:.3f},afade=t=out:st={total - fade_out:.3f}:d={fade_out:.3f}[mus]"
        )
        idx += 1
    if voice:
        inputs += ["-i", voice["path"]]
        delay = round(float(voice.get("start", 0.0)) * 1000)
        graph.append(
            f"[{idx}:a]{_AFORMAT},volume={float(voice.get('volume', 1.0)):.3f},"
            f"adelay={delay}:all=1,apad,atrim=0:{total:.3f}[vo]"
        )
        idx += 1

    limiter = "alimiter=limit=0.95:level=disabled"
    if music and voice:
        if duck["enabled"]:
            graph.append("[vo]asplit=2[vo_mix][vo_key]")
            graph.append(
                f"[mus][vo_key]sidechaincompress=threshold={duck['threshold']}:ratio={duck['ratio']}:"
                f"attack={duck['attack_ms']}:release={duck['release_ms']}[mus_ducked]"
            )
            graph.append(f"[mus_ducked][vo_mix]amix=inputs=2:normalize=0:duration=first,{limiter}[aout]")
        else:
            graph.append(f"[mus][vo]amix=inputs=2:normalize=0:duration=first,{limiter}[aout]")
    elif music or voice:
        graph.append(f"[{'mus' if music else 'vo'}]{limiter}[aout]")
    else:
        graph.append(f"anullsrc=r={SAMPLE_RATE}:cl=stereo,atrim=0:{total:.3f}[aout]")
    return inputs, graph


def assemble(cfg: dict, clips: list[Path], out_path: Path, logs: Path, fmt: str) -> None:
    out = cfg["output"]
    fps = out["fps"]
    starts, total = timeline(cfg)
    # scene clips are frame-aligned, so snap the total to whole frames too
    total = round(total * fps) / fps

    inputs: list[str] = []
    for clip in clips:
        inputs += ["-i", str(clip)]

    graph: list[str] = []
    last = "0:v"
    for i in range(1, len(clips)):
        sc = cfg["scenes"][i]
        kind = sc["transition"]["type"]
        graph.append(
            f"[{last}][{i}:v]xfade=transition={'fade' if kind == 'cut' else kind}:"
            f"duration={transition_duration(sc, fps):.4f}:offset={starts[i]:.4f}[x{i}]"
        )
        last = f"x{i}"
    fades = []
    if out["fade_in"] > 0:
        fades.append(f"fade=t=in:st=0:d={out['fade_in']:.3f}")
    if out["fade_out"] > 0:
        fades.append(f"fade=t=out:st={total - out['fade_out']:.3f}:d={out['fade_out']:.3f}")
    graph.append(f"[{last}]{','.join([*fades, 'format=yuv420p'])}[vout]")

    a_inputs, a_graph = audio_graph(cfg["audio"], len(clips), total)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    args = [
        *inputs, *a_inputs,
        "-filter_complex", ";".join(graph + a_graph),
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", str(out["preset"]), "-crf", str(out["crf"]),
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(fps),
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", str(SAMPLE_RATE),
        "-t", f"{total:.3f}", "-movflags", "+faststart", str(out_path),
    ]
    ffutil.run_ffmpeg(args, logs / f"assemble_{fmt}.log", f"final assembly ({fmt})")


def verify(path: Path, width: int, height: int, expected_duration: float) -> dict:
    """Check the rendered file really is what was asked for; raise otherwise."""
    info = ffutil.probe(path)
    v, a = ffutil.stream_of(info, "video"), ffutil.stream_of(info, "audio")
    problems = []
    if v is None:
        problems.append("no video stream")
    else:
        if v.get("codec_name") != "h264":
            problems.append(f"video codec is {v.get('codec_name')}, expected h264")
        if (v.get("width"), v.get("height")) != (width, height):
            problems.append(f"size is {v.get('width')}x{v.get('height')}, expected {width}x{height}")
        if v.get("pix_fmt") != "yuv420p":
            problems.append(f"pixel format is {v.get('pix_fmt')}, expected yuv420p")
    if a is None:
        problems.append("no audio stream")
    duration = ffutil.duration_of(info)
    if abs(duration - expected_duration) > 0.25:
        problems.append(f"duration is {duration:.2f}s, expected {expected_duration:.2f}s")
    if problems:
        raise ffutil.FFmpegError(f"Output check failed for {path}: " + "; ".join(problems))
    return {
        "file": str(path),
        "width": width, "height": height,
        "duration_seconds": round(duration, 2),
        "size_mb": round(path.stat().st_size / 1e6, 2),
        "video_codec": v["codec_name"], "audio_codec": a.get("codec_name"),
        "fps": v.get("r_frame_rate"),
    }


def render(raw: dict, out_dir: str | Path = "output", formats: list[str] | None = None,
           scale: float = 1.0, keep_work: bool = False) -> list[dict]:
    """Validate and render every requested format. Returns one report per file."""
    ffutil.require_binaries()
    errors, warnings = validate(raw)
    for w in warnings:
        log.warning("%s", w)
    if errors:
        raise ConfigError(errors)

    cfg = normalize(raw)
    if scale != 1.0:  # draft renders trade quality for speed
        cfg["output"]["preset"] = "veryfast"
    formats = formats or cfg["output"]["formats"]
    unknown = [f for f in formats if f not in FORMATS]
    if unknown:
        raise ConfigError([f"unknown format(s): {', '.join(unknown)}. Use {', '.join(FORMATS)}"])

    out_dir = Path(out_dir)
    logs = out_dir / "logs"
    work = out_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    _, total = timeline(cfg)
    total = round(total * cfg["output"]["fps"]) / cfg["output"]["fps"]
    workers = max(1, min(4, os.cpu_count() or 2))
    reports = []

    for fmt in formats:
        width, height = frame_size(fmt, scale)
        t0 = time.time()
        log.info("Rendering %s %dx%d, %d scenes, %.1fs", fmt, width, height, len(cfg["scenes"]), total)

        def one(scene, fmt=fmt, width=width, height=height):
            t = time.time()
            clip = render_scene(scene, fmt, width, height, cfg, work, logs)
            log.info("  scene %-14s done in %.1fs", scene["id"], time.time() - t)
            return clip

        with ThreadPoolExecutor(max_workers=workers) as pool:
            clips = list(pool.map(one, cfg["scenes"]))

        suffix = "" if scale == 1.0 else "_draft"
        out_path = out_dir / f"{cfg['output']['basename']}_{fmt}{suffix}.mp4"
        log.info("  assembling transitions + audio")
        assemble(cfg, clips, out_path, logs, fmt)
        report = verify(out_path, width, height, total)
        report["format"] = fmt
        report["render_seconds"] = round(time.time() - t0, 1)
        reports.append(report)
        log.info("  OK %s (%.1f MB, %.1fs)", out_path, report["size_mb"], report["duration_seconds"])

    (out_dir / "render_report.json").write_text(
        json.dumps({"project": cfg["project"], "outputs": reports, "warnings": warnings}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    if not keep_work:
        shutil.rmtree(work, ignore_errors=True)
    return reports
