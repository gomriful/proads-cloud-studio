---
name: motion-explainer
description: End-to-end pipeline for short motion-graphics explainer videos (Shorts/Reels/YouTube) narrated by an external TTS voice. Phase 0 runs a short "grill" interview that turns a vague idea into an approved brief. Phase 1 writes an Arabic (or any language) voiceover script formatted for an expressive TTS tool such as Gemini TTS (style field + inline vocal tags). Phase 2 takes the uploaded voiceover and renders a real MP4, with animation beats synced to the speech pauses, a reusable component library, ready themes, a fast proxy for timing approval, and synthesized sound effects. Use this skill whenever the user wants a motion graphics video, animated explainer, short/reel from a voiceover, a "script for a TTS tool", asks for a video topic or idea, or uploads a voiceover and asks for a video, even if they don't say "motion graphics".
---

# Motion Explainer

Phases: **0 Brief → 1 Script → 2 Video**, usually across several turns. Reply in the user's language (often Arabic), short, result first.

## Environment (check once, then adapt)
- **claude.ai (container):** uploads are in `/mnt/user-data/uploads/`, deliverables go to `/mnt/user-data/outputs/`, and the work dir is `/home/claude/mx/`. There's **no network** (Google Fonts won't load; ask the user to upload font files). **Background processes die when a tool call ends**, so never `nohup`; render in foreground chunks of ~650 frames. Playwright+Chromium, ffmpeg, numpy, scipy and Pillow are preinstalled.
- **Claude Code / local machine:** work in a folder the user chooses, and use their file paths. If something is missing: `pip install -r requirements.txt && python -m playwright install chromium`, plus ffmpeg from the OS package manager. Rendering can run in one call (`render_frames.py index.html frames 0 999999`). Fonts can be any installed family.
- **Everywhere:** you cannot hear the audio. Timing comes from waveform pauses aligned to text lengths (`scripts/analyze_audio.py`). It is tag-aware, but still an estimate. Say so, and offer to shift any scene the user flags.

Below, `<uploads>` and `<outputs>` mean the paths for the current environment.

## Phase 0: brief interview (grill)
Read `references/brief_interview.md`. In short:
- One question per message, each with a recommended answer. Skip anything already known.
- At most 7 decisions. "كمّل" or "use defaults" ends the interview immediately.
- Challenge weak answers once (no angle, nothing drawable, unverifiable claims, risky dialect).
- End with a brief that separates **facts / decisions / assumptions / risks**, and wait for approval.

If the user already gave a complete brief, or asks you to choose everything, skip the questions. Still show the brief, with your choices marked as assumptions.

## Phase 1: the script
Read `references/script_writing.md`, and `references/gemini_tts.md` when the TTS is Gemini (AI Studio). Deliver:
- **Block 1, style field:** voice description plus a numbered per-paragraph delivery list. The text field is read verbatim, so **delivery directions never go in the script**, in any bracket style. A script once had `[جاد، أبطأ قليلًا]` inside it, and the TTS read it aloud.
- **Block 2, text field:** the clean script. One paragraph per scene, `<long pause>` on its own line between paragraphs, and at most 3–5 English vocal tags from the supported list.
- Generate as **one file** (WAV preferred). Ask the user to upload the chosen font file together with the audio.
- Keep your own visual and SFX plan out of the copy blocks.

For other TTS tools, don't assume their tag syntax. Ask for a screenshot of their expression feature, or check its docs.

## Phase 2: the video
Work in a fresh working folder. Copy the skill's `scripts/` there, and copy `assets/{template.html,themes.js,engine.js,components.js}` into the working folder. If a font was uploaded, copy its Bold `.ttf` there too (unzip if needed).

### 1. Analyze
Save the paragraphs to `scenes.json` **exactly as sent to the TTS, including `<tags>`**, as a JSON list of strings. Then:
```bash
python3 scripts/analyze_audio.py <uploads>/<voice>.wav scenes.json timeline.json
```
It prints each scene's `window` (paste as `S`), its `beats` (word-phrase onsets), its `sounds` (vocal-tag segments such as a sigh or chuckle), and `END`.
- **Beats are sync points:** every visual event and its SFX go on a beat. Sounds can get a small reaction (a dim, a loop mark) but not a new idea.
- **Sanity-check:** a list line should map one item per beat, and the punch line should be the last beat. If a boundary is off by one segment, fix `S` by hand. Multi-burst sounds like `<chuckle>` can show up as one beat plus one sound.

