// engine.js: core helpers, base icons, node, person, scene wrapper, render loop.
// Globals expected from index.html: THEME (name), AR (font family), S, END, SFX, SC.
const C=document.getElementById('c'),X=C.getContext('2d');
const W=C.width,H=C.height,CX=W/2,CY=H/2;
const COL=THEMES[THEME].col;
// ---------- helpers ----------
const cl=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
const pr=(t,a,d)=>cl((t-a)/d);
const eo=p=>1-Math.pow(1-p,3), eio=p=>p<.5?4*p*p*p:1-Math.pow(-2*p+2,3)/2;
const back=p=>{const c=1.9;return p<=0?0:1+(c+1)*Math.pow(p-1,3)+c*Math.pow(p-1,2)};
const lerp=(a,b,p)=>a+(b-a)*p;
function glow(c,b){X.shadowColor=c;X.shadowBlur=b}
function noglow(){X.shadowBlur=0}
function stroke(c,w){X.strokeStyle=c;X.lineWidth=w;X.lineCap='round';X.lineJoin='round'}
function polyP(pts,p){ // draw polyline to fraction p
 if(p<=0)return; let L=[],T=0;
 for(let i=1;i<pts.length;i++){const d=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);L.push(d);T+=d}
 let r=T*p;X.beginPath();X.moveTo(pts[0][0],pts[0][1]);
 for(let i=1;i<pts.length;i++){ if(r>=L[i-1]){X.lineTo(pts[i][0],pts[i][1]);r-=L[i-1]} else {const f=r/L[i-1];X.lineTo(lerp(pts[i-1][0],pts[i][0],f),lerp(pts[i-1][1],pts[i][1],f));break}}
 X.stroke();
}
function ptOn(pts,p){let L=[],T=0;for(let i=1;i<pts.length;i++){const d=Math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]);L.push(d);T+=d}
 let r=T*cl(p);for(let i=1;i<pts.length;i++){if(r<=L[i-1]){const f=r/L[i-1];return[lerp(pts[i-1][0],pts[i][0],f),lerp(pts[i-1][1],pts[i][1],f)]}r-=L[i-1]}return pts[pts.length-1]}
function rr(x,y,w,h,r){X.beginPath();X.roundRect(x,y,w,h,r)}
function dot(x,y,r,c,g=24){X.fillStyle=c;glow(c,g);X.beginPath();X.arc(x,y,r,0,7);X.fill();noglow()}
function txt(s,x,y,size,font,col,al=1,align='center',dir='ltr'){X.save();X.globalAlpha*=al;X.fillStyle=col;X.font=`700 ${size}px ${font}`;X.textAlign=align;X.textBaseline='middle';X.direction=dir;X.fillText(s,x,y);X.restore()}
function pulses(pts,t,n,speed,col=COL.sig,r=9){for(let k=0;k<n;k++){const p=((t*speed+k/n)%1);const q=ptOn(pts,p);dot(q[0],q[1],r,col,30)}}

