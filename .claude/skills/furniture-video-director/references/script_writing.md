# Writing the voiceover script

## Length and structure
- Short (45–60 s): 7–9 paragraphs, about 120–150 Arabic words. Speech runs ~2.3–2.6 words/s plus pauses.
- One paragraph = one scene = one visual idea.
- Arc: **hook** (common misconception or surprising claim, under 3 s) → **turn** ("but the real…") → **demonstration** (concrete mechanism the viewer can picture) → **payoff** (time or effort saved) → **contrast** (who wins vs who doesn't) → **how** (simple method, 2–3 verbs) → **call to action** (one small, specific step) → **punch line** (short, memorable, ends on a strong word).

## Writing for the ear and for the animation
- Write lines that **can be drawn**: lists of concrete things ("one collects data, another analyzes it, a third writes the report") give the animation natural beats. Abstract lines give it nothing.
- Use commas, "…" and `<short pause>` deliberately. They create the pauses the aligner uses as sync points. Lists separated by commas become separate beats. Put `<long pause>` between paragraphs so scene boundaries are unmistakable.
- End the video on a short final phrase after a pause. It becomes the visual climax.
- Persuasive does not mean exaggerated. Avoid claims that aren't true in general (e.g. "with perfect accuracy"). Prefer honest strength ("every day, without getting tired").
- For experienced audiences, include one real technical idea (chaining, decomposition, human-in-the-loop review) rather than hype.

## Language
- If the user accepts it, neutral Modern Standard Arabic (عربية بيضاء) is pronounced far more reliably by TTS than Gulf or Omani dialect. Warn about dialect drift if they insist on a dialect, and suggest a 2–3 line test first.
- Keep English terms the audience uses (Workflow, AI). If the TTS mispronounces one, spell it in Arabic letters ("وورك فلو").

## Output format (two separate copy blocks)
Block 1 goes in the TTS **style/description field**: the voice description plus a numbered list of delivery directions, one per paragraph.
Block 2 goes in the **text field**: the verbatim script only.

Never put delivery directions inside the script text. Verbatim TTS models read them aloud. For Gemini's exact tag syntax and supported tags, see `gemini_tts.md`.

Keep a private scene plan (visual + SFX per paragraph) for Phase 2. Don't put it in the copy blocks.