### 2. Design plan (brief, before code)
Read `references/visual_style.md`. Pick a theme from `assets/themes.js`, or derive a new one from the topic's world:
- `blueprint`: systems, engineering, automation.
- `nightphone`: attention, psychology, phones, habits.
- `ledger`: money, economics, history. It is light-colored; preview before its first real use.

Write one line per scene saying which beat triggers what. For quality and patterns, skim `assets/examples/` (two finished videos, 8 scenes each).

### 3. Build
Copy `template.html` to `index.html` and edit the CONFIG block: `THEME`, `AR`, `S`, `END`, `SFX`. For an uploaded font, uncomment the `@font-face` line, set `AR='Brand'`, and change `document.fonts.load` to `'700 40px Brand'`.

Write `SC[i]=(t)=>{...}` per scene using **absolute t**. Everything must be a pure function of t: no CSS animation, no `Date.now()`, no unseeded randomness. Use the library before drawing anything by hand:
- **engine.js:** `pr eo eio back lerp cl`, `polyP` (self-drawing lines), `ptOn`, `pulses` (data flowing along a path), `node(x,y,size,icon,appear,{lit,ic,rot})`, `person`, `txt`, `dot`, `rr`, `glow`. Icons: `db chart doc shield search eye gear cursor code loop`.
- **components.js:** `phone`, `head`, `gauge` (level meter), `clockFace`, `card`, `strike`, `crosshair`, `wordPop`, `counter`, `checkmark`, `weekBars`, `chainLink`, `sparkBurst`, `swipeUp`, `loopMark`. Extra icons: `bell book screen timer grid dumbbell`.
- **themes.js:** `fadeOut(t)` for the last scene, and `THEMES.nightphone.calmFrom/calmTo` to shift the room light.

When a new scene produces a reusable element, add it to `components.js` in the skill, so the next video starts richer.

Rules:
- **No captions or subtitles.** On-screen words are sparse keywords, numbers, or a final punch word.
- One idea per beat. Use numbered markers only for true sequences.
- Safe area: y≈300–1650, x≈100–980. Text at least 60 px.

### 4. Check stills, then motion
```bash
python3 scripts/preview.py index.html sheet.jpg --beats timeline.json      # one frame 0.5 s after every beat
python3 scripts/proxy.py index.html <uploads>/<voice>.wav proxy.mp4   # 540x960, 12 fps, ~1 min
```
- Fix layout from the sheet: overlaps, empty scenes, clipping, the moment a beat lands.
- **Present the proxy to the user** and ask for timing notes before the full render. It costs about 1 minute, and a full render costs about 4. Skip the proxy only if the user asked for speed or already approved the timing.

### 5. Render (foreground chunks)
```bash
python3 scripts/render_frames.py index.html frames 0 650
python3 scripts/render_frames.py index.html frames 650 1300
python3 scripts/render_frames.py index.html frames 1300 1950    # continue until it prints ALL DONE
```

### 6. SFX and mux
```bash
python3 scripts/make_sfx.py index.html sfx.wav
python3 scripts/mux.py frames <uploads>/<voice>.wav sfx.wav <outputs>/<Name>.mp4 --sfx-volume 0.3
```
SFX types: `whoosh sweep swipe type pop close clank tick click ding boom hit riser`. `boom` and `hit` also shake the camera.
**Music is off by default** (SFX only). If the user wants music, they must supply a track they have the rights to: add `--music <track> --music-volume 0.12`, and it is ducked under the voice automatically. Then deliver the file (in claude.ai, `present_files`).

### 7. Report (short)
Give resolution, duration and style, then the honest caveats: timing is estimated, and any manual boundary fixes you made. Ask for scene or second notes.

## Revisions
- **Timing:** edit `S` and the beats, re-render only the affected frame range, then re-mux.
- **SFX level:** re-run `mux.py` with a new `--sfx-volume`. No re-render.
- **Style:** switch `THEME`, re-run the proxy, then do a full render.
