"""End-to-end tests: they really run FFmpeg and inspect the produced MP4 files."""

import math
import struct
import subprocess

import pytest
from PIL import Image

from conftest import needs_ffmpeg
from proads import cli, ffutil
from proads.config import load_config
from proads.render import frame_size, render

pytestmark = needs_ffmpeg
SCALE = 0.25  # 270x480 / 480x270: same code path as 1080p, a fraction of the time


def frame_at(video: str, seconds: float) -> Image.Image:
    info = ffutil.stream_of(ffutil.probe(video), "video")
    w, h = info["width"], info["height"]
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{seconds:.3f}", "-i", str(video), "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return Image.frombytes("RGB", (w, h), raw)


def band_rms(video: str, start: float, end: float, lowpass: int) -> float:
    """RMS level of the audio below `lowpass` Hz between two timestamps."""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ss", f"{start}", "-to", f"{end}",
         "-af", f"lowpass=f={lowpass},lowpass=f={lowpass},lowpass=f={lowpass}",
         "-ac", "1", "-ar", "8000", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    samples = struct.unpack(f"<{len(raw) // 2}h", raw)
    return math.sqrt(sum(s * s for s in samples) / len(samples))


def diff(a: Image.Image, b: Image.Image) -> float:
    pa, pb = a.convert("L").tobytes(), b.convert("L").tobytes()
    return sum(abs(x - y) for x, y in zip(pa, pb)) / len(pa)


def config(media: dict, **audio) -> dict:
    return {
        "project": "test_ad",
        "business": {"name": "Dream House Meuble", "phone": None, "price": "2950", "currency": "د.ت"},
        "output": {"formats": ["vertical", "horizontal"], "fps": 25, "fade_in": 0, "fade_out": 0},
        "audio": audio,
        "scenes": [
            {"id": "card", "type": "color", "colors": ["#C02040"], "duration": 2.0,
             "texts": [{"text": "{price} {currency}", "position": "center", "size": 160, "shadow": False,
                        "animation": {"in": "none"}, "start": 1.0}]},
            {"id": "photo", "type": "image", "source": media["photo"], "duration": 2.0,
             "motion": {"type": "zoom_in", "amount": 0.3}, "transition": {"type": "fade", "duration": 0.4},
             "texts": [{"text": "بيت نوم", "position": "bottom", "box": {"color": "#000000"},
                        "animation": {"in": "slide_up", "out": "fade"}, "start": 0.2, "end": 1.5},
                       {"text": "Tel {phone}", "position": "top"}]},
            {"id": "clip", "type": "video", "source": media["clip"], "duration": 4.0, "fit": "contain",
             "transition": {"type": "slideleft", "duration": 0.4},
             "texts": [{"text": "Livraison gratuite", "position": "upper", "animation": {"in": "zoom"}}]},
        ],
    }


@pytest.fixture(scope="module")
def rendered(media, tmp_path_factory):
    out = tmp_path_factory.mktemp("render")
    cfg = config(
        media,
        music={"path": media["music"], "volume": 0.8, "fade_in": 0, "fade_out": 0},
        voiceover={"path": media["voice"], "start": 3.0},
    )
    reports = render(cfg, out, scale=SCALE)
    return {r["format"]: r for r in reports}, out


def test_full_resolution_is_1080p():
    assert frame_size("vertical") == (1080, 1920)
    assert frame_size("horizontal") == (1920, 1080)


def test_outputs_are_h264_mp4_in_both_orientations(rendered):
    reports, out = rendered
    assert set(reports) == {"vertical", "horizontal"}
    for fmt, size in (("vertical", (270, 480)), ("horizontal", (480, 270))):
        info = ffutil.probe(reports[fmt]["file"])
        v, a = ffutil.stream_of(info, "video"), ffutil.stream_of(info, "audio")
        assert reports[fmt]["file"].endswith(".mp4")
        assert v["codec_name"] == "h264" and v["pix_fmt"] == "yuv420p"
        assert (v["width"], v["height"]) == size
        assert v["r_frame_rate"] == "25/1"
        assert a["codec_name"] == "aac"
        # 2 + 2 + 4 seconds, minus two 0.4 s transitions
        assert abs(ffutil.duration_of(info) - 7.2) < 0.15
    assert (out / "render_report.json").is_file()
    assert not (out / "work").exists(), "intermediate clips must be cleaned up"


