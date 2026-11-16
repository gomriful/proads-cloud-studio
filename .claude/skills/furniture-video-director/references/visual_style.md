# Visual style and motion

## Pick a world from the topic
The visual language should come from the subject's own world. Starting points (don't reuse blindly; adapt the palette and motifs):

| Topic world | Motif | Palette idea |
|---|---|---|
| Systems, engineering, automation, AI workflows | Blueprint: grid paper, schematic nodes, dimension lines, self-drawing strokes | blueprint blue #0F3A66/#082647, ink #E9F3FC, signal yellow #FFC93C, human/alert coral #FF7A66 |
| Money, economics, markets | Ledger/receipt paper, stamps, stacked coins as bars | paper #EDE6D6, ink #1D2A38, green #2E8B57, red stamp #C23B22 |
| Health, biology | Cells/cross-sections, soft organic shapes, microscope circle | deep teal #0C3B3E, cell #7FD1C7, membrane #F2F7F5, marker #F4A259 |
| History, culture, heritage | Map lines, manuscript borders, geometric star patterns | sand #D9C7A3, ink #3B2A1A, indigo #26315C, gold #C99A2E |
| Psychology, habits, attention | Dial meters, loops, a single figure in empty space | night #1B1B3A, soft white #F1F0FF, attention red #FF5A5F, calm blue #6C8EF5 |
| Space, science | Orbits, star charts, measurement ticks | void #070B1A, chart line #9FB3D9, star #FFFFFF, hot accent #FF9F1C |

Spend boldness in **one** place (the accent color and one signature motion). Keep everything else disciplined.

## Motion principles
- **Sync to beats, not to scenes.** Each phrase onset from `timeline.json` is a moment: something appears, lights up, breaks or connects. SFX lands on the same frame.
- **Draw, don't fade.** Lines drawing themselves (`polyP`) and elements popping with overshoot (`back`) read as motion design. Plain opacity fades read as slideshows.
- **Continuous life.** Pulses flowing along connections, slow grid drift and gentle rotation keep static moments alive.
- **Contrast beats.** Strike-throughs (coral), a boom with a camera shake, a bright flash on a divider: use these when the voice says "but", "the difference", "not".
- **The ending is the climax.** Converge everything into one element, then one strong final word, then a hold of about 2 s and a fade.
- **Scene transitions:** the template's fade/push plus the accent-colored sweep line. Keep them under 0.5 s.

## Composition for 9:16 (1080×1920)
- Safe area: keep essentials between y≈300 and y≈1650 and x≈100–980. Platform UI covers the bottom ~250 px and the top ~200 px.
- One focal cluster per scene, centered around y≈900–1100.
- Minimum on-screen text size: 60 px. Punch words: 150–200 px.

## Sound design
- Default: **SFX only**. Music is optional, needs a licensed track supplied by the user, and is ducked under the voice (`mux.py --music`).
- Map: appearing → `pop`, connecting/linking → `clank` or `click`, typing → `type`, checks/steps → `tick`, reveal/transition → `whoosh`/`sweep`, emphasis → `boom` (also shakes), repeated action → `hit`, build-up to a climax → `riser` (auto-starts 0.2 s before its cue), success → `ding`, negation → `swipe`, ending/vanishing → `close`.
- Don't stack more than ~3 cues within 0.3 s, except fast rhythmic series (chain links, checkmarks).
