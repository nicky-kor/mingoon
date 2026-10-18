// 고품질 벡터 일러스트 (그라디언트·음영·질감)
const DEFS = `<svg width="0" height="0" style="position:absolute"><defs>
<linearGradient id="gGray" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e9b98f"/><stop offset="1" stop-color="#b87444"/></linearGradient>
<linearGradient id="gBlueGray" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b7c3dc"/><stop offset="1" stop-color="#6e7fa4"/></linearGradient>
<linearGradient id="gWhite" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#cfd5e3"/></linearGradient>
<linearGradient id="gOrange" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffb877"/><stop offset="1" stop-color="#e2570c"/></linearGradient>
<linearGradient id="gAmber" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffd9a8"/><stop offset="1" stop-color="#f08a2c"/></linearGradient>
<linearGradient id="gPurple" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#cdb4ff"/><stop offset="1" stop-color="#7a4be0"/></linearGradient>
<linearGradient id="gNeck" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3aa88f"/><stop offset=".55" stop-color="#6a5bc4"/><stop offset="1" stop-color="#8a4fb0"/></linearGradient>
<linearGradient id="gSkin" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f4a9b5"/><stop offset="1" stop-color="#d9647c"/></linearGradient>
<linearGradient id="gMouse" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dcdcdc"/><stop offset="1" stop-color="#8e8e8e"/></linearGradient>
<linearGradient id="gGreen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6fcf72"/><stop offset="1" stop-color="#2f8f43"/></linearGradient>
<linearGradient id="gBrown" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#c58a4e"/><stop offset="1" stop-color="#6b4020"/></linearGradient>
<linearGradient id="gSea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6fb4e8"/><stop offset="1" stop-color="#2a5fa8"/></linearGradient>
<linearGradient id="gSky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#dff0fb"/><stop offset="1" stop-color="#fdfdfd"/></linearGradient>
<linearGradient id="gBee" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffe066"/><stop offset="1" stop-color="#f2a900"/></linearGradient>
<radialGradient id="rJelly" cx=".35" cy=".3" r=".8"><stop offset="0" stop-color="#ffffff"/><stop offset=".5" stop-color="#d9f3e6"/><stop offset="1" stop-color="#8fcfae"/></radialGradient>
<radialGradient id="rPink" cx=".4" cy=".3" r=".9"><stop offset="0" stop-color="#ff9fb5"/><stop offset="1" stop-color="#d63a63"/></radialGradient>
<radialGradient id="rLens" cx=".35" cy=".3" r=".9"><stop offset="0" stop-color="#e7f1ff"/><stop offset="1" stop-color="#7fa8ea"/></radialGradient>
<radialGradient id="rEye" cx=".5" cy=".5" r=".6"><stop offset="0" stop-color="#2a1500"/><stop offset=".45" stop-color="#2a1500"/><stop offset=".5" stop-color="#ff8a00"/><stop offset="1" stop-color="#d95f00"/></radialGradient>
<linearGradient id="gEle" gradientUnits="userSpaceOnUse" x1="0" y1="-100" x2="0" y2="125"><stop offset="0" stop-color="#c3c6cd"/><stop offset="1" stop-color="#6c707a"/></linearGradient>
<filter id="fuzz" x="-20%" y="-20%" width="140%" height="140%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="7"/></filter>
<filter id="soft" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3"/></filter>
</defs></svg>`;
const OL = '#262626';
const sh = (cx,cy,rx,ry,op=.14)=>`<ellipse cx="${cx}" cy="${cy}" rx="${rx}" ry="${ry}" fill="#000" opacity="${op}" filter="url(#soft)"/>`;

