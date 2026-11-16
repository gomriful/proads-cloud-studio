// themes.js: ready visual worlds. Load BEFORE engine.js. Pick with: const THEME='blueprint' | 'nightphone' | 'ledger'
// Each theme: col (tokens used by engine/components), bg(t), sweep(t,p) for scene transitions, vignette(), rail color.
// Token meaning: ink=lines/text, panel=filled shapes, sig=main accent (node glow, pulses), alert=negative/strike,
// gold=reward/highlight, calm=positive/recovery, dim=secondary text, bg2=base background.
// To add a world: copy one theme, change tokens + bg motif. Keep token names so components keep working.
const THEMES={
 // Systems, engineering, automation (used in the AI-workflows video)
 blueprint:{
  col:{bg1:'#0F3A66',bg2:'#082647',panel:'#15497D',ink:'#E9F3FC',dim:'rgba(233,243,252,0.35)',sig:'#FFC93C',alert:'#FF7A66',gold:'#FFC93C',calm:'#7FD1F0',hum:'#FF7A66'},
  rail:'rgba(233,243,252,.18)',
  bg(t){const c=this.col;const g=X.createRadialGradient(CX,CY*.9,100,CX,CY,1300);g.addColorStop(0,c.bg1);g.addColorStop(1,c.bg2);X.fillStyle=g;X.fillRect(0,0,W,H);
   const off=(t*8)%40,offM=(t*8)%200;X.lineWidth=1.5;X.strokeStyle='rgba(160,205,245,0.09)';X.beginPath();
   for(let x=-off;x<W;x+=40){X.moveTo(x,0);X.lineTo(x,H)}for(let y=-off;y<H;y+=40){X.moveTo(0,y);X.lineTo(W,y)}X.stroke();
   X.lineWidth=2;X.strokeStyle='rgba(160,205,245,0.18)';X.beginPath();
   for(let x=-offM;x<W;x+=200){X.moveTo(x,0);X.lineTo(x,H)}for(let y=-offM;y<H;y+=200){X.moveTo(0,y);X.lineTo(W,y)}X.stroke();
   stroke('rgba(233,243,252,0.28)',3);X.strokeRect(44,44,W-88,H-88);stroke('rgba(233,243,252,0.14)',2);X.strokeRect(60,60,W-120,H-120);
   [[44,44],[W-44,44],[44,H-44],[W-44,H-44]].forEach(([x,y])=>{stroke('rgba(233,243,252,.5)',3);X.beginPath();X.moveTo(x-18,y);X.lineTo(x+18,y);X.moveTo(x,y-18);X.lineTo(x,y+18);X.stroke()});
   progressRail(t,c.sig)},
  sweep(t,p){const y=lerp(-40,H+40,p);stroke(this.col.sig,5);glow(this.col.sig,40);X.beginPath();X.moveTo(0,y);X.lineTo(W,y);X.stroke();noglow();X.fillStyle='rgba(255,201,60,0.06)';X.fillRect(0,y-160,W,160)},
  vignette(){const g=X.createRadialGradient(CX,CY,500,CX,CY,1250);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(2,12,26,0.55)');X.fillStyle=g;X.fillRect(0,0,W,H)},
  fade:'rgba(4,18,36,A)'
 },
 // Attention, psychology, phones, habits (used in the attention video)
 nightphone:{
  col:{bg2:'#100E24',panel:'#1E1A40',ink:'#F1F0FF',dim:'rgba(241,240,255,0.35)',sig:'#FF4D5E',alert:'#FF4D5E',gold:'#FFC23D',calm:'#7B93FF',hum:'#FF4D5E'},
  rail:'rgba(241,240,255,.15)',
  calmFrom:null, calmTo:null, // set e.g. THEMES.nightphone.calmFrom=35.9 to shift the room light to calm blue
  bg(t){const c=this.col;X.fillStyle=c.bg2;X.fillRect(0,0,W,H);
   const w=(this.calmFrom!=null)?cl(pr(t,this.calmFrom,1.2)*(this.calmTo!=null?1-pr(t,this.calmTo,0.6):1)):0;
   const g=X.createRadialGradient(CX,900,60,CX,960,1150);
   g.addColorStop(0,`rgba(${Math.round(lerp(92,70,w))},${Math.round(lerp(60,95,w))},${Math.round(lerp(170,200,w))},0.55)`);g.addColorStop(1,'rgba(0,0,0,0)');X.fillStyle=g;X.fillRect(0,0,W,H);
   const off=(t*22)%60;X.fillStyle='rgba(241,240,255,0.08)';for(let y=-off;y<H;y+=60)for(let x=30;x<W;x+=60){X.beginPath();X.arc(x,y,2.4,0,7);X.fill()}
   progressRail(t,c.alert)},
  sweep(t,p){const y=lerp(H+60,-60,p);X.fillStyle='rgba(255,77,94,0.08)';X.fillRect(0,y,W,220);stroke(this.col.alert,5);glow(this.col.alert,36);X.beginPath();X.moveTo(0,y);X.lineTo(W,y);X.stroke();noglow()},
  vignette(){const g=X.createRadialGradient(CX,CY,520,CX,CY,1250);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(4,3,14,0.6)');X.fillStyle=g;X.fillRect(0,0,W,H)},
  fade:'rgba(10,8,26,A)'
 },
 // Money, economics, markets, history: light paper ledger (new; preview before first use)
 ledger:{
  col:{bg2:'#EDE6D6',panel:'#F7F2E7',ink:'#1D2A38',dim:'rgba(29,42,56,0.4)',sig:'#C23B22',alert:'#C23B22',gold:'#B8860B',calm:'#2E7D5B',hum:'#C23B22'},
  rail:'rgba(29,42,56,.15)',
  bg(t){const c=this.col;X.fillStyle=c.bg2;X.fillRect(0,0,W,H);
   const off=(t*10)%64;stroke('rgba(29,42,56,0.08)',2);X.beginPath();for(let y=-off;y<H;y+=64){X.moveTo(0,y);X.lineTo(W,y)}X.stroke();
   stroke('rgba(194,59,34,0.35)',3);X.beginPath();X.moveTo(150,0);X.lineTo(150,H);X.stroke();
   // paper grain
   X.fillStyle='rgba(29,42,56,0.035)';for(let i=0;i<220;i++){const x=(i*397)%W,y=(i*733+Math.floor(t*2)*13)%H;X.fillRect(x,y,2,2)}
   progressRail(t,c.sig)},
  sweep(t,p){const x=lerp(-60,W+60,p);X.fillStyle='rgba(194,59,34,0.07)';X.fillRect(x-200,0,200,H);stroke(this.col.sig,5);X.beginPath();X.moveTo(x,0);X.lineTo(x,H);X.stroke()},
  vignette(){const g=X.createRadialGradient(CX,CY,600,CX,CY,1300);g.addColorStop(0,'rgba(0,0,0,0)');g.addColorStop(1,'rgba(60,40,10,0.18)');X.fillStyle=g;X.fillRect(0,0,W,H)},
  fade:'rgba(237,230,214,A)'
 }
};
// closing fade helper usable in the last scene: fadeOut(t)
function fadeOut(t,dur=1.0){const f=pr(t,END-dur,dur);if(f>0){X.fillStyle=THEMES[THEME].fade.replace('A',f);X.fillRect(0,0,W,H)}}
