"""Thin wrappers around the ffmpeg / ffprobe binaries with useful error logs."""

from __future__ import annotations

import json
import logging
import shlex
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("proads")


class FFmpegError(RuntimeError):
    """ffmpeg/ffprobe failed. The message carries the command and stderr tail."""


def require_binaries() -> None:
    missing = [b for b in ("ffmpeg", "ffprobe") if shutil.which(b) is None]
    if missing:
        raise FFmpegError(
            f"Required program(s) not found on PATH: {', '.join(missing)}. "
            "On GitHub Actions they are installed by the workflow (apt-get install ffmpeg)."
        )


def _tail(path: Path, lines: int = 40) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "(no log available)"
    return "\n".join(text.splitlines()[-lines:])


def _fail(step: str, cmd: list[str], code: int, log_path: Path) -> FFmpegError:
    return FFmpegError(
        f"ffmpeg failed during '{step}' (exit code {code}).\n"
        f"Command: {shlex.join(cmd)}\n"
        f"Full log: {log_path}\n"
        f"--- last lines of ffmpeg output ---\n{_tail(log_path)}"
    )


def run_ffmpeg(args: list[str], log_path: Path, step: str, frames=None) -> None:
    """Run ffmpeg. `frames`, if given, is an iterable of raw bytes written to stdin."""
    cmd = ["ffmpeg", "-hide_banner", "-y", *([] if frames is not None else ["-nostdin"]), *args]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log.debug("ffmpeg [%s]: %s", step, shlex.join(cmd))
    with open(log_path, "w", encoding="utf-8") as logf:
        logf.write(shlex.join(cmd) + "\n\n")
        logf.flush()
        if frames is None:
            code = subprocess.run(cmd, stdout=logf, stderr=subprocess.STDOUT).returncode
        else:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=logf, stderr=subprocess.STDOUT)
            try:
                for chunk in frames:
                    proc.stdin.write(chunk)
                proc.stdin.close()
            except BrokenPipeError:
                pass  # ffmpeg died early; the exit code + log below explain why
            code = proc.wait()
    if code != 0:
        raise _fail(step, cmd, code, log_path)


def probe(path: str | Path) -> dict:
    """Return ffprobe's JSON description (format + streams) of a media file."""
    cmd = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise FFmpegError(f"ffprobe could not read '{path}': {res.stderr.strip() or 'unknown error'}")
    return json.loads(res.stdout)


def stream_of(info: dict, kind: str) -> dict | None:
    for s in info.get("streams", []):
        if s.get("codec_type") == kind:
            return s
    return None


def duration_of(info: dict) -> float:
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError, TypeError):
        return 0.0
