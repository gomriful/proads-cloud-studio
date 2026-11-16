"""Generate self-contained placeholder media for the sample advertisement.

Everything here is synthetic (drawn or synthesised), so the first render
needs no customer photos, videos or recordings.
"""

from __future__ import annotations

import array
import logging
import math
import shutil
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from . import ffutil

log = logging.getLogger("proads")

SAMPLE_DIR = Path("assets/sample")
SIZE = 1600   # final placeholder image size (square works for 9:16 and 16:9)
SS = 2        # supersampling factor for smooth edges
RATE = 44100

NARRATION_AR = (
    "مرحبا بيكم في دريم هاوس موبل. "
    "بيوت نوم، صالونات، موبل تلفزة، وخزاين صبابط. "
    "العرض بألفين وتسعمية وخمسين دينار. "
    "والتوصيل بلاش لكامل تونس. "
    "تلقاونا في مدنين، سوق ليبيا."
)


# --------------------------------------------------------------------------
# Placeholder furniture illustrations
# --------------------------------------------------------------------------

class _Room:
    """A simple room (wall + floor) drawn in a 1000 x 1000 coordinate space."""

    def __init__(self, wall: str, wall2: str, floor: str):
        px = SIZE * SS
        self.k = px / 1000
        top = Image.new("RGB", (px, px), wall)
        bottom = Image.new("RGB", (px, px), wall2)
        self.img = Image.composite(bottom, top, Image.linear_gradient("L").resize((px, px)))
        self.d = ImageDraw.Draw(self.img)
        self.rect(0, 700, 1000, 1000, floor)
        self.rect(0, 692, 1000, 706, "#FFFFFF")  # skirting board
        for x in range(0, 1000, 125):            # floorboards
            self.rect(x, 706, x + 2, 1000, "#00000022")

    def _box(self, x0, y0, x1, y1):
        k = self.k
        return (round(x0 * k), round(y0 * k), round(x1 * k), round(y1 * k))

    def rect(self, x0, y0, x1, y1, fill, r=0):
        if len(fill) == 9:  # "#RRGGBBAA": blend a translucent shape
            layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
            ImageDraw.Draw(layer).rounded_rectangle(self._box(x0, y0, x1, y1), round(r * self.k), fill=fill)
            self.img.paste(layer, (0, 0), layer)
            self.d = ImageDraw.Draw(self.img)
        else:
            self.d.rounded_rectangle(self._box(x0, y0, x1, y1), round(r * self.k), fill=fill)

    def ellipse(self, x0, y0, x1, y1, fill):
        self.d.ellipse(self._box(x0, y0, x1, y1), fill=fill)

    def shadow(self, x0, x1, y=0):
        """Soft contact shadow on the floor under a piece of furniture."""
        layer = Image.new("RGBA", self.img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).ellipse(self._box(x0 - 30, y - 22, x1 + 30, y + 30), fill=(0, 0, 0, 90))
        layer = layer.filter(ImageFilter.GaussianBlur(14 * self.k))
        self.img.paste(layer, (0, 0), layer)
        self.d = ImageDraw.Draw(self.img)

    def frame(self, x0, y0, x1, y1, color):
        self.rect(x0, y0, x1, y1, "#FFFFFF", 4)
        self.rect(x0 + 12, y0 + 12, x1 - 12, y1 - 12, color, 2)

    def plant(self, x, y):
        for dx, dy, r in ((0, -70, 34), (-28, -45, 28), (28, -48, 30), (-10, -100, 26), (16, -92, 24)):
            self.ellipse(x + dx - r, y + dy - r, x + dx + r, y + dy + r, "#4F8A5B")
        self.rect(x - 26, y - 30, x + 26, y, "#C97B4A", 6)

    def finish(self) -> Image.Image:
        return self.img.resize((SIZE, SIZE), Image.LANCZOS)


def _bedroom() -> Image.Image:
    r = _Room("#EFE6DA", "#E2D3C0", "#B98B5E")
    r.frame(390, 150, 610, 300, "#C9B79C")
    r.shadow(170, 830, 850)
    r.rect(230, 330, 770, 640, "#2F5D62", 36)              # headboard
    r.rect(190, 600, 810, 800, "#F7F3EC", 26)              # mattress + duvet
    r.rect(190, 690, 810, 830, "#D9A441", 22)              # blanket
    r.rect(190, 810, 810, 850, "#6B4A2E", 10)              # bed base
    r.rect(270, 540, 480, 640, "#FFFFFF", 30)              # pillows
    r.rect(520, 540, 730, 640, "#FFFFFF", 30)
    for x0 in (60, 840):                                   # nightstands + lamps
        r.rect(x0, 660, x0 + 100, 850, "#6B4A2E", 8)
        r.rect(x0 + 10, 690, x0 + 90, 745, "#8A6240", 4)
        r.rect(x0 + 10, 765, x0 + 90, 820, "#8A6240", 4)
        r.rect(x0 + 44, 590, x0 + 56, 660, "#3A3A3A")
        r.rect(x0 + 18, 520, x0 + 82, 595, "#F4D58D", 10)
    return r.finish()


