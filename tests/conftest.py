import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAVE_FFMPEG, reason="ffmpeg/ffprobe not installed")


@pytest.fixture(autouse=True)
def _repo_root(monkeypatch):
    """Config paths (fonts, sample media) are relative to the repository root."""
    monkeypatch.chdir(ROOT)


def write_tone(path: Path, freq: float, seconds: float, start: float = 0.0, end: float | None = None, amp: float = 0.5):
    """Mono 16-bit WAV: a sine that is only audible between start and end."""
    rate = 44100
    end = seconds if end is None else end
    frames = bytearray()
    for i in range(int(seconds * rate)):
        t = i / rate
        v = amp * math.sin(2 * math.pi * freq * t) if start <= t < end else 0.0
        frames += struct.pack("<h", int(v * 32767))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(frames))


@pytest.fixture(scope="session")
def media(tmp_path_factory) -> dict:
    """Tiny synthetic photo, clip, music and narration used by the render tests."""
    d = tmp_path_factory.mktemp("media")
    photo = Image.new("RGB", (800, 600), "#335577")
    draw = ImageDraw.Draw(photo)
    for i in range(0, 800, 40):  # detail, so camera motion is measurable
        draw.rectangle((i, 0, i + 18, 600), fill=(60 + i % 160, 120, 200 - i % 150))
    draw.ellipse((300, 200, 500, 400), fill="#FFCC00")
    photo.save(d / "photo.jpg", quality=92)

    out = {"photo": str(d / "photo.jpg"), "clip": str(d / "clip.mp4"),
           "music": str(d / "music.wav"), "voice": str(d / "voice.wav")}
    if HAVE_FFMPEG:
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=3",
             "-pix_fmt", "yuv420p", out["clip"]], check=True)
    write_tone(d / "music.wav", 220, 2.0)                     # short: must be looped by the engine
    write_tone(d / "voice.wav", 2000, 2.0)                    # 2 s of "speech"
    return out