// ---------- 비둘기 (오른쪽을 봄) ----------
function pigeon(x,y,s,o={}){
  const body = o.fill||'url(#gBlueGray)';
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(5,100,110,10,.18);
  // 다리
  [[0],[30]].forEach(([dx])=>{g+=`<path d="M${-6+dx},52 L${-10+dx},92" stroke="#c94d68" stroke-width="7" fill="none"/><path d="M${-10+dx},92 L${-30+dx},98 M${-10+dx},92 L${8+dx},98 M${-10+dx},92 L${-14+dx},101" stroke="#c94d68" stroke-width="5" fill="none"/>`});
  // 꼬리
  if(o.v==='fan'){for(let i=-4;i<=4;i++)g+=`<path d="M-72,18 C-110,2 -160,2 -196,18 C-160,38 -112,36 -72,30Z" fill="${body}" transform="rotate(${i*10-34} -72 24)"/>`;}
  else {for(let i=-2;i<=2;i++)g+=`<path d="M-72,18 C-110,12 -150,18 -176,34 C-150,46 -108,40 -72,30Z" fill="${body}" transform="rotate(${i*5+8} -72 24)"/>`;}
  // 몸통
  g+=`<path d="M-88,14 C-98,-26 -58,-56 -6,-56 C40,-56 80,-42 94,-12 C102,14 86,42 46,54 C4,64 -46,60 -74,42 C-84,34 -88,24 -88,14Z" fill="${body}"/>`;
  if(o.v==='pout') g+=`<ellipse cx="62" cy="-6" rx="52" ry="54" fill="url(#gAmber)"/><path d="M34,-34 C50,-50 76,-48 90,-30" fill="none" stroke="#fff" stroke-width="5" opacity=".5"/>`;
  // 목 (무지갯빛)
  if(o.v!=='pout') g+=`<ellipse cx="74" cy="-40" rx="34" ry="30" transform="rotate(-30 74 -40)" fill="${o.v==='fan'?'url(#gWhite)':o.v==='carrier'?'url(#gPurple)':'url(#gNeck)'}" stroke="none"/>`;
  // 날개
  g+=`<path d="M-66,-22 C-24,-50 44,-42 76,-12 C46,10 -12,22 -78,12 C-82,-2 -76,-14 -66,-22Z" fill="${o.wing||'url(#gBlueGray)'}"/>`;
  g+=`<g fill="none" stroke="#fff" opacity=".35" stroke-width="2"><path d="M-60,-8 C-20,-26 30,-24 62,-6"/><path d="M-62,2 C-20,-14 30,-10 56,4"/></g>`;
  if(o.v==='rock'||!o.v) g+=`<path d="M-22,-34 L-12,10 M12,-38 L24,6" stroke="#1d1d1d" stroke-width="9" fill="none"/>`;
  // 머리
  const hx=o.v==='pout'?104:100, hy=o.v==='pout'?-90:-76;
  g+=`<circle cx="${hx}" cy="${hy}" r="25" fill="${o.v==='fan'?'url(#gWhite)':o.v==='carrier'?'url(#gPurple)':o.v==='pout'?'url(#gAmber)':'url(#gBlueGray)'}"/>`;
  // 부리
  g+=`<path d="M${hx+20},${hy-6} L${hx+50},${hy+2} L${hx+20},${hy+8}Z" fill="#efe3cf"/><path d="M${hx+20},${hy+1} L${hx+48},${hy+2}" stroke="${OL}" stroke-width="1.6"/>`;
  if(o.v==='carrier'){g+=`<path d="M${hx+16},${hy-12} C${hx+26},${hy-26} ${hx+42},${hy-18} ${hx+36},${hy-6} C${hx+30},${hy} ${hx+20},${hy} ${hx+16},${hy-12}Z" fill="#f4efe6"/><circle cx="${hx+4}" cy="${hy-6}" r="15" fill="none" stroke="#f4efe6" stroke-width="7"/>`;}
  else g+=`<ellipse cx="${hx+22}" cy="${hy-8}" rx="6" ry="4" fill="#f6f0e6" stroke-width="1.6"/>`;
  // 눈
  g+=`<circle cx="${hx+5}" cy="${hy-6}" r="8" fill="url(#rEye)" stroke-width="1.6"/><circle cx="${hx+7}" cy="${hy-8}" r="2.4" fill="#fff" stroke="none"/>`;
  return g+`</g>`;
}

