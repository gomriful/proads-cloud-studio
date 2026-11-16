# Furniture video production checklist

1. Run `ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate,codec_name -of json INPUT.mp4` for each uploaded clip.
2. Review actual footage and note timestamped usable sections. Do not derive shots solely from metadata.
3. Write EDL with source in/out and final sequence in/out; preserve original colors.
4. Build video base with FFmpeg trim/scale/pad/fps/concat, taking care to normalize each clip's resolution and fps. Crop only if it does not conceal key furniture features; otherwise pad.
5. Render Arabic title overlays with browser-based HTML/CSS and an available Arabic font; check joined glyphs and RTL. Composite with ffmpeg overlay.
6. Mix approved voiceover and licensed music at intelligible levels. Never silently assume music rights.
7. Inspect rendered first/middle/end frames, check total duration, verify MP4 output exists and plays.
8. On Claude mobile without runnable tools, provide EDL and CapCut instructions instead of claiming a rendered file.

## Example export settings
H.264, yuv420p, 1080x1920, 30 fps, AAC 48 kHz. Preserve original audio if desired and lawful.
