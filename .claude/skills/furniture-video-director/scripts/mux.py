#!/usr/bin/env python3
"""Encode frames + voice + sfx to MP4. usage: mux.py <frames_dir> <voice> <sfx.wav> <out.mp4> [--sfx-volume 0.3] [--fps 30] [--music track.mp3 --music-volume 0.12]
Music is optional and off by default; only use tracks you have the rights to.
If <out>.video.mp4 (silent encode) already exists and is newer than the frames, only the audio is remixed."""
import argparse, subprocess, os, glob
ap=argparse.ArgumentParser(); ap.add_argument('frames'); ap.add_argument('voice'); ap.add_argument('sfx'); ap.add_argument('out')
ap.add_argument('--sfx-volume',type=float,default=0.3); ap.add_argument('--fps',type=int,default=30); ap.add_argument('--reencode',action='store_true')
ap.add_argument('--music',default=None); ap.add_argument('--music-volume',type=float,default=0.12)
a=ap.parse_args()
silent=os.path.join(os.path.dirname(os.path.abspath(a.frames)),'_silent.mp4')
newest=max(os.path.getmtime(f) for f in glob.glob(a.frames+'/f*.jpg'))
if a.reencode or not os.path.exists(silent) or os.path.getmtime(silent)<newest:
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(a.fps),'-i',a.frames+'/f%05d.jpg',
        '-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p',silent],check=True)
inputs=['-i',silent,'-i',a.voice,'-i',a.sfx]
fc=f"[1:a]aresample=48000,aformat=channel_layouts=stereo,apad{',asplit=2[v][vk]' if a.music else '[v]'};[2:a]volume={a.sfx_volume}[s];"
if a.music:
    inputs+=['-stream_loop','-1','-i',a.music]
    fc+=(f"[3:a]aresample=48000,aformat=channel_layouts=stereo,volume={a.music_volume}[m];"
         "[m][vk]sidechaincompress=threshold=0.05:ratio=6:attack=20:release=300[md];"  # duck music under the voice
         "[v][s][md]amix=inputs=3:duration=longest:normalize=0,alimiter=limit=0.95[a]")
else:
    fc+="[v][s]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95[a]"
subprocess.run(['ffmpeg','-y','-loglevel','error',*inputs,'-filter_complex',fc,
    '-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',a.out],check=True)
print('wrote',a.out)