// ---------- 코끼리 (오른쪽을 봄) ----------
function elephant(x,y,s,o={}){
  const f='url(#gEle)';
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(10,122,150,12,.2);
  g+=`<path d="M-128,-20 C-150,0 -148,40 -140,70" fill="none" stroke-width="5"/><path d="M-140,66 l-8,16 M-140,66 l2,18 M-140,66 l12,14" fill="none" stroke-width="3"/>`;
  // 뒤쪽 다리(어둡게)
  g+=`<path d="M-92,30 L-92,108 Q-92,122 -76,122 L-50,122 Q-36,122 -36,108 L-36,34Z" fill="${f}"/><path d="M52,30 L52,108 Q52,122 68,122 L92,122 Q106,122 106,108 L106,34Z" fill="${f}"/><path d="M-92,30 L-92,108 Q-92,122 -76,122 L-50,122 Q-36,122 -36,108 L-36,34Z M52,30 L52,108 Q52,122 68,122 L92,122 Q106,122 106,108 L106,34Z" fill="#000" opacity=".16" stroke="none"/>`;
  // 앞다리
  g+=`<path d="M-62,34 L-62,110 Q-62,124 -46,124 L-20,124 Q-6,124 -6,110 L-6,38Z" fill="${f}"/><path d="M26,34 L26,110 Q26,124 42,124 L66,124 Q80,124 80,110 L80,38Z" fill="${f}"/>`;
  g+=`<g fill="#efe7da" stroke-width="1.8"><path d="M-56,119 q5,7 11,0 M-34,119 q5,7 11,0 M32,119 q5,7 11,0 M54,119 q5,7 11,0"/></g>`;
  // 몸통: 채움(테두리 없음) + 윗선만 윤곽
  g+=`<path d="M-132,-12 C-136,-70 -70,-100 10,-98 C80,-96 126,-62 134,-8 C138,24 132,48 118,60 L-120,60 C-130,44 -132,10 -132,-12Z" fill="${f}" stroke="none"/>`;
  g+=`<path d="M-120,56 C-130,44 -132,10 -132,-12 C-136,-70 -70,-100 10,-98 C80,-96 126,-62 134,-8 C138,24 132,44 122,56" fill="none"/>`;
  g+=`<ellipse cx="140" cy="-34" rx="52" ry="56" fill="${f}"/>`;
  g+=`<path d="M120,-86 C70,-96 60,-30 88,20 C112,22 140,0 138,-40 C138,-60 130,-76 120,-86Z" fill="${f}"/><path d="M114,-72 C84,-74 80,-30 98,6 C116,6 126,-14 126,-40 C126,-56 122,-66 114,-72Z" fill="url(#gSkin)" stroke="none" opacity=".75"/>`;
  g+=`<path d="M164,-48 C206,-34 212,24 198,62 C194,82 168,84 166,68 C176,40 164,8 150,-8Z" fill="${f}"/><g fill="none" stroke="${OL}" stroke-width="1.6" opacity=".5"><path d="M168,-20 q16,4 24,0 M170,0 q16,4 26,0 M170,20 q14,4 24,0 M172,40 q12,4 20,0"/></g>`;
  g+=`<path d="M158,-6 C190,0 212,14 220,-6 C214,22 186,20 158,4Z" fill="#faf5e8"/>`;
  g+=`<circle cx="148" cy="-54" r="6" fill="#222" stroke="none"/><circle cx="150" cy="-56" r="2" fill="#fff" stroke="none"/>`;
  g+=`<g fill="none" stroke="${OL}" stroke-width="1.6" opacity=".3"><path d="M-100,-40 q40,-20 90,-10 M-90,-10 q50,-18 110,-6 M-110,20 q50,-14 120,-2"/></g>`;
  return g+`</g>`;
}