// ---------- icons (centered, unit size s) ----------
const ICON={
 db(s){X.beginPath();X.ellipse(0,-s*.32,s*.34,s*.11,0,0,7);X.stroke();X.beginPath();X.moveTo(-s*.34,-s*.32);X.lineTo(-s*.34,s*.3);X.ellipse(0,s*.3,s*.34,s*.11,0,Math.PI,0,true);X.lineTo(s*.34,-s*.32);X.stroke();X.beginPath();X.ellipse(0,0,s*.34,s*.11,0,0,Math.PI);X.stroke()},
 chart(s){X.beginPath();X.moveTo(-s*.36,-s*.36);X.lineTo(-s*.36,s*.34);X.lineTo(s*.38,s*.34);X.stroke();[[-.2,.3],[0,.5],[.2,.2]].forEach(([x,h],i)=>{rr(s*(x-.06)+s*.04,s*(.28-h*1.0),s*.12,s*h,4);X.stroke()});X.beginPath();X.moveTo(-s*.26,s*0.02);X.lineTo(-s*.02,-s*.2);X.lineTo(s*.12,-s*.08);X.lineTo(s*.34,-s*.32);X.stroke()},
 doc(s){X.beginPath();X.moveTo(-s*.28,-s*.38);X.lineTo(s*.12,-s*.38);X.lineTo(s*.28,-s*.22);X.lineTo(s*.28,s*.38);X.lineTo(-s*.28,s*.38);X.closePath();X.stroke();X.beginPath();X.moveTo(s*.12,-s*.38);X.lineTo(s*.12,-s*.22);X.lineTo(s*.28,-s*.22);X.stroke();for(let i=0;i<3;i++){X.beginPath();X.moveTo(-s*.16,-s*.06+i*s*.14);X.lineTo(s*.16-(i==2?s*.12:0),-s*.06+i*s*.14);X.stroke()}},
 shield(s){X.beginPath();X.moveTo(0,-s*.4);X.lineTo(s*.32,-s*.26);X.quadraticCurveTo(s*.32,s*.24,0,s*.4);X.quadraticCurveTo(-s*.32,s*.24,-s*.32,-s*.26);X.closePath();X.stroke();X.beginPath();X.moveTo(-s*.13,0);X.lineTo(-s*.02,s*.11);X.lineTo(s*.15,-s*.1);X.stroke()},
 search(s){X.beginPath();X.arc(-s*.06,-s*.06,s*.22,0,7);X.stroke();X.beginPath();X.moveTo(s*.1,s*.1);X.lineTo(s*.3,s*.3);X.stroke()},
 eye(s){X.beginPath();X.moveTo(-s*.42,0);X.quadraticCurveTo(0,-s*.36,s*.42,0);X.quadraticCurveTo(0,s*.36,-s*.42,0);X.stroke();X.beginPath();X.arc(0,0,s*.12,0,7);X.stroke()},
 gear(s,rot=0){X.save();X.rotate(rot);X.beginPath();for(let i=0;i<16;i++){const a=i/16*Math.PI*2,r=i%2?s*.3:s*.38;const a2=a+Math.PI/16;X.lineTo(Math.cos(a)*r,Math.sin(a)*r);X.lineTo(Math.cos(a2)*r,Math.sin(a2)*r)}X.closePath();X.stroke();X.beginPath();X.arc(0,0,s*.12,0,7);X.stroke();X.restore()},
 cursor(s){X.beginPath();X.moveTo(-s*.2,-s*.34);X.lineTo(-s*.2,s*.22);X.lineTo(-s*.06,s*.08);X.lineTo(s*.06,s*.32);X.lineTo(s*.14,s*.28);X.lineTo(s*.02,s*.04);X.lineTo(s*.2,s*.04);X.closePath();X.stroke()},
 code(s){X.beginPath();X.moveTo(-s*.14,-s*.26);X.lineTo(-s*.38,0);X.lineTo(-s*.14,s*.26);X.stroke();X.beginPath();X.moveTo(s*.14,-s*.26);X.lineTo(s*.38,0);X.lineTo(s*.14,s*.26);X.stroke();X.beginPath();X.moveTo(s*.07,-s*.32);X.lineTo(-s*.07,s*.32);X.stroke()},
 loop(s){X.beginPath();X.arc(0,0,s*.3,-Math.PI*.3,Math.PI*1.35);X.stroke();const a=Math.PI*1.35;const px=Math.cos(a)*s*.3,py=Math.sin(a)*s*.3;X.beginPath();X.moveTo(px-s*.12,py-s*.02);X.lineTo(px,py);X.lineTo(px+s*.02,py-s*.13);X.stroke();X.beginPath();X.moveTo(-s*.07,-s*.12);X.lineTo(s*.13,0);X.lineTo(-s*.07,s*.12);X.closePath();X.fillStyle=X.strokeStyle;X.fill()}
};
function node(x,y,sz,icon,ap,opt={}){ // ap: appear progress
 if(ap<=0)return; const sc=back(cl(ap));X.save();X.translate(x,y);X.scale(sc,sc);X.globalAlpha*=cl(ap*2);
 const lit=opt.lit||0;
 X.fillStyle=COL.panel;rr(-sz/2,-sz/2,sz,sz,sz*.22);X.fill();
 stroke(lit>0?COL.sig:COL.ink,5);if(lit>0)glow(COL.sig,30*lit);rr(-sz/2,-sz/2,sz,sz,sz*.22);X.stroke();noglow();
 stroke(opt.ic||(lit>.5?COL.sig:COL.ink),6);ICON[icon](sz*.72,opt.rot||0);
 X.restore();
}
function person(x,y,s,al=1,col=COL.ink,arm=0){X.save();X.globalAlpha*=al;X.translate(x,y);stroke(col,6);
 X.beginPath();X.arc(0,-s*.62,s*.16,0,7);X.stroke();
 X.beginPath();X.moveTo(0,-s*.44);X.lineTo(0,s*.1);X.stroke();
 X.beginPath();X.moveTo(0,s*.1);X.lineTo(-s*.18,s*.5);X.moveTo(0,s*.1);X.lineTo(s*.18,s*.5);X.stroke();
 X.beginPath();X.moveTo(0,-s*.3);X.lineTo(-s*.26,-s*.02);X.stroke();
 const a=arm;X.beginPath();X.moveTo(0,-s*.3);const hx=Math.cos(a)*s*.34,hy=Math.sin(a)*s*.34-s*.3;X.lineTo(hx,hy);X.stroke();X.restore();return[x+Math.cos(a)*s*.34,y+Math.sin(a)*s*.34-s*.3]}


// ---------- scene wrapper, transitions, camera ----------
function scene(t,i,fn){const [a,b]=S[i];if(t<a-0.01||t>b+0.01)return;
 const fin=eo(pr(t,a,0.45)), fout=i==S.length-1?1:1-eio(pr(t,b-0.4,0.4));
 X.save();X.globalAlpha=Math.min(fin,fout);const s=lerp(0.94,1,fin)*lerp(1.06,1,fout);X.translate(CX,CY);X.scale(s,s);X.translate(-CX,-CY);
 fn(t);X.restore()}
function shake(t){let s=0;SFX.forEach(([c,k])=>{if(k=='boom'||k=='hit'){const d=t-c;if(d>=0&&d<0.45)s+=(k=='boom'?14:6)*Math.pow(1-d/0.45,2)}});return[Math.sin(t*93)*s,Math.cos(t*71)*s]}
function progressRail(t,col){const p=cl(t/(END-2.4));stroke(THEMES[THEME].rail||'rgba(255,255,255,.15)',4);X.beginPath();X.moveTo(120,H-110);X.lineTo(W-120,H-110);X.stroke();
 stroke(col,4);X.beginPath();X.moveTo(W-120,H-110);X.lineTo(W-120-(W-240)*p,H-110);X.stroke();dot(W-120-(W-240)*p,H-110,7,col,16)}
function renderAt(t){
 const T=THEMES[THEME];
 X.setTransform(1,0,0,1,0,0);X.globalAlpha=1;
 const [sx,sy]=shake(t);X.translate(sx,sy);
 T.bg(t);
 SC.forEach((f,i)=>f&&scene(t,i,f));
 for(let i=1;i<S.length;i++){const p=pr(t,S[i][0]-0.3,0.6);if(p>0&&p<1)T.sweep(t,eio(p))}
 X.setTransform(1,0,0,1,0,0);T.vignette();
}
window.renderAt=renderAt;