def test_colours_are_accurate(rendered):
    r, g, b = frame_at(rendered[0]["vertical"]["file"], 0.4).getpixel((20, 20))
    assert abs(r - 0xC0) <= 8 and abs(g - 0x20) <= 8 and abs(b - 0x40) <= 8


def test_text_appears_at_its_start_time(rendered):
    video = rendered[0]["horizontal"]["file"]
    before, after = frame_at(video, 0.5), frame_at(video, 1.4)
    w, h = before.size
    centre = (w // 4, h // 3, 3 * w // 4, 2 * h // 3)
    whites = lambda im: sum(1 for v in im.crop(centre).convert('L').tobytes() if v > 215)
    assert whites(before) == 0
    assert whites(after) > 150


def test_image_scene_has_camera_motion(rendered):
    video = rendered[0]["vertical"]["file"]
    # photo scene runs from 1.6 s to 3.6 s; compare two moments in the text-free upper half
    a, b = frame_at(video, 2.2), frame_at(video, 3.0)
    top = (0, 0, a.width, a.height // 2)
    assert diff(a.crop(top), b.crop(top)) > 4


def test_transition_blends_two_scenes(rendered):
    video = rendered[0]["vertical"]["file"]
    r, g, b = frame_at(video, 1.8).getpixel((5, 5))  # middle of the card -> photo cross-fade
    card = (0xC0, 0x20, 0x40)
    assert max(abs(r - card[0]), abs(g - card[1]), abs(b - card[2])) > 12, "should no longer be the plain card"
    r0, g0, b0 = frame_at(video, 3.0).getpixel((5, 5))
    assert (abs(r - r0) + abs(g - g0) + abs(b - b0)) > 12, "should not yet be the plain photo"


def test_music_is_looped_and_ducked_under_the_voice(rendered):
    video = rendered[0]["vertical"]["file"]
    # music = 220 Hz tone (a 2 s file looped over 7.2 s); voice = 2 kHz tone from 3.0 s to 5.0 s
    alone_early = band_rms(video, 1.0, 2.5, 500)
    under_voice = band_rms(video, 3.6, 4.8, 500)
    alone_late = band_rms(video, 6.2, 7.0, 500)
    assert alone_early > 500, "music must be audible"
    assert alone_late > 0.6 * alone_early, "music must loop to the end and recover after the narration"
    assert under_voice < 0.5 * alone_early, "music must drop by at least 6 dB during narration"


def test_ducking_can_be_disabled(media, tmp_path):
    cfg = config(
        media,
        music={"path": media["music"], "volume": 0.8, "fade_in": 0, "fade_out": 0},
        voiceover={"path": media["voice"], "start": 3.0},
        ducking={"enabled": False},
    )
    cfg["output"]["formats"] = ["horizontal"]
    video = render(cfg, tmp_path, scale=SCALE)[0]["file"]
    assert band_rms(video, 3.6, 4.8, 500) > 0.85 * band_rms(video, 1.0, 2.5, 500)


def test_render_without_audio_still_has_an_audio_track(media, tmp_path):
    cfg = config(media)
    cfg["output"]["formats"] = ["vertical"]
    report = render(cfg, tmp_path, scale=SCALE)[0]
    assert report["audio_codec"] == "aac"


def test_ffmpeg_failures_are_reported_with_the_log(media, tmp_path):
    bad = tmp_path / "broken.mp4"
    bad.write_bytes(b"this is not a video")
    cfg = config(media)
    cfg["scenes"][2]["source"] = str(bad)
    with pytest.raises(Exception) as exc:
        render(cfg, tmp_path / "out", scale=SCALE)
    assert "broken.mp4" in str(exc.value)


def test_sample_advertisement_renders_end_to_end(tmp_path):
    """The shipped Dream House Meuble sample, placeholder media included."""
    assert cli.main(["render", "configs/dream_house_meuble.json", "-o", str(tmp_path), "--scale", str(SCALE)]) == 0
    cfg = load_config("configs/dream_house_meuble.json")
    for fmt, size in (("vertical", (270, 480)), ("horizontal", (480, 270))):
        path = tmp_path / f"dream_house_meuble_{fmt}_draft.mp4"
        info = ffutil.probe(path)
        v = ffutil.stream_of(info, "video")
        assert v["codec_name"] == "h264" and (v["width"], v["height"]) == size
        assert ffutil.stream_of(info, "audio") is not None
        assert 20 < ffutil.duration_of(info) < 40
        assert len(cfg["scenes"]) == 8