// ---------- 고양이 (정면 상반신) ----------
function cat(x,y,s){
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.6" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(0,98,70,8,.18);
  g+=`<path d="M-62,96 C-70,50 -46,24 0,24 C46,24 70,50 62,96Z" fill="url(#gOrange)"/>`;
  g+=`<path d="M-66,-20 L-62,-84 L-20,-52Z" fill="url(#gOrange)"/><path d="M66,-20 L62,-84 L20,-52Z" fill="url(#gOrange)"/><path d="M-58,-30 L-56,-68 L-34,-50Z" fill="url(#gSkin)" stroke="none"/><path d="M58,-30 L56,-68 L34,-50Z" fill="url(#gSkin)" stroke="none"/>`;
  g+=`<ellipse cx="0" cy="-8" rx="72" ry="62" fill="url(#gOrange)"/>`;
  g+=`<g fill="none" stroke="#9a3c05" stroke-width="5" opacity=".7"><path d="M-14,-66 L-14,-44 M0,-70 L0,-42 M14,-66 L14,-44"/><path d="M-72,-10 L-50,-8 M-70,10 L-50,6 M72,-10 L50,-8 M70,10 L50,6"/></g>`;
  g+=`<ellipse cx="0" cy="14" rx="30" ry="22" fill="#fff4e4" stroke="none" opacity=".9"/>`;
  [-26,26].forEach(ex=>g+=`<ellipse cx="${ex}" cy="-10" rx="13" ry="14" fill="#9be15d" stroke-width="2"/><ellipse cx="${ex}" cy="-10" rx="4.5" ry="11" fill="#1a1a1a" stroke="none"/><circle cx="${ex+4}" cy="-15" r="3" fill="#fff" stroke="none"/>`);
  g+=`<path d="M-7,6 L7,6 L0,15Z" fill="#e9778f"/><path d="M0,15 L0,22 M0,22 Q-10,30 -18,24 M0,22 Q10,30 18,24" fill="none" stroke-width="2.2"/>`;
  g+=`<g stroke="#fff" stroke-width="2.4" fill="none"><path d="M-30,16 L-86,8 M-30,22 L-86,26 M30,16 L86,8 M30,22 L86,26"/></g><g stroke="${OL}" stroke-width="1" fill="none" opacity=".5"><path d="M-86,8 L-86,8"/></g>`;
  return g+`</g>`;
}

// ---------- 들쥐 (오른쪽을 봄) ----------
function mouse(x,y,s){
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(0,52,80,7,.18);
  g+=`<path d="M-62,18 C-100,30 -110,-10 -86,-30" fill="none" stroke="#d7869a" stroke-width="6"/>`;
  g+=`<path d="M-66,12 C-70,-34 -26,-52 14,-46 C46,-42 70,-24 78,-6 L92,2 L78,10 C60,38 20,50 -20,48 C-48,46 -64,34 -66,12Z" fill="url(#gMouse)"/>`;
  g+=`<ellipse cx="22" cy="-42" rx="22" ry="26" fill="url(#gMouse)"/><ellipse cx="22" cy="-42" rx="14" ry="18" fill="url(#gSkin)" stroke="none"/>`;
  g+=`<path d="M-40,22 C-20,34 30,34 62,18" fill="none" stroke="#fff" opacity=".45" stroke-width="3"/>`;
  g+=`<circle cx="94" cy="2" r="5" fill="#e9778f"/><circle cx="58" cy="-12" r="6" fill="#1a1a1a" stroke="none"/><circle cx="60" cy="-14" r="2" fill="#fff" stroke="none"/>`;
  g+=`<g stroke="#fff" stroke-width="1.8" fill="none"><path d="M80,4 L118,-6 M80,8 L118,12 M78,12 L112,28"/></g><g stroke="#555" stroke-width="1" fill="none"/>`;
  g+=`<path d="M10,44 l-6,8 M32,44 l8,8 M-30,44 l-4,8" stroke="#d7869a" stroke-width="5" fill="none"/>`;
  return g+`</g>`;
}

