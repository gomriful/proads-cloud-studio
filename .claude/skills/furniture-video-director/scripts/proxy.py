#!/usr/bin/env python3
"""Fast low-res motion proxy (540x960, 12 fps) with voice + SFX, for checking rhythm and sync BEFORE the full render.
usage: proxy.py <index.html> <voice> <out.mp4> [--fps 12] [--from 0] [--to END]
Renders ~40-60 s of video per minute of compute. Present it to the user for timing approval."""
import argparse, os, subprocess, tempfile, time
from playwright.sync_api import sync_playwright
ap=argparse.ArgumentParser(); ap.add_argument('html'); ap.add_argument('voice'); ap.add_argument('out')
ap.add_argument('--fps',type=int,default=12); ap.add_argument('--from',dest='t0',type=float,default=0); ap.add_argument('--to',dest='t1',type=float,default=None)
a=ap.parse_args(); here=os.path.dirname(os.path.abspath(__file__)); tmp=tempfile.mkdtemp(); t_start=time.time()
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920},device_scale_factor=0.5)
    errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+os.path.abspath(a.html)); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
    end=a.t1 if a.t1 is not None else pg.evaluate('END'); n=int((end-a.t0)*a.fps)
    for i in range(n):
        pg.evaluate(f'renderAt({a.t0+i/a.fps})'); pg.screenshot(path=f'{tmp}/f{i:05d}.jpg',type='jpeg',quality=70)
    b.close()
if errs: print('PAGE ERRORS:',errs[:5])
sfx=os.path.join(tmp,'sfx.wav'); subprocess.run(['python3',os.path.join(here,'make_sfx.py'),a.html,sfx],check=True,stdout=subprocess.DEVNULL)
fc=("[1:a]atrim=start=%f,asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,apad[v];"
    "[2:a]atrim=start=%f,asetpts=PTS-STARTPTS,volume=0.3[s];[v][s]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]")%(a.t0,a.t0)
subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(a.fps),'-i',f'{tmp}/f%05d.jpg','-i',a.voice,'-i',sfx,'-filter_complex',fc,
    '-map','0:v','-map','[a]','-c:v','libx264','-preset','veryfast','-crf','26','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest',a.out],check=True)
print(f'proxy {a.out}: {n} frames in {time.time()-t_start:.0f}s')