def _living_room() -> Image.Image:
    r = _Room("#E8ECEF", "#D5DCE2", "#A9805A")
    r.frame(250, 170, 450, 330, "#E07A5F")
    r.frame(490, 200, 620, 330, "#3D5A80")
    r.rect(120, 820, 880, 960, "#C8553D88", 20)            # rug
    r.shadow(150, 850, 815)
    r.rect(180, 430, 820, 700, "#3D5A80", 40)              # sofa back
    r.rect(130, 560, 240, 800, "#34506F", 34)              # arms
    r.rect(760, 560, 870, 800, "#34506F", 34)
    r.rect(220, 640, 780, 790, "#4A6C96", 26)              # seat
    r.rect(496, 640, 504, 790, "#34506F")
    r.rect(170, 790, 200, 825, "#3A2A1C", 4)               # legs
    r.rect(800, 790, 830, 825, "#3A2A1C", 4)
    r.rect(270, 530, 400, 650, "#F2CC8F", 24)              # cushions
    r.rect(610, 530, 740, 650, "#E07A5F", 24)
    r.shadow(360, 640, 925)
    r.rect(350, 850, 650, 880, "#6B4A2E", 8)               # coffee table
    r.rect(380, 880, 396, 930, "#3A2A1C")
    r.rect(604, 880, 620, 930, "#3A2A1C")
    r.plant(925, 850)
    return r.finish()


def _tv_cabinet() -> Image.Image:
    r = _Room("#ECE7E1", "#D8CFC4", "#8F6B4A")
    r.rect(150, 250, 850, 268, "#6B4A2E", 4)               # wall shelf
    r.plant(790, 250)
    r.rect(180, 205, 240, 250, "#E07A5F", 4)
    r.rect(250, 190, 290, 250, "#3D5A80", 4)
    r.shadow(140, 860, 850)
    r.rect(300, 330, 700, 580, "#1E1E24", 12)              # TV
    r.rect(314, 344, 686, 566, "#39424E", 6)
    r.rect(480, 580, 520, 640, "#1E1E24")
    r.rect(420, 632, 580, 646, "#1E1E24", 4)
    r.rect(130, 645, 870, 820, "#F7F3EC", 12)              # cabinet body
    r.rect(130, 645, 870, 665, "#6B4A2E", 6)               # wooden top
    for x0 in (150, 392, 634):                             # doors
        r.rect(x0, 685, x0 + 216, 800, "#E9E2D6", 6)
        r.rect(x0 + 96, 730, x0 + 120, 738, "#6B4A2E", 3)
    for x0 in (170, 800):                                  # legs
        r.rect(x0, 820, x0 + 26, 852, "#3A2A1C", 4)
    return r.finish()


def _shoe_cabinet() -> Image.Image:
    r = _Room("#F1ECE4", "#E0D6C8", "#A47C56")
    r.ellipse(590, 170, 810, 390, "#FFFFFF")               # round mirror
    r.ellipse(604, 184, 796, 376, "#C9DDE8")
    r.shadow(300, 700, 850)
    r.rect(320, 330, 680, 840, "#F7F3EC", 12)              # cabinet body
    r.rect(310, 320, 690, 345, "#6B4A2E", 6)               # wooden top
    for y0 in (365, 520, 675):                             # tilt-out drawers
        r.rect(340, y0, 660, y0 + 140, "#E9E2D6", 8)
        r.rect(455, y0 + 22, 545, y0 + 32, "#6B4A2E", 4)
    r.rect(335, 840, 360, 858, "#3A2A1C", 3)
    r.rect(640, 840, 665, 858, "#3A2A1C", 3)
    r.plant(400, 320)
    for x0, color in ((730, "#C8553D"), (800, "#3D5A80")):  # a pair of shoes on the floor
        r.rect(x0, 815, x0 + 60, 850, color, 14)
        r.rect(x0 + 30, 830, x0 + 95, 850, color, 10)
        r.rect(x0, 846, x0 + 95, 854, "#FFFFFF", 3)
    return r.finish()


ILLUSTRATIONS = {
    "bedroom.png": _bedroom,
    "living_room.png": _living_room,
    "tv_cabinet.png": _tv_cabinet,
    "shoe_cabinet.png": _shoe_cabinet,
}