// ---------- 뒤영벌 (털북숭이) ----------
function bee(x,y,s){
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(0,70,70,8,.16);
  g+=`<g fill="#e8f2ff" fill-opacity=".75" stroke="#7c8fb0" stroke-width="2"><ellipse cx="-14" cy="-52" rx="22" ry="42" transform="rotate(-24 -14 -52)"/><ellipse cx="22" cy="-56" rx="20" ry="40" transform="rotate(14 22 -56)"/></g><g stroke="#7c8fb0" stroke-width="1.2" fill="none"><path d="M-14,-84 L-14,-24 M22,-88 L22,-26"/></g>`;
  g+=`<g stroke="${OL}" stroke-width="2.4"><path d="M-14,36 L-24,64 M6,40 L8,68 M26,34 L38,60" fill="none" stroke-width="4"/></g>`;
  g+=`<g filter="url(#fuzz)">`;
  g+=`<ellipse cx="-6" cy="0" rx="64" ry="46" fill="url(#gBee)"/>`;
  g+=`<path d="M-4,-46 C16,-40 22,40 -4,46 C-20,44 -26,-40 -4,-46Z" fill="#1c1c1c" transform="translate(6 0)"/>`;
  g+=`<path d="M-62,-14 C-48,-40 -34,-44 -30,-42 L-30,42 C-48,40 -62,16 -62,-14Z" fill="#1c1c1c" opacity=".92"/>`;
  g+=`<circle cx="58" cy="-6" r="26" fill="#2a2a2a"/>`;
  g+=`</g>`;
  g+=`<circle cx="66" cy="-14" r="6" fill="#111"/><circle cx="68" cy="-16" r="2" fill="#fff"/><path d="M72,-26 C84,-48 100,-52 106,-46 M62,-28 C66,-52 80,-62 90,-60" fill="none" stroke="#222" stroke-width="3"/>`;
  g+=`<path d="M80,-2 C96,2 100,16 92,24" fill="none" stroke="#e8590c" stroke-width="5"/>`;
  return g+`</g>`;
}

// ---------- 붉은 클로버 ----------
function clover(x,y,s){
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(0,98,60,7,.14);
  g+=`<path d="M0,30 C4,60 -2,80 0,96" fill="none" stroke="#2f8f43" stroke-width="7"/>`;
  [[-44,64,-24],[44,64,24],[0,86,0]].forEach(([lx,ly,r])=>{
    g+=`<g transform="translate(${lx},${ly}) rotate(${r})"><path d="M0,0 C-26,-6 -30,-34 0,-36 C30,-34 26,-6 0,0Z" fill="url(#gGreen)" stroke="#1f6b31" stroke-width="2" transform="translate(0,-4)"/><path d="M-12,-26 Q0,-16 12,-26" fill="none" stroke="#d9f4d4" stroke-width="3" opacity=".8"/></g>`});
  g+=`<ellipse cx="0" cy="-26" rx="40" ry="52" fill="#b03a5c" opacity=".35" filter="url(#soft)"/>`;
  g+=`<g stroke="#8a1f45" stroke-width="1.4">`;
  const rows=[[-62,2],[-48,3],[-34,4],[-20,4],[-6,4],[8,4],[22,3],[34,2]];
  rows.forEach(([ry,n],ri)=>{for(let i=0;i<n;i++){const w=[0,26,38,44,44,44,38,26][ri]||30;const cx=n>1?-w/2*1+ (w*2/ (n-1))*i - w/2 +w/2 -w/2:0;
    g+=`<ellipse cx="${((i-(n-1)/2)*18)}" cy="${ry}" rx="9" ry="13" fill="url(#rPink)" transform="rotate(${(i-(n-1)/2)*14} ${((i-(n-1)/2)*18)} ${ry})"/>`}});
  g+=`</g>`;
  return g+`</g>`;
}

// ---------- 개구리 알 ----------
function frogegg(x,y,s=1){
  let g=`<g transform="translate(${x},${y}) scale(${s})">`+sh(0,34,60,7,.14);
  const pts=[[-30,6],[0,10],[30,4],[-14,-18],[16,-16],[-44,-14],[46,-12],[0,-40],[-30,-38],[30,-38]];
  pts.forEach(([px,py],i)=>{g+=`<g transform="translate(${px},${py})"><circle r="19" fill="url(#rJelly)" stroke="#5fae8a" stroke-width="1.8"/><circle r="7" cx="${(i%3)-1}" cy="${(i%2)}" fill="#1f2a24"/><ellipse cx="-7" cy="-9" rx="6" ry="3.5" fill="#fff" opacity=".85" transform="rotate(-30 -7 -9)"/></g>`});
  return g+`</g>`;
}

