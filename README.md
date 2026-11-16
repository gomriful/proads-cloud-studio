# ProAds Cloud Studio

A cloud advertising video editor. You describe an advertisement in one JSON
file, press **Run workflow** on GitHub, and a GitHub-hosted runner renders a
1080p H.264 MP4 that you download to your phone.

Nothing is installed on your own device. Everything runs on GitHub Actions.

> **بالعربية — البداية السريعة**
> 1. افتح المستودع في Safari ثم **Actions** ← **Render Advertisement** ← **Run workflow**.
> 2. انتظر حتى تظهر العلامة الخضراء (دقيقتان إلى أربع دقائق تقريبًا).
> 3. افتح التشغيل، وانزل إلى **Artifacts**، ونزّل الملف، ثم افتحه من تطبيق «الملفات».
> 4. لتغيير النصوص أو السعر أو الصور عدّل الملف `configs/dream_house_meuble.json`.

## What it does

| Feature | Details |
|---|---|
| Automatic assembly | Photos, video clips and colour cards are joined in the order you list them |
| Transitions | 24 styles (fade, smooth slides, wipes, circle, zoom, ...) with configurable length |
| Cinematic photos | Smooth sub-pixel zoom and pan (Ken Burns) on every image |
| Animated text | Fade, slide (4 directions) and "pop" zoom; boxes, outlines and shadows |
| Arabic + French | Correct right-to-left Arabic shaping, French accents, mixed lines such as `2950 د.ت` |
| Audio | Voice-over + background music, music looped to the video length |
| Auto ducking | Music is lowered automatically while the narration speaks |
| Formats | Vertical 9:16 (1080x1920), horizontal 16:9 (1920x1080), square 1:1 |
| Output | MP4, H.264 High profile, yuv420p, AAC 48 kHz, fast-start for social media |
| Business info | Name, price, phone, address, offers: written once, reused in any scene |

## Run your first video from an iPhone

The sample advertisement (**Dream House Meuble**) needs no uploads: its
pictures, clip, music and narration are placeholders generated during the run.

1. Open the repository in **Safari** (sign in to github.com).
2. Tap **Actions**. If you do not see it, swipe the tab bar sideways.
3. Tap **Render Advertisement** in the list of workflows.
4. Tap **Run workflow**, keep the default values, tap the green **Run workflow** button.
5. Refresh after a few seconds and tap the new run. It takes about 2 to 4 minutes.
6. When the run shows a green tick, scroll to **Artifacts** and tap `advertisement-N`.
7. Safari downloads a ZIP. Open the **Files** app, go to **Downloads**, tap the ZIP to
   unpack it, open the MP4, then **Share → Save Video** to put it in Photos.

The GitHub mobile app can also start the workflow (repository → Actions →
Render Advertisement → Run workflow), but artifacts download most reliably in Safari.

> The **Run workflow** button only appears once the workflow file is on the
> default branch (`main`). Merge the pull request first.

### The three options of the Run workflow form

| Option | Meaning |
|---|---|
| **config** | Path of the JSON file to render, for example `configs/dream_house_meuble.json` |
| **format** | `config` (formats listed in the file), `both`, `vertical`, `horizontal` or `square` |
| **quality** | `final` = 1080p. `draft` = half size, much faster, for checking texts and timing |

## Make an advertisement with your own media

### 1. Upload photos, clips and audio

1. In Safari open the repository, then the `media` folder.
2. Tap **Add file → Upload files**, then **choose your files** and pick from Photo
   Library or Files.
3. Tap **Commit changes**.

Use simple file names without spaces (`bedroom.jpg`, not `IMG 0042.HEIC`).
Browser uploads are limited to 25 MB per file. Supported: JPG, PNG, WEBP, HEIC
photos; MP4 and MOV video; MP3, M4A and WAV audio.

Record the voice-over with the iPhone **Voice Memos** app, share it to Files,
and upload the `.m4a` the same way.

### 2. Edit the configuration

Open `configs/dream_house_meuble.json`, tap the pencil icon, change it, and tap
**Commit changes**. To keep the sample intact, create a copy instead: **Add file
→ Create new file**, name it `configs/my_ad.json`, and paste the content.

When you use your own media:

- set `"generate_sample_assets": false`
- point every `"source"` and audio `"path"` to your files, e.g. `"media/bedroom.jpg"`
- set `"voiceover"` to `null` if you have no recording (remove the placeholder voice)

The quickest way from a phone is to ask Claude Code in plain language, e.g.
*"change the price to 3200 and replace the bedroom photo with media/bed2.jpg"*.

### 3. Render

Run the workflow again and type your file path in **config**.

## Configuration reference

All paths are relative to the repository root. Sizes are designed for a
1080-pixel frame and scale automatically for every format.

```jsonc
{
  "project": "dream_house_meuble",       // used for the output file name
  "generate_sample_assets": true,        // true only for the built-in sample

  "business": {                          // any key here can be used as {key} in texts
    "name": "Dream House Meuble",
    "phone": null,                       // empty: every text using {phone} is skipped
    "address": "مدنين - سوق ليبيا",
    "price": "2950",
    "currency": "د.ت"
  },

  "output": {
    "formats": ["vertical", "horizontal"],
    "fps": 30,
    "crf": 18,                           // quality: lower = better and bigger (16 to 23)
    "preset": "medium",
    "fade_in": 0.4, "fade_out": 0.6      // fade from / to black, in seconds
  },

  "style": {
    "text_color": "#FFFFFF",
    "accent_color": "#F2B134"            // default colour of text boxes
  },

  "audio": {
    "music":     { "path": "media/music.mp3", "volume": 0.55, "fade_in": 1.0, "fade_out": 2.0, "loop": true },
    "voiceover": { "path": "media/voice.m4a", "start": 1.0, "volume": 1.0 },
    "ducking":   { "enabled": true, "threshold": 0.03, "ratio": 10, "attack_ms": 40, "release_ms": 600 }
  },

  "defaults": {
    "scene_duration": 4.0,
    "transition": { "type": "fade", "duration": 0.6 }
  },

  "scenes": [ /* see below */ ]
}
```

