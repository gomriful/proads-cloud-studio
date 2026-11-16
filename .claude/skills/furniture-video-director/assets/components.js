// components.js: reusable pieces from past videos. Load AFTER engine.js.
// All take explicit positions and a progress/time value, so they stay pure functions of t.
// Catalog (see SKILL.md):
//  phone(x,y,w,h,al,col,fill)        head(x,y,s,al,col)            gauge(x,y,r,v,al,label)
//  clockFace(x,y,r,turn,al,arcCol)    card(x,y,w,h,ap,col)          strike(x1,y1,x2,y2,p,col)
//  crosshair(x,y,r,p)                 wordPop(str,x,y,size,p,col,dir) counter(from,to,p,x,y,size,fmt,col)
//  checkmark(x,y,s,p,col)             weekBars(x0,base,heights,t,start,step) chainLink(x,y,p,vertical,lit)
//  sparkBurst(x,y,p,col,n)            swipeUp(x,yFrom,yTo,p)         loopMark(x,y,s,p,t,col)
//  Extra icons for node(): bell book screen timer grid dumbbell

Object.assign(ICON,{
 bell(s){X.beginPath();X.moveTo(-s*.3,s*.18);X.quadraticCurveTo(-s*.22,s*.08,-s*.22,-s*.08);X.quadraticCurveTo(-s*.22,-s*.34,0,-s*.36);X.quadraticCurveTo(s*.22,-s*.34,s*.22,-s*.08);X.quadraticCurveTo(s*.22,s*.08,s*.3,s*.18);X.closePath();X.stroke();X.beginPath();X.arc(0,s*.26,s*.07,0,Math.PI);X.stroke()},
 book(s){X.beginPath();X.moveTo(0,-s*.26);X.quadraticCurveTo(-s*.2,-s*.34,-s*.4,-s*.28);X.lineTo(-s*.4,s*.28);X.quadraticCurveTo(-s*.2,s*.22,0,s*.3);X.quadraticCurveTo(s*.2,s*.22,s*.4,s*.28);X.lineTo(s*.4,-s*.28);X.quadraticCurveTo(s*.2,-s*.34,0,-s*.26);X.lineTo(0,s*.3);X.stroke()},
 screen(s){rr(-s*.4,-s*.28,s*.8,s*.48,s*.04);X.stroke();X.beginPath();X.moveTo(-s*.12,s*.36);X.lineTo(s*.12,s*.36);X.moveTo(0,s*.2);X.lineTo(0,s*.36);X.stroke()},
 timer(s){X.beginPath();X.arc(0,s*.04,s*.3,0,7);X.stroke();X.beginPath();X.moveTo(-s*.08,-s*.36);X.lineTo(s*.08,-s*.36);X.moveTo(0,-s*.36);X.lineTo(0,-s*.26);X.moveTo(0,s*.04);X.lineTo(s*.12,-s*.1);X.stroke()},
 grid(s){for(let r=0;r<3;r++)for(let c=0;c<3;c++){rr(-s*.34+c*s*.25,-s*.34+r*s*.25,s*.18,s*.18,s*.05);X.stroke()}},
 dumbbell(s){X.beginPath();X.moveTo(-s*.2,0);X.lineTo(s*.2,0);X.stroke();[-1,1].forEach(k=>{rr(k*s*.26-s*.05,-s*.2,s*.1,s*.4,s*.03);X.stroke();rr(k*s*.36-s*.035,-s*.12,s*.07,s*.24,s*.03);X.stroke()})}
});

function phone(x,y,w,h,al=1,col=COL.ink,fill=COL.panel){X.save();X.globalAlpha*=al;X.fillStyle=fill;stroke(col,6);rr(x-w/2,y-h/2,w,h,w*.14);X.fill();X.stroke();X.fillStyle=col;rr(x-w*.12,y-h/2+18,w*.24,10,5);X.fill();X.restore()}
function head(x,y,s,al=1,col=COL.ink){X.save();X.globalAlpha*=al;X.translate(x,y);stroke(col,7);X.beginPath();
 X.moveTo(-s*.1,s*.5);X.lineTo(-s*.1,s*.3);X.bezierCurveTo(-s*.42,s*.24,-s*.44,-s*.1,-s*.34,-s*.26);X.bezierCurveTo(-s*.2,-s*.52,s*.26,-s*.54,s*.36,-s*.2);
 X.lineTo(s*.46,-s*.02);X.lineTo(s*.38,s*.02);X.lineTo(s*.36,s*.22);X.lineTo(s*.2,s*.24);X.lineTo(s*.2,s*.5);X.stroke();X.restore()}
// level meter 0..1; color shifts alert -> gold -> calm
function gauge(x,y,r,v,al=1,label=true){X.save();X.globalAlpha*=al;X.translate(x,y);const a0=Math.PI*0.8,a1=Math.PI*2.2;
 stroke(COL.dim,26);X.save();X.globalAlpha*=0.4;X.beginPath();X.arc(0,0,r,a0,a1);X.stroke();X.restore();
 const col=v<0.35?COL.alert:(v<0.6?COL.gold:COL.calm);stroke(col,26);glow(col,24);X.beginPath();X.arc(0,0,r,a0,a0+(a1-a0)*cl(v));X.stroke();noglow();
 for(let i=0;i<=10;i++){const a=a0+(a1-a0)*i/10;stroke(COL.dim,3);X.beginPath();X.moveTo(Math.cos(a)*(r-40),Math.sin(a)*(r-40));X.lineTo(Math.cos(a)*(r-26),Math.sin(a)*(r-26));X.stroke()}
 const na=a0+(a1-a0)*cl(v);stroke(COL.ink,8);X.beginPath();X.moveTo(0,0);X.lineTo(Math.cos(na)*(r-55),Math.sin(na)*(r-55));X.stroke();dot(0,0,14,COL.ink,0);
 if(label)txt(Math.round(cl(v)*100)+'%',0,r*0.55,Math.round(r*0.3),AR,col);X.restore()}
