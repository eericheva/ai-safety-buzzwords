# -*- coding: utf-8 -*-
"""Assemble taxonomy.html — ONE unified grouping map of the 125 buzzwords.
Three independent controls: Layout (position), Colour, Size (radius)."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


LBL = {"curated": "Curated", "raw2": "Mined phrases", "openalex": "OpenAlex keywords"}


def main():
    curated = json.load(open(os.path.join(HERE, "data", "taxonomy_map.json")))
    curated["label"] = LBL["curated"]
    sources = {"curated": curated}
    for s in ("raw2", "openalex"):
        p = os.path.join(HERE, "data", "src_" + s, "taxonomy_map.json")
        if os.path.exists(p):
            sd = json.load(open(p)); sd["label"] = LBL[s]; sources[s] = sd
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(sources, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "web", "taxonomy.html")
    open(out, "w").write(html)
    print(f"wrote {out} ({os.path.getsize(out)/1024:.0f} KB) sources={list(sources)}")


TEMPLATE = r"""<title>AI Safety Buzzwords — one map, many groupings</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --paper:#faf9f6;--plane:#f2f1ec;--card:#ffffff;
  --ink:#171613;--ink2:#57544d;--muted:#8a877f;
  --line:#e4e1d8;--line2:#d3cfc4;--accent:#1f5fb0;--accent-soft:#e7eef8;--gap:#c14a1f;
  --shadow:0 1px 2px rgba(23,22,19,.05),0 8px 24px -12px rgba(23,22,19,.12);
}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){
  --paper:#141413;--plane:#0e0e0d;--card:#1c1c1a;
  --ink:#f4f2ec;--ink2:#c0bdb2;--muted:#8f8c83;
  --line:#2b2a27;--line2:#3a3934;--accent:#5598e7;--accent-soft:#1b2739;--gap:#eb6834;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
}}
:root[data-theme=dark]{
  --paper:#141413;--plane:#0e0e0d;--card:#1c1c1a;
  --ink:#f4f2ec;--ink2:#c0bdb2;--muted:#8f8c83;
  --line:#2b2a27;--line2:#3a3934;--accent:#5598e7;--accent-soft:#1b2739;--gap:#eb6834;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);font-size:16px;line-height:1.55;
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}
h1,h2{text-wrap:balance;margin:0;line-height:1.14}
a{color:var(--accent)}
.eyebrow{font:600 12px/1.4 ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.themebtn{position:fixed;top:14px;right:14px;z-index:30;width:38px;height:38px;border-radius:10px;
  border:1px solid var(--line2);background:var(--card);color:var(--ink);cursor:pointer;font-size:16px;box-shadow:var(--shadow)}
.nav{display:flex;gap:6px;align-items:center;padding:10px 0}
.nav a{display:flex;align-items:center;gap:6px;text-decoration:none;font:600 13px/1 system-ui;
  color:var(--ink2);border:1px solid var(--line2);background:var(--card);border-radius:9px;padding:8px 12px}
.nav a.cur{color:var(--ink);border-color:var(--accent);background:var(--accent-soft)}
.nav .sep{flex:1}
header{border-bottom:1px solid var(--line);background:linear-gradient(180deg,var(--paper),var(--plane))}
.hero{padding:40px 0 26px;display:grid;gap:14px}
.hero h1{font-size:clamp(28px,4.4vw,46px);font-weight:800;letter-spacing:-.02em}
.hero h1 em{font-style:normal;color:var(--accent)}
.lead{max-width:70ch;color:var(--ink2);font-size:16.5px}
.findings{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:6px}
.finding{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:12px;padding:12px 14px;box-shadow:var(--shadow)}
.finding h4{font-size:12.5px;margin:0 0 4px;color:var(--accent);letter-spacing:.02em}
.finding p{margin:0;font-size:13px;color:var(--ink2)}

/* control bar */
.bar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 90%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.bar-in{display:flex;flex-wrap:wrap;gap:16px 22px;align-items:center;padding:12px 0}
.ctl{display:flex;align-items:center;gap:9px}
.ctl>.eyebrow{color:var(--muted)}
.seg{display:inline-flex;background:var(--plane);border:1px solid var(--line);border-radius:10px;padding:3px;flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--ink2);font:600 12.5px/1 system-ui;padding:7px 10px;border-radius:7px;cursor:pointer}
.seg button.on{background:var(--card);color:var(--ink);box-shadow:var(--shadow)}

