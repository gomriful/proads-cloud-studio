#!/usr/bin/env python3
"""Synthesize an SFX track from the SFX cue list and END in index.html.
usage: make_sfx.py <index.html> <sfx.wav>"""
import re,sys,numpy as np,wave
from scipy.signal import butter,sosfilt
html=open(sys.argv[1],encoding='utf-8').read()
cues=[(float(a),b) for a,b in re.findall(r"\[([\d.]+),'(\w+)'\]",html.split('const SFX=')[1].split('];')[0])]
END=float(re.search(r'const END=([\d.]+)',html).group(1))
sr=48000; out=np.zeros(int(sr*(END+1)))
rng=np.random.default_rng(7)
def T(d): return np.arange(int(sr*d))/sr
def bp(x,lo,hi): return sosfilt(butter(2,[lo,hi],btype='band',fs=sr,output='sos'),x)
def hp(x,f): return sosfilt(butter(2,f,btype='high',fs=sr,output='sos'),x)
def lp(x,f): return sosfilt(butter(2,f,btype='low',fs=sr,output='sos'),x)
def chirp(f0,f1,d):
    t=T(d); f=np.geomspace(f0,f1,len(t)); return np.sin(2*np.pi*np.cumsum(f)/sr)
def norm(x,a): return x/ (np.max(np.abs(x))+1e-9)*a
def S(k):
    if k=='whoosh':
        t=T(.5); e=np.sin(np.pi*t/.5)**2; return norm(bp(rng.standard_normal(len(t)),500,5000)*e,.55)
    if k=='sweep':
        t=T(.6); e=np.sin(np.pi*t/.6)**3; return norm(bp(rng.standard_normal(len(t)),250,2500)*e,.35)
    if k=='swipe':
        t=T(.22); e=np.exp(-t*14); return norm(hp(rng.standard_normal(len(t)),2500)*e,.35)
    if k=='type':
        t=T(.03); return norm(hp(rng.standard_normal(len(t)),1500)*np.exp(-t*220),.3)
    if k=='pop':
        t=T(.12); return norm(chirp(900,280,.12)*np.exp(-t*30),.55)
    if k=='close':
        t=T(.16); return norm(chirp(520,140,.16)*np.exp(-t*22),.5)
    if k=='clank':
        t=T(.4); x=sum(np.sin(2*np.pi*f*t)*np.exp(-t*d) for f,d in [(1180,12),(1830,16),(2710,20),(3900,28)]); return norm(x,.25)
    if k=='tick':
        t=T(.04); return norm(np.sin(2*np.pi*2100*t)*np.exp(-t*120),.3)
    if k=='click':
        t=T(.03); x=np.sin(2*np.pi*3000*t)*np.exp(-t*200)+hp(rng.standard_normal(len(t)),3000)*np.exp(-t*300)*.5; return norm(x,.35)
    if k=='ding':
        t=T(1.0); x=(np.sin(2*np.pi*1320*t)+.4*np.sin(2*np.pi*2640*t)+.2*np.sin(2*np.pi*3960*t))*np.exp(-t*4.5); return norm(x,.3)
    if k=='boom':
        t=T(1.0); x=chirp(75,38,1.0)*np.exp(-t*4)+lp(rng.standard_normal(len(t)),200)*np.exp(-t*12)*.6; return norm(x,.8)
    if k=='hit':
        t=T(.18); x=np.sin(2*np.pi*170*t)*np.exp(-t*30)+lp(rng.standard_normal(len(t)),1200)*np.exp(-t*40); return norm(x,.45)
    if k=='riser':
        t=T(.9); e=(t/.9)**2; x=bp(rng.standard_normal(len(t)),800,6000)*e+chirp(200,900,.9)*e*.4; x[-int(sr*.03):]*=np.linspace(1,0,int(sr*.03)); return norm(x,.35)
    raise Exception(k)
for c,k in cues:
    s=S(k)
    start=int(c*sr) if k!='riser' else max(0,int((c-0.2)*sr))
    out[start:start+len(s)]+=s[:len(out)-start]
st=np.stack([out,out],1)
st=np.clip(st,-1,1)
w=wave.open(sys.argv[2],'wb');w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((st*32767).astype(np.int16).tobytes());w.close()
print(len(cues),'cues',END)
