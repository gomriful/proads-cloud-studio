# Phase 0: brief interview ("grill" mode)

Goal: reach a shared, explicit brief before writing a single line of script. Do it fast. For a 60-second video, a long interrogation costs more than it saves.

## Rules
1. **One question per message.** Use the tappable-options tool when the answers are discrete. Open text only for topic and message.
2. **Every question carries a recommended answer** with a one-line reason, so the user can reply "ok". Example: "Recommended: neutral MSA, because Gemini pronounces it far more reliably than dialects."
3. **Skip what is already known** from the conversation or stored context. Never re-ask. State the known value in the final brief instead.
4. **Cap: 7 decisions.** If more remain open, fill them with the recommended defaults and mark them as assumptions.
5. **Escape hatch:** if the user says "كمّل" / "use defaults" / "اختر أنت", stop asking immediately, choose the defaults, and mark everything you chose as an assumption.
6. **Challenge, don't just collect.** This is the "grill" part. If an answer weakens the video, say so once, with the reason, and offer the fix. Examples: a vague topic ("AI") has no angle; a message with no concrete, drawable mechanism; a claim that can't be stated honestly; a dialect the TTS handles badly. The user decides.
7. Never invent facts about the topic. If the script will need numbers or claims the user hasn't given and you can't verify, ask or keep the claim qualitative.

## Decision tree (ask in this order, skipping the known ones)
1. **Topic + angle**: the single idea the viewer should leave with. A topic without an angle gets challenged ("what should they believe or do after 60 s?").
2. **Audience**: who, and their level (beginner / somewhat experienced / expert). This drives vocabulary and how much to explain.
3. **Goal and tone**: persuade / explain / warn / inspire, and the tone (calm, confident, hype).
4. **Length + format**: default Short, 9:16, 45–60 s.
5. **Language / dialect**: default neutral MSA (عربية بيضاء). Warn about TTS dialect drift.
6. **Visual world + font**: propose ONE theme (see `visual_style.md`, `assets/themes.js`) and ONE free font with its source, both tied to the topic. The user can override.
7. **Call to action**: one small, specific step the viewer can take today.

Defaults, not asked unless the user raises them: SFX only and no music (music needs a licensed track from the user), no captions, Gemini TTS format.

## Close with the brief (wait for approval)
Show it compactly, separating what was said from what you chose:

```
الحقائق (منك):        الموضوع… / الجمهور… / …
القرارات (اتفقنا):     الزاوية… / الأسلوب… / المدة والمقاس…
الافتراضات (اخترتها):  العالم البصري… / الخط… (قابلة للتغيير)
المخاطر:              مثال: ادعاء يحتاج صياغة حذرة، لهجة قد تتعثر
```

Write the script (Phase 1) only after the user approves or adjusts the brief.