// ---------- 박쥐 ----------
function bat(x,y,s){
  let g=`<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">`;
  g+=sh(0,66,90,7,.14);
  g+=`<path d="M-12,-8 C-50,-52 -110,-40 -140,-6 L-120,6 L-102,0 L-84,16 L-62,6 L-40,26 L-14,18Z" fill="url(#gPurple)"/><path d="M12,-8 C50,-52 110,-40 140,-6 L120,6 L102,0 L84,16 L62,6 L40,26 L14,18Z" fill="url(#gPurple)"/>`;
  g+=`<g fill="none" stroke="#3b1f86" stroke-width="2.2"><path d="M-14,-4 L-140,-6 M-14,-2 L-102,0 M-14,4 L-62,6 M14,-4 L140,-6 M14,-2 L102,0 M14,4 L62,6"/></g>`;
  g+=`<ellipse cx="0" cy="12" rx="18" ry="30" fill="#5a4a6e"/><circle cx="0" cy="-22" r="18" fill="#6b5a80"/><path d="M-14,-34 L-16,-56 L-3,-38Z M14,-34 L16,-56 L3,-38Z" fill="#6b5a80"/><circle cx="-6" cy="-24" r="3.5" fill="#fff" stroke-width="1.4"/><circle cx="6" cy="-24" r="3.5" fill="#fff" stroke-width="1.4"/><circle cx="-6" cy="-24" r="1.6" fill="#111" stroke="none"/><circle cx="6" cy="-24" r="1.6" fill="#111" stroke="none"/><path d="M-4,-14 L4,-14 L0,-9Z" fill="#e9778f" stroke-width="1.4"/>`;
  return g+`</g>`;
}

// ---------- 씨앗(싹) ----------
function seed(x,y,s){
  return `<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">${sh(0,56,40,6,.16)}
  <path d="M0,-6 C6,-44 34,-76 62,-84 C64,-56 46,-30 18,-10" fill="none" stroke="#2f8f43" stroke-width="7"/>
  <path d="M56,-90 C82,-100 100,-82 94,-64 C70,-62 56,-74 56,-90Z" fill="url(#gGreen)" stroke="#1f6b31"/>
  <path d="M-34,16 C-34,-22 -4,-36 18,-30 C40,-22 40,26 6,50 C-18,58 -34,40 -34,16Z" fill="url(#gBrown)"/>
  <ellipse cx="-12" cy="-4" rx="9" ry="18" fill="#fff" opacity=".28" transform="rotate(22 -12 -4)" stroke="none"/><path d="M-26,34 C-10,48 14,46 26,30" fill="none" stroke="#3d2310" stroke-width="2" opacity=".5"/></g>`;
}
// ---------- 오리 발 + 달팽이 ----------
function duckfoot(x,y,s){
  return `<g transform="translate(${x},${y}) scale(${s})" stroke="${OL}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round">${sh(0,64,70,6,.14)}
  <path d="M-9,-78 L9,-78 L9,-14 L-9,-14Z" fill="url(#gOrange)"/>
  <path d="M0,-14 L-74,52 Q-60,66 -37,58 Q-18,72 0,62 Q18,72 37,58 Q60,66 74,52Z" fill="url(#gAmber)"/>
  <g fill="none" stroke="#b5510a" stroke-width="5"><path d="M0,-14 L-74,52 M0,-14 L0,62 M0,-14 L74,52"/></g>
  <g transform="translate(40,-36)"><path d="M-22,12 C-26,-6 -16,-20 0,-22 C16,-24 28,-8 24,6 C22,18 8,22 -4,18 C-14,16 -20,12 -22,12Z" fill="url(#gAmber)"/><path d="M2,-2 m-3,0 a3,3 0 1 1 3,3 a7,7 0 1 1 -7,-7 a11,11 0 1 1 11,11" fill="none" stroke="#7a3a08" stroke-width="2.4"/><path d="M-20,14 C-32,22 -38,18 -44,12 M-32,14 C-42,4 -42,-8 -36,-14" fill="#e8d8c0" stroke="#8a7a60" stroke-width="2.4"/></g></g>`;
}