// clock; turn = number of minute-hand turns completed (0..n); arc shows the current turn
function clockFace(x,y,r,turn,al=1,arcCol=COL.alert){X.save();X.globalAlpha*=al;X.translate(x,y);stroke(COL.ink,7);X.beginPath();X.arc(0,0,r,0,7);X.stroke();
 for(let i=0;i<12;i++){const q=i/12*Math.PI*2;stroke(COL.dim,5);X.beginPath();X.moveTo(Math.cos(q)*r*.84,Math.sin(q)*r*.84);X.lineTo(Math.cos(q)*r*.93,Math.sin(q)*r*.93);X.stroke()}
 const f=turn%1||(turn>0?1:0);stroke(arcCol,r*.12);glow(arcCol,24);X.beginPath();X.arc(0,0,r*.7,-Math.PI/2,-Math.PI/2+Math.PI*2*f);X.stroke();noglow();
 const mn=-Math.PI/2+Math.PI*2*turn,hr=-Math.PI/2+Math.PI/6*turn;stroke(COL.ink,r*.065);X.beginPath();X.moveTo(0,0);X.lineTo(Math.cos(hr)*r*.47,Math.sin(hr)*r*.47);X.stroke();
 stroke(COL.ink,r*.04);X.beginPath();X.moveTo(0,0);X.lineTo(Math.cos(mn)*r*.8,Math.sin(mn)*r*.8);X.stroke();dot(0,0,r*.07,arcCol,10);X.restore()}
function card(x,y,w,h,ap,col=COL.ink){if(ap<=0)return;X.save();X.globalAlpha*=cl(ap*2);X.translate(x,y);const s=back(cl(ap));X.scale(s,s);X.fillStyle=COL.panel;stroke(col,5);rr(-w/2,-h/2,w,h,Math.min(48,h*.2));X.fill();X.stroke();X.restore()}
function strike(x1,y1,x2,y2,p,col=COL.alert){if(p<=0)return;stroke(col,12);glow(col,20);polyP([[x1,y1],[x2,y2]],eo(p));noglow()}
function crosshair(x,y,r,p){if(p<=0)return;const rr_=lerp(r*2.2,r,eo(p));stroke(COL.alert,6);glow(COL.alert,24*p);X.beginPath();X.arc(x,y,rr_,0,7);X.stroke();
 [[0,-1],[0,1],[-1,0],[1,0]].forEach(([dx,dy])=>{X.beginPath();X.moveTo(x+dx*(rr_-40),y+dy*(rr_-40));X.lineTo(x+dx*(rr_+60),y+dy*(rr_+60));X.stroke()});noglow();if(p>0.8)dot(x,y,16,COL.alert,40)}
function wordPop(str,x,y,size,p,col=COL.ink,dir='rtl'){if(p<=0)return;X.save();X.translate(x,y);X.scale(back(p),back(p));txt(str,0,0,size,AR,col,cl(p*2),'center',dir);X.restore()}
function counter(from,to,p,x,y,size,fmt=v=>String(Math.round(v)),col=COL.ink){txt(fmt(lerp(from,to,eio(cl(p)))),x,y,size,AR,col)}
function checkmark(x,y,s,p,col=COL.calm){if(p<=0)return;stroke(col,s*.16);glow(col,20);polyP([[x-s*.4,y],[x-s*.1,y+s*.3],[x+s*.45,y-s*.35]],eo(p));noglow()}
// bars that grow one by one from `start`, every `step` seconds; heights 0..1 of 700px
function weekBars(x0,base,hs,t,start,step,bw=90,gap=30,col=COL.calm){hs.forEach((h,i)=>{const x=x0+i*(bw+gap);stroke(COL.dim,4);rr(x,base-700,bw,700,20);X.stroke();
 const g=eo(pr(t,start+i*step,0.5));X.fillStyle=col;glow(col,20*g);rr(x,base-700*h*g,bw,700*h*g,20);X.fill();noglow()})}
function chainLink(x,y,p,vertical=false,lit=false){if(p<=0)return;X.save();X.translate(x,y);X.scale(back(p),back(p));stroke(lit?COL.sig:COL.ink,14);if(lit)glow(COL.sig,18);X.beginPath();
 if(vertical)X.ellipse(0,0,50,105,0,0,7);else X.ellipse(0,0,110,62,0,0,7);X.stroke();noglow();X.restore()}
function sparkBurst(x,y,p,col=COL.gold,n=14){if(p<=0||p>=1)return;for(let k=0;k<n;k++){const a=k/n*Math.PI*2;const d=80+p*360;dot(x+Math.cos(a)*d,y+Math.sin(a)*d,7*(1-p),col,14)}}
function swipeUp(x,yFrom,yTo,p){if(p<=0||p>=1)return;const y=lerp(yFrom,yTo,eo(p));X.save();X.globalAlpha*=Math.sin(p*Math.PI);stroke(COL.ink,8);X.beginPath();X.moveTo(x,yFrom+40);X.lineTo(x,y);X.stroke();X.beginPath();X.moveTo(x-30,y+30);X.lineTo(x,y);X.lineTo(x+30,y+30);X.stroke();X.restore()}
function loopMark(x,y,s,p,t,col=COL.alert){if(p<=0)return;X.save();X.translate(x,y);X.scale(back(p),back(p));X.rotate(t*2);stroke(col,8);ICON.loop(s);X.restore()}