def _showroom_video(images: list[Image.Image], path: Path, logs: Path) -> None:
    """A slow camera travel along the four products: a stand-in for a real clip."""
    w, h, fps, seconds = 1280, 720, 30, 6
    gap = 60
    strip = Image.new("RGB", (len(images) * (h + gap) + gap, h), "#2B2118")
    for i, im in enumerate(images):
        strip.paste(im.resize((h - 2 * gap, h - 2 * gap), Image.LANCZOS), (gap + i * (h + gap) + gap // 2, gap))
    n = fps * seconds
    travel = strip.width - w

    def frames():
        for i in range(n):
            x = travel * i / (n - 1)
            yield strip.transform((w, h), Image.AFFINE, (1, 0, x, 0, 1, 0), resample=Image.BICUBIC).tobytes()

    ffutil.run_ffmpeg(
        ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "pipe:0",
         "-vf", "scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
         "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", str(path)],
        logs / "sample_video.log", "sample showroom video", frames=frames(),
    )


# --------------------------------------------------------------------------
# Placeholder audio
# --------------------------------------------------------------------------

def _write_wav(path: Path, samples: list[float]) -> None:
    peak = max(1e-9, max(abs(s) for s in samples))
    pcm = array.array("h", (int(s / peak * 0.8 * 32767) for s in samples))
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(pcm.tobytes())


def _music(path: Path) -> None:
    """A 16-second seamless loop: warm pad chords with a light plucked arpeggio."""
    chords = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63), (261.63, 329.63, 392.00), (196.00, 246.94, 293.66)]
    bar = 4.0
    n_bar = int(bar * RATE)
    two_pi = 2 * math.pi
    out = [0.0] * (n_bar * len(chords))
    for c, chord in enumerate(chords):
        base = c * n_bar
        for i in range(n_bar):
            t = i / RATE
            env = min(1.0, t / 0.6, (bar - t) / 0.6)  # soft swell in and out of every chord
            pad = sum(math.sin(two_pi * f * t) + 0.35 * math.sin(two_pi * 2 * f * t) for f in chord)
            pad += 1.2 * math.sin(two_pi * chord[0] / 2 * t)  # bass
            step = int(t / 0.5)                               # eighth-note arpeggio
            lt = t - step * 0.5
            note = chord[step % 3] * 2
            pluck = math.exp(-lt * 7) * (math.sin(two_pi * note * lt) + 0.3 * math.sin(two_pi * 2 * note * lt))
            out[base + i] = 0.22 * env * pad + 0.5 * pluck
    _write_wav(path, out)


def _voice_fallback(path: Path) -> None:
    """Voice-like placeholder phrases (used when no speech synthesiser exists)."""
    phrases = [(0.0, 3.0), (4.2, 7.6), (9.0, 11.6), (13.0, 15.4), (16.8, 19.6)]
    total = phrases[-1][1] + 0.3
    out = [0.0] * int(total * RATE)
    two_pi = 2 * math.pi
    for start, end in phrases:
        for i in range(int(start * RATE), int(end * RATE)):
            t = i / RATE
            lt = t - start
            f0 = 135 + 18 * math.sin(two_pi * 0.7 * lt)                  # gentle intonation
            syll = 0.5 - 0.5 * math.cos(two_pi * 3.6 * lt)               # ~3.6 syllables / second
            edge = min(1.0, lt / 0.08, (end - t) / 0.08)
            tone = sum(math.sin(two_pi * f0 * h * t) / h for h in (1, 2, 3, 4, 5, 6))
            out[i] = tone * (0.25 + 0.75 * syll) * edge
    _write_wav(path, out)


def _voice(path: Path) -> str:
    """Placeholder narration: synthetic Arabic speech if espeak-ng exists, else voice-like tones."""
    exe = shutil.which("espeak-ng") or shutil.which("espeak")
    if exe:
        res = subprocess.run([exe, "-v", "ar", "-s", "135", "-w", str(path), NARRATION_AR], capture_output=True)
        if res.returncode == 0 and path.is_file() and path.stat().st_size > 2000:
            return "espeak-ng synthetic Arabic voice"
        log.warning("espeak-ng failed (%s); using the tone placeholder", res.stderr.decode(errors="replace").strip())
    _voice_fallback(path)
    return "voice-like tone placeholder (espeak-ng not installed)"


# --------------------------------------------------------------------------

def generate(target: Path = SAMPLE_DIR, force: bool = False) -> Path:
    """Create the placeholder media (skipped for files that already exist)."""
    target.mkdir(parents=True, exist_ok=True)
    logs = Path("output/logs")
    images = []
    for name, draw in ILLUSTRATIONS.items():
        path = target / name
        if force or not path.is_file():
            draw().save(path)
            log.info("sample: generated %s", path)
        images.append(Image.open(path).convert("RGB"))
    video = target / "showroom.mp4"
    if force or not video.is_file():
        _showroom_video(images, video, logs)
        log.info("sample: generated %s", video)
    music = target / "music.wav"
    if force or not music.is_file():
        _music(music)
        log.info("sample: generated %s", music)
    voice = target / "voiceover_placeholder.wav"
    if force or not voice.is_file():
        log.info("sample: generated %s (%s)", voice, _voice(voice))
    return target
