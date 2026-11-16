#!/usr/bin/env python3
"""Render frames [start,end) of a renderAt(t) canvas page to JPEGs. Run in the foreground, in chunks.
usage: render_frames.py <index.html> <frames_dir> <start> <end> [--fps 30] [--w 1080 --h 1920]"""
import argparse, os, time
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser(); ap.add_argument('html'); ap.add_argument('out'); ap.add_argument('start',type=int); ap.add_argument('end',type=int)
ap.add_argument('--fps',type=int,default=30); ap.add_argument('--w',type=int,default=1080); ap.add_argument('--h',type=int,default=1920)
a=ap.parse_args(); os.makedirs(a.out,exist_ok=True); t0=time.time()
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':a.w,'height':a.h})
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+os.path.abspath(a.html)); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
    N=int(pg.evaluate('END')*a.fps); last=min(a.end,N)
    for i in range(a.start,last):
        pg.evaluate(f'renderAt({i/a.fps})')
        pg.screenshot(path=f'{a.out}/f{i:05d}.jpg',type='jpeg',quality=92)
    b.close()
if errs: print('PAGE ERRORS:',errs[:5])
print(f'total frames N={N}; rendered {a.start}..{last-1} in {time.time()-t0:.0f}s' + ('  (ALL DONE)' if last>=N else f'  next: {last} {last+650}'))
