#!/usr/bin/env python3
"""Contact sheet of frames. usage: preview.py <index.html> <sheet.jpg> t1 t2 ...
   or: preview.py <index.html> <sheet.jpg> --beats timeline.json   (one frame 0.5s after every beat)"""
import sys, os, io, json
from playwright.sync_api import sync_playwright
from PIL import Image
html,out=sys.argv[1],sys.argv[2]
if sys.argv[3]=='--beats':
    ts=[round(b+0.5,2) for sc in json.load(open(sys.argv[4],encoding='utf-8'))['scenes'] for b in sc['beats']]
else: ts=[float(x) for x in sys.argv[3:]]
ims=[]; errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1080,'height':1920})
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('file://'+os.path.abspath(html)); pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(300)
    for t in ts:
        pg.evaluate(f'renderAt({t})'); ims.append(Image.open(io.BytesIO(pg.screenshot(type='jpeg',quality=75))).resize((270,480)))
    b.close()
cols=min(6,len(ims)); rows=(len(ims)+cols-1)//cols
m=Image.new('RGB',(270*cols,480*rows),'white')
for i,im in enumerate(ims): m.paste(im,((i%cols)*270,(i//cols)*480))
m.save(out); print('saved',out,'times',ts, 'ERRORS:'+str(errs) if errs else '')