// ---------- 눈 단면 ----------
function eyeStage(i,cx,cy){
  const ray=(x1,y1,x2,y2)=>`<path d="M${x1},${y1} L${x2},${y2}" stroke="#f28c28" stroke-width="3" fill="none" stroke-linecap="round"/>`;
  const dots=(pts)=>pts.map(p=>`<circle cx="${p[0]}" cy="${p[1]}" r="5.5" fill="url(#rPink)" stroke="#8a1f45" stroke-width="1.2"/>`).join('');
  let g=`<g transform="translate(${cx},${cy})" stroke-linecap="round" stroke-linejoin="round">`;
  if(i===0){
    g+=ray(-40,-120,-40,-46)+ray(0,-120,0,-46)+ray(40,-120,40,-46);
    g+=`<rect x="-92" y="-34" width="184" height="24" rx="12" fill="url(#gGray)" stroke="${OL}" stroke-width="2.4"/>`+dots([-66,-33,0,33,66].map(x=>[x,-40]));
  } else if(i===1){
    g+=ray(-40,-120,-30,-30)+ray(0,-120,0,-10)+ray(40,-120,30,-30);
    g+=`<path d="M-92,-50 Q0,70 92,-50" fill="none" stroke="url(#gGray)" stroke-width="22"/><path d="M-92,-50 Q0,70 92,-50" fill="none" stroke="${OL}" stroke-width="2.4" transform="translate(0,-11)"/>`+dots([-60,-30,0,30,60].map(x=>[x,18-Math.abs(x)*0.0+ (-Math.abs(x)*0.38)+0]));
  } else {
    // 구형 눈: 구멍, 막, 렌즈
    g+=`<circle cx="0" cy="10" r="74" fill="${i>=3?'#eaf3ff':'#f7f7f7'}" stroke="none"/>`;
    g+=`<path d="M-26,-58 A74 74 0 1 0 26,-58" fill="none" stroke="url(#gGray)" stroke-width="22"/><path d="M-26,-58 A74 74 0 1 0 26,-58" fill="none" stroke="${OL}" stroke-width="2.4" transform="translate(0,0)" opacity=".0"/>`;
    const a=[-52,-26,0,26,52].map(a=>a*Math.PI/180);
    g+=dots(a.map(t=>[Math.sin(t)*70,10+Math.cos(t)*70]));
    if(i===2){g+=ray(-6,-120,-3,-60)+ray(6,-120,3,-60)+`<path d="M-3,-60 L-20,60 M3,-60 L20,60" stroke="#f28c28" stroke-width="3" fill="none" opacity=".8"/>`;}
    if(i===3){g+=`<path d="M-26,-62 Q0,-90 26,-62 Q0,-72 -26,-62Z" fill="#9ec3ff" stroke="#4f7fd0" stroke-width="2"/>`+ray(-10,-120,-5,-70)+ray(10,-120,5,-70)+`<path d="M-5,-70 L-12,62 M5,-70 L12,62" stroke="#f28c28" stroke-width="3" fill="none" opacity=".8"/>`;}
    if(i===4){g+=`<ellipse cx="0" cy="-60" rx="34" ry="20" fill="url(#rLens)" stroke="#2c5fb3" stroke-width="2.4"/><ellipse cx="-10" cy="-66" rx="12" ry="5" fill="#fff" opacity=".8" transform="rotate(-15 -10 -66)"/>`+ray(-40,-120,-26,-70)+ray(0,-120,0,-80)+ray(40,-120,26,-70)+`<path d="M-26,-70 L0,78 M0,-80 L0,78 M26,-70 L0,78" stroke="#f28c28" stroke-width="3" fill="none"/><circle cx="0" cy="80" r="6" fill="#f28c28"/>`;}
  }
  return g+`</g>`;
}