### Scenes

| Key | Values | Notes |
|---|---|---|
| `type` | `image`, `video`, `color` | |
| `source` | file path | for `image` and `video` |
| `colors` | `["#RRGGBB"]` or two colours | for `color` (two = vertical gradient) |
| `duration` | seconds | time on screen, including the transitions at both ends |
| `fit` | `cover` (default), `contain` | `cover` fills the frame and crops; `contain` shows the whole picture over a blurred copy of itself |
| `motion` | `{ "type": ..., "amount": 0.12 }` | images only: `zoom_in`, `zoom_out`, `pan_left`, `pan_right`, `pan_up`, `pan_down`, `none` |
| `dim` | `0` to `0.95` | darkens the background so text is readable |
| `start` | seconds | video only: where to start inside the clip |
| `transition` | `{ "type": ..., "duration": 0.6 }` | how **this** scene arrives; ignored on the first scene |
| `texts` | list | see below |

Transitions: `cut`, `fade`, `fadeblack`, `fadewhite`, `dissolve`, `slideleft`,
`slideright`, `slideup`, `slidedown`, `wipeleft`, `wiperight`, `wipeup`,
`wipedown`, `smoothleft`, `smoothright`, `smoothup`, `smoothdown`, `circleopen`,
`circleclose`, `radial`, `zoomin`, `pixelize`, `hblur`, `distance`.

Total length = sum of scene durations minus the transition durations.

### Texts

| Key | Values | Notes |
|---|---|---|
| `text` | string | Arabic, French or mixed; `{name}`, `{price}`... are filled from `business`; `\n` forces a new line |
| `position` | `top`, `upper`, `center`, `lower`, `bottom`, corners, or `{ "x": 0.5, "y": 0.4 }` | centre of the text, as a fraction of the frame |
| `size` | number (default 64) | long lines wrap automatically |
| `weight` | `regular`, `bold`, `black` | |
| `color` | `#RRGGBB` | |
| `box` | `{ "color": "#F2B134", "opacity": 1, "padding": 26, "radius": 22 }` | coloured label behind the text |
| `stroke` | `{ "color": "#000000", "width": 4 }` | outline |
| `shadow` | `true` / `false` | |
| `align` | `center`, `left`, `right` | for multi-line text |
| `max_width` | `0.1` to `1` (default 0.86) | fraction of the frame width |
| `start`, `end` | seconds inside the scene | without `end` the text stays until the scene ends |
| `animation` | `{ "in": "slide_up", "out": "fade", "duration": 0.5 }` | `none`, `fade`, `slide_up`, `slide_down`, `slide_left`, `slide_right`, `zoom`; `out` is used only when `end` is set |
| `vertical`, `horizontal`, `square` | object | overrides for one format, e.g. `"horizontal": { "size": 120 }`; `"hidden": true` hides the text there |

## When something goes wrong

The run page shows a red cross and the reason:

- **Configuration errors** are listed one by one at the top of the run page, in
  plain language, for example
  `scenes[2] (living_room): file not found: media/salon.jpg`.
- **FFmpeg errors** show the failing step, the exact command and the last lines
  of FFmpeg output. Complete logs are attached as the `render-logs-N` artifact.

| Message | Fix |
|---|---|
| `is not valid JSON ... line 12` | A comma or quote is missing near that line |
| `file not found` | The path differs from the uploaded file name (capitals matter) |
| `transition must be shorter than half of ...` | Shorten the transition or lengthen the scene |
| `the voice-over ends at ...` (warning) | The recording is longer than the video: add or lengthen scenes |
| `business.phone is empty` (warning) | Expected until you add a phone number |

## Project layout

```
configs/                 advertisement descriptions (JSON)
media/                   your uploaded photos, clips and audio
assets/fonts/            Tajawal (Arabic + Latin), SIL Open Font License
proads/                  the engine
  config.py              defaults, validation, timeline
  textrender.py          Arabic / French text to transparent layers
  scenes.py              one scene: background, camera motion, animated text
  render.py              transitions, audio mix and ducking, final encode, checks
  sample.py              placeholder pictures, clip, music and narration
  cli.py                 command line
tests/                   automated tests (they run real FFmpeg renders)
.github/workflows/
  render.yml             "Render Advertisement" (manual button)
  ci.yml                 "Tests": runs on every pull request, also renders the sample
```

Command line, for reference (this is what the workflow runs):

```
python -m proads validate configs/dream_house_meuble.json
python -m proads render   configs/dream_house_meuble.json --format both [--draft]
python -m pytest
```

## Good to know

- **The sample narration is a placeholder.** It is a synthetic voice (or plain
  tones) that only exists to demonstrate mixing and ducking. Replace it with a
  real recording, or set `"voiceover": null`.
- **The sample pictures are drawings**, not product photos.
- **No phone number is included** in the sample because none was provided. Add
  it in `business.phone` and it appears on the last scene automatically.
- The sound of video clips is muted; audio comes from the music and voice-over.
- iPhone HDR video can look washed out. Record in standard dynamic range
  (Settings → Camera → Record Video → turn HDR Video off) for accurate colour.
- GitHub keeps artifacts for 30 days. Save the videos you want to keep.
- GitHub Actions is free for public repositories; private repositories on the
  free plan include a monthly quota of minutes. A sample render uses about 3.
- Only use music you have the right to use in advertising.
