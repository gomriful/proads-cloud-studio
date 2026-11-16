# Formatting for Gemini 3.8 Flash TTS (AI Studio)

Verified from Google's docs (Sept 2026). Re-check the docs if the user reports odd behavior or mentions a newer model.

## The rule that caused a real failure
The text field is a **verbatim transcript**. Everything in it is spoken. A previous script used Arabic direction tags like `[جاد، أبطأ قليلًا]` inside the text, and the TTS **read them aloud**. The alignment also broke, because the extra spoken words shifted the timing.

So:
- **Never** put delivery directions (mood, pace, tone) in the text, in any bracket style.
- Delivery goes in the **style field** (AI Studio "style"/description; API `speech_metadata.style`). Put the voice description plus a numbered per-paragraph direction list there.

## Inline tags: point-in-time vocal sounds only
- Angle brackets, **English**, even when the script is Arabic: `<sigh>`, not `<تنهيدة>`.
- AI Studio has a "+ Expression" button that inserts them. Pasting them as text works the same.
- They describe a **sound, not a mood**. There is no `<excited>` or `<serious>`.
- Anything outside the supported list is read as text.

Supported set (as documented):
`<argh> <breath> <heavy breath> <exhales> <cackle> <cheer> <chuckle> <cough> <cry> <gasp> <giggle> <groan> <growl> <grunt> <grr> <hiss> <laugh> <moan> <pant> <pff> <phew> <scream> <shout> <shriek> <sigh> <sneeze> <snicker> <snort> <sob> <throat-clearing> <tsk> <whimper> <whispers> <yawn> <short pause> <long pause>`

## How this skill uses them
- `<long pause>` on its own line **between every paragraph**. This creates the clear scene-boundary silences that `analyze_audio.py` relies on.
- `<short pause>` inside a paragraph where a dramatic beat helps (usually replacing or following "…").
- 3–5 vocal tags per ~60 s script at most (`<sigh>`, `<breath>`, `<exhales>`, `<chuckle>`, `<gasp>`), placed where a real speaker would make that sound. More sounds fake.
- Keep the script free of any other markup.

## Output template

Style field block:
```
صوت [..] [عمر]، [صفات]، بإيقاع [..]، ونبرة [..] وليست نبرة مذيع رسمي. نطق عربي فصيح مبسّط.
طريقة الأداء لكل فقرة بالترتيب:
1: ...
2: ...
```

Text block:
```
الفقرة الأولى… <short pause> بقيتها. <sigh>
<long pause>
الفقرة الثانية.
<long pause>
...
```