section{padding:26px 0 40px}
.mapcard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:8px;box-shadow:var(--shadow)}
.map{width:100%;height:640px;display:block}
.map circle{cursor:pointer}
@media (prefers-reduced-motion:no-preference){
  .map circle{transition:cx .55s cubic-bezier(.4,0,.2,1),cy .55s cubic-bezier(.4,0,.2,1),r .3s,fill .25s,opacity .15s}
}
.map .glabel{fill:var(--ink);font:600 13px/1 system-ui;paint-order:stroke;
  stroke:var(--card);stroke-width:3px;stroke-linejoin:round;pointer-events:none}
.legend{display:flex;flex-wrap:wrap;gap:7px 14px;margin-top:14px;align-items:center}
.legend .cap{font:600 12px/1 ui-monospace,monospace;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.lg{display:flex;align-items:center;gap:7px;font-size:12.5px;color:var(--ink2)}
.lg .sw{width:11px;height:11px;border-radius:3px}
.hint{color:var(--muted);font-size:13px;margin:14px 2px 0;max-width:90ch}
.hint b{color:var(--ink2)}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--gap);border-radius:12px;
  padding:13px 15px;color:var(--ink2);font-size:13.5px;margin-top:22px}
.note b{color:var(--ink)}
#tip{position:fixed;z-index:40;pointer-events:none;opacity:0;transition:opacity .1s;background:var(--ink);
  color:var(--paper);padding:8px 11px;border-radius:9px;font-size:12.5px;box-shadow:var(--shadow);max-width:280px}
#tip .tv{font-weight:700}#tip .sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px}
#tip .row{display:flex;justify-content:space-between;gap:16px}
footer{padding:30px 0 60px;color:var(--muted);font-size:13px}
@media (max-width:760px){.findings{grid-template-columns:1fr}}
</style>

<button class="themebtn" id="themebtn" aria-label="Toggle theme">◐</button>
<div id="tip"></div>

<div class="wrap"><nav class="nav">
  <a href="https://claude.ai/code/artifact/925356f2-6bd0-48bd-931e-4da6525c7b00">🧭 Word cloud</a>
  <a href="https://claude.ai/code/artifact/77473750-146a-4348-a4c1-5d476b986789">📈 Trends</a>
  <a class="cur" href="#">🗂️ Groupings</a>
  <span class="sep"></span><span class="eyebrow" style="align-self:center">Source</span>
  <div class="seg" id="srcseg"></div>
</nav></div>

<header><div class="wrap hero">
  <div class="eyebrow" id="eyebrow">125 buzzwords · one map · three controls</div>
  <h1>One map, <em>many groupings</em></h1>
  <p class="lead">Every buzzword is a dot. <b>Layout</b> arranges the dots in space by one grouping;
  <b>Colour</b> paints them by another; <b>Size</b> scales them by a metric. Set layout and colour to the
  <em>same</em> lens to see clean clusters; set them <em>differently</em> to see how one grouping cuts across another.</p>
  <div class="findings" id="findings">
    <div class="finding"><h4>THEMES MOSTLY HOLD</h4><p>Layout by co-occurrence or meaning, colour by glossary theme — the colours stay clumped. The manual themes aren’t arbitrary.</p></div>
    <div class="finding"><h4>ONE BIG MERGE</h4><p>In the co-occurrence layout, alignment + agents + oversight collapse into one blob: the literature writes about them together.</p></div>
    <div class="finding"><h4>A REAL GAP</h4><p>Layout by MIT risk: every empty region is socioeconomic (labour, inequality, governance). Our vocabulary is model-centric.</p></div>
  </div>
</div></header>

<div class="bar"><div class="wrap bar-in">
  <div class="ctl"><span class="eyebrow">Layout</span><div class="seg" id="layoutseg"></div></div>
  <div class="ctl"><span class="eyebrow">Colour</span><div class="seg" id="colourseg"></div></div>
  <div class="ctl"><span class="eyebrow">Size</span><div class="seg" id="sizeseg"></div></div>
</div></div>

<div class="wrap">
  <section>
    <div class="mapcard"><svg class="map" id="map" preserveAspectRatio="xMidYMid meet"></svg></div>
    <div class="legend" id="legend"></div>
    <p class="hint" id="hint"></p>
    <div class="note" id="mitnote"></div>
  </section>
</div>

<footer><div class="wrap">
  One scatter, 125 dots · position = layout lens, colour = colour lens, size ≈ √metric ·
  semantic layout = SPECTER2 embeddings (PCA); glossary / MIT / co-occurrence layouts = grouped packing.
</div></footer>

