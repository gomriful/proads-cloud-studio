#!/usr/bin/env python3
"""Detect pauses in a voiceover and align scene texts to speech segments.

usage: analyze_audio.py <audio> <scenes.json> <timeline.json> [--min-pause 0.3] [--db-drop 38]

scenes.json: JSON list of scene texts, one per paragraph, WITH their inline <tags> (vocal tags guide the alignment;
they are stripped from the text length). Short segments at vocal-tag positions are reported as 'sounds', not beats.
Output timeline.json:
  {duration, pauses:[[a,b],...], scenes:[{text,start,end,beats:[...], window:[in,out]}], suggested_end}
Timing is inferred from silence + text length. It is an estimate, not speech recognition.
"""
import sys, json, wave, subprocess, tempfile, os, argparse
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument('audio'); ap.add_argument('scenes'); ap.add_argument('out')
ap.add_argument('--min-pause', type=float, default=0.3)
ap.add_argument('--db-drop', type=float, default=38.0, help='silence threshold below loudest frame (dB)')
a = ap.parse_args()

src = a.audio
if not src.lower().endswith('.wav'):
    tmp = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '24000', tmp], check=True)
    src = tmp
w = wave.open(src)
sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
raw = w.readframes(n)
dt = {1: np.uint8, 2: np.int16, 4: np.int32}[sw]
x = np.frombuffer(raw, dtype=dt).astype(float)
if sw == 1: x -= 128
x = x.reshape(-1, ch).mean(1)
dur = len(x) / sr

hop = int(sr * 0.02)
fr = len(x) // hop
rms = np.sqrt(np.mean(x[:fr * hop].reshape(fr, hop) ** 2, 1))
db = 20 * np.log10(rms + 1e-9)
sil = db < db.max() - a.db_drop

pauses = []; i = 0
while i < fr:
    if sil[i]:
        j = i
        while j < fr and sil[j]: j += 1
        if (j - i) * 0.02 >= a.min_pause: pauses.append((round(i * 0.02, 2), round(j * 0.02, 2)))
        i = j
    else: i += 1

# speech segments between pauses (drop leading/trailing silence)
segs = []; s = 0.0
for p0, p1 in pauses:
    if p0 > s + 0.05: segs.append((s, p0))
    s = p1
if dur > s + 0.05: segs.append((s, dur))
if segs and pauses and pauses[0][0] == 0: pass

import re
raw = json.load(open(a.scenes, encoding='utf-8'))
PAUSE_TAGS = {'short pause', 'long pause'}
def vocal_tags(t): return [m.strip() for m in re.findall(r'<([^>]*)>', t) if m.strip() not in PAUSE_TAGS]
def starts_vocal(t): m = re.match(r'\s*<([^>]*)>', t); return bool(m and m.group(1).strip() not in PAUSE_TAGS)
def ends_vocal(t): m = re.search(r'<([^>]*)>\s*[.،…]*\s*$', t); return bool(m and m.group(1).strip() not in PAUSE_TAGS)
texts = [re.sub(r'<[^>]*>', ' ', t).strip() for t in raw]
SV = [starts_vocal(t) for t in raw]; EV = [ends_vocal(t) for t in raw]; NV = [len(vocal_tags(t)) for t in raw]
K, M = len(texts), len(segs)
if M < K:
    sys.exit(f'Only {M} speech segments for {K} scenes. Lower --min-pause or --db-drop, or check the audio.')
L = np.array([len(t.replace(' ', '')) for t in texts], float); L /= L.sum()
sp = np.array([b - a_ for a_, b in segs]); S = sp.sum()
cum = np.concatenate([[0], np.cumsum(sp)])
gap = [segs[m + 1][0] - segs[m][1] for m in range(M - 1)]  # pause after segment m

SHORT = 0.7  # seconds; vocal-tag sounds are usually shorter than this
# DP: assign contiguous segment groups to scenes; cost = squared share error, bonus for long boundary pauses
INF = 1e18
D = np.full((K + 1, M + 1), INF); B = np.zeros((K + 1, M + 1), int); D[0][0] = 0
for k in range(1, K + 1):
    for m in range(k, M - (K - k) + 1):
        for j in range(k - 1, m):
            if D[k - 1][j] >= INF: continue
            share = (cum[m] - cum[j]) / S
            c = (share - L[k - 1]) ** 2
            if m < M: c += 0.0004 / max(gap[m - 1], 0.1)  # boundary after segment m-1
            # vocal tags (<sigh>, <chuckle>...) are heard as short sound segments: keep them with their scene
            # only where a tag sound is plausible: short words (e.g. "لأن") are left alone
            if sp[j] < SHORT and not SV[k - 1] and k >= 2 and EV[k - 2]: c += 0.004  # belongs to previous scene's ending tag
            if sp[m - 1] < SHORT and not EV[k - 1] and k < K and SV[k] and m - 1 > j: c += 0.004  # belongs to next scene's opening tag
            if D[k - 1][j] + c < D[k][m]: D[k][m] = D[k - 1][j] + c; B[k][m] = j
idx = [M]
for k in range(K, 0, -1): idx.append(B[k][idx[-1]])
idx = idx[::-1]

scenes = []
for k in range(K):
    g = segs[idx[k]:idx[k + 1]]
    beats = [round(q[0], 2) for q in g]; sounds = []
    if NV[k]:  # short segments in a scene that has vocal tags are likely the tag sounds, not words
        for q in g:
            if q[1] - q[0] < SHORT and ((q is g[0] and SV[k]) or (q is g[-1] and EV[k]) or len(sounds) < NV[k] - SV[k] - EV[k]):
                sounds.append(round(q[0], 2))
        beats = [b for b in beats if b not in sounds] or beats
    scenes.append({'text': texts[k], 'start': round(g[0][0], 2), 'end': round(g[-1][1], 2),
                   'beats': beats, 'sounds': sounds})
# windows: boundaries at pause midpoints
for k, sc in enumerate(scenes):
    win_in = 0.0 if k == 0 else round((scenes[k - 1]['end'] + sc['start']) / 2, 2)
    win_out = None if k == K - 1 else round((sc['end'] + scenes[k + 1]['start']) / 2, 2)
    sc['window'] = [win_in, win_out]
end = round(dur + 2.4, 2)
scenes[-1]['window'][1] = end

out = {'duration': round(dur, 2), 'pauses': pauses, 'scenes': scenes, 'suggested_end': end}
json.dump(out, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'duration {dur:.2f}s  pauses {len(pauses)}  segments {M}')
for k, sc in enumerate(scenes):
    print(f"S{k+1}: {sc['start']:6.2f}-{sc['end']:6.2f}  window {sc['window']}  beats {sc['beats']}" + (f"  sounds {sc['sounds']}" if sc['sounds'] else ''))
print('S =', json.dumps([sc['window'] for sc in scenes]), ';  END =', end)