<script>
const SOURCES = /*__DATA__*/;
let curSource='curated';
let D = SOURCES[curSource], T = D.terms, LM = D.lens_meta, termMap = {};
function buildMaps(){ T=D.terms; LM=D.lens_meta; termMap={}; T.forEach(t=>termMap[t.term]=t); }
buildMaps();
const isDark=()=>document.documentElement.getAttribute('data-theme')==='dark'||
  (!document.documentElement.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);
const fmt=n=>n>=1000?(n/1000).toFixed(n>=10000?0:1)+'k':''+n;
const WSHORT={papers:'Papers',citations:'Citations',cpp:'Cit/paper',recency:'Recency',momentum:'Momentum',debut:'Debut yr',peak:'Peak yr'};
const YEARM=k=>k==='debut'||k==='peak';
const defLayout=()=>D.layouts.semantic?'semantic':Object.keys(D.layouts)[0];
const defColour=()=>LM.glossary?'glossary':Object.keys(LM)[0];
let state={layout:defLayout(),colour:defColour(),size:'papers'};

const tip=document.getElementById('tip');
function showTip(h,x,y){tip.innerHTML=h;tip.style.opacity=1;const w=tip.offsetWidth,ht=tip.offsetHeight;
  tip.style.left=Math.min(x+14,innerWidth-w-8)+'px';tip.style.top=Math.max(8,y-ht-12)+'px';}
const hideTip=()=>tip.style.opacity=0;

const colours=()=>{const m=LM[state.colour];return isDark()?m.colors_dark:m.colors;};
const grp=(t,lens)=>t.lenses[lens];
const mval=t=>t.m[state.size];
const svVal=t=>YEARM(state.size)?Math.max((t.m[state.size]||2005)-2004,1):(t.m[state.size]||0);
const mfmt=(k,v)=>YEARM(k)?''+(v||'—'):k==='cpp'?(+v).toFixed(1):k==='recency'?v+'%':fmt(v);

function radiusScale(){
  const vals=T.map(svVal); const mx=Math.max(...vals)||1;
  return v=>4 + 22*Math.sqrt(Math.max(v,0)/mx);
}

function segs(){
  const lensBtns=(id,cur,keys)=>{
    document.getElementById(id).innerHTML=keys.map(k=>
      `<button data-k="${k}" class="${k===cur?'on':''}">${LM[k]?LM[k].label.replace(' theme','').replace(' risk domain',' risk').replace(' cluster','').replace(' community',''):k}</button>`).join('');
  };
  lensBtns('layoutseg',state.layout,Object.keys(LM));
  lensBtns('colourseg',state.colour,Object.keys(LM));
  document.getElementById('sizeseg').innerHTML=D.weight_metrics.map(m=>
    `<button data-k="${m.key}" class="${m.key===state.size?'on':''}">${WSHORT[m.key]}</button>`).join('');
  document.querySelectorAll('#layoutseg button').forEach(b=>b.onclick=()=>set('layout',b.dataset.k));
  document.querySelectorAll('#colourseg button').forEach(b=>b.onclick=()=>set('colour',b.dataset.k));
  document.querySelectorAll('#sizeseg button').forEach(b=>b.onclick=()=>set('size',b.dataset.k));
}
function set(key,val){ state[key]=val; segs(); render(); }
function buildSrcSeg(){
  const el=document.getElementById('srcseg'); if(!el) return;
  el.innerHTML=Object.keys(SOURCES).map(s=>`<button data-s="${s}" class="${s===curSource?'on':''}">${SOURCES[s].label}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>setSource(b.dataset.s));
}
function setSource(src){
  curSource=src; D=SOURCES[src]; buildMaps();
  state.layout=defLayout(); state.colour=defColour(); state.size='papers';
  document.querySelectorAll('#srcseg button').forEach(b=>b.classList.toggle('on',b.dataset.s===src));
  const dots=svg.querySelector('#dots'); if(dots) dots.remove();   // term set changed → rebuild dots
  const labels=svg.querySelector('#labels'); if(labels) labels.remove();
  segs(); render();
}

const svg=document.getElementById('map');
let W=1100,H=620,PAD=42;
function xy(t){const p=D.layouts[state.layout][t.term]||[0.5,0.5];
  return [PAD+p[0]*(W-2*PAD), PAD+p[1]*(H-2*PAD)];}

function render(){
  W=svg.clientWidth||1100; H=svg.clientHeight||620;
  const col=colours(), rscale=radiusScale();
  // dots (keyed by term so transitions morph positions)
  let circles=svg.querySelector('#dots');
  if(!circles){circles=document.createElementNS('http://www.w3.org/2000/svg','g');circles.id='dots';svg.appendChild(circles);}
  if(!circles.dataset.built){
    circles.innerHTML=T.map(t=>`<circle data-t="${t.term}"></circle>`).join('');
    circles.dataset.built='1';
    circles.querySelectorAll('circle').forEach(c=>{
      const t=termMap[c.dataset.t];
      c.onmousemove=e=>{const m=t.m;
        showTip(`<span class="tv">${t.term}</span>
          <div class="row"><span><span class="sw" style="background:${colours()[grp(t,state.colour)]}"></span>${grp(t,state.colour)}</span></div>
          <div style="color:#bbb;margin-top:3px">${fmt(m.papers)} papers · ${fmt(m.citations)} cit · ${(+m.cpp).toFixed(1)}/paper · ${m.recency}% since ’24</div>`,e.clientX,e.clientY);
        c.style.strokeWidth='2.4';};
      c.onmouseleave=()=>{hideTip();c.style.strokeWidth='';
        circles.querySelectorAll('circle').forEach(o=>o.style.opacity='1');};
      c.onmouseover=()=>{const g=grp(t,state.colour);
        circles.querySelectorAll('circle').forEach(o=>o.style.opacity=(grp(termMap[o.dataset.t],state.colour)===g)?'1':'.15');};
    });
  }
  circles.querySelectorAll('circle').forEach(c=>{
    const t=termMap[c.dataset.t],[x,y]=xy(t);
    c.setAttribute('cx',x.toFixed(1));c.setAttribute('cy',y.toFixed(1));
    c.setAttribute('r',rscale(svVal(t)).toFixed(1));
    c.setAttribute('fill',col[grp(t,state.colour)]||'var(--muted)');
    c.setAttribute('fill-opacity','0.82');
    c.setAttribute('stroke','var(--card)');c.style.strokeWidth=c.style.strokeWidth||'1.2';
  });
  // group labels at the layout-group centroids
  let labels=svg.querySelector('#labels');
  if(!labels){labels=document.createElementNS('http://www.w3.org/2000/svg','g');labels.id='labels';svg.appendChild(labels);}
  const groups={};
  T.forEach(t=>{const g=grp(t,state.layout);(groups[g]=groups[g]||[]).push(t);});
  labels.innerHTML=Object.entries(groups).map(([g,ts])=>{
    let sx=0,sy=0;ts.forEach(t=>{const[x,y]=xy(t);sx+=x;sy+=y;});
    const cx=sx/ts.length, cy=sy/ts.length;
    const short=state.layout==='semantic'?g:g.split(/[,·]/)[0].replace(' +','');
    return `<text class="glabel" x="${cx.toFixed(0)}" y="${cy.toFixed(0)}" text-anchor="middle">${short}</text>`;
  }).join('');
  // legend (colour lens)
  document.getElementById('legend').innerHTML=
    `<span class="cap">colour = ${LM[state.colour].label}</span>`+
    LM[state.colour].groups.map(g=>`<span class="lg"><span class="sw" style="background:${col[g]}"></span>${g}</span>`).join('');
  document.getElementById('hint').innerHTML=
    `Position clusters by <b>${LM[state.layout].label}</b>, colour by <b>${LM[state.colour].label}</b>, size by <b>${WSHORT[state.size]}</b>.
     Hover a dot to isolate its colour group. ${state.layout===state.colour?'Layout = colour → clean single-colour clusters.':'Layout ≠ colour → watch how the colours mix inside each cluster.'}`;
  document.getElementById('eyebrow').textContent=T.length+' terms · one map · three controls';
  document.getElementById('findings').style.display=curSource==='curated'?'':'none';
  // MIT gaps note (curated only)
  const note=document.getElementById('mitnote');
  if(D.mit_gaps&&D.mit_gaps.length){note.style.display='';
    note.innerHTML=`<b>What a scatter can’t show —</b> ${D.mit_gaps.length} MIT risk subdomains have <b>no buzzword</b> at all
     (they’d be empty regions in the MIT layout): ${D.mit_gaps.map(s=>s.split(',')[0]).join(' · ')}. All socioeconomic.`;
  }else{note.style.display='none';}
}

document.getElementById('themebtn').onclick=()=>{const r=document.documentElement;
  r.setAttribute('data-theme',isDark()?'light':'dark');render();};
matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(render,150);});
buildSrcSeg();segs();render();
</script>
"""

if __name__ == "__main__":
    main()
