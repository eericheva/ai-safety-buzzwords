# -*- coding: utf-8 -*-
"""Assemble trends.html — the time-series visualizer (Atlas / Overlay / Themes)."""
import json, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


LBL = {"curated": "Curated", "raw2": "Mined phrases", "openalex": "OpenAlex keywords"}


def main():
    curated = json.load(open(os.path.join(HERE, "data", "trends_data.json")))
    curated["label"] = LBL["curated"]
    sources = {"curated": curated}
    for s in ("raw2", "openalex"):
        p = os.path.join(HERE, "data", "src_" + s, "trends_data.json")
        if os.path.exists(p):
            sd = json.load(open(p)); sd["label"] = LBL[s]; sources[s] = sd
    html = TEMPLATE.replace("/*__DATA__*/", json.dumps(sources, ensure_ascii=False, separators=(",", ":")))
    out = os.path.join(HERE, "web", "trends.html")
    open(out, "w").write(html)
    print(f"wrote {out}  ({os.path.getsize(out)/1024:.0f} KB)  sources={list(sources)}")


TEMPLATE = r"""<title>AI Safety Buzzwords — Trends over time</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --paper:#faf9f6; --plane:#f2f1ec; --card:#ffffff;
  --ink:#171613; --ink2:#57544d; --muted:#8a877f;
  --line:#e4e1d8; --line2:#d3cfc4;
  --accent:#1f5fb0; --accent-soft:#e7eef8;
  --shadow:0 1px 2px rgba(23,22,19,.05),0 8px 24px -12px rgba(23,22,19,.12);
  --c1:#2a78d6;--c2:#008300;--c3:#e87ba4;--c4:#eda100;--c5:#1baf7a;--c6:#eb6834;--c7:#4a3aa7;--c8:#e34948;
}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){
  --paper:#141413; --plane:#0e0e0d; --card:#1c1c1a;
  --ink:#f4f2ec; --ink2:#c0bdb2; --muted:#8f8c83;
  --line:#2b2a27; --line2:#3a3934;
  --accent:#5598e7; --accent-soft:#1b2739;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
  --c1:#3987e5;--c2:#38ad38;--c3:#e87ba4;--c4:#eda100;--c5:#1baf7a;--c6:#eb6834;--c7:#9085e9;--c8:#e66767;
}}
:root[data-theme=dark]{
  --paper:#141413; --plane:#0e0e0d; --card:#1c1c1a;
  --ink:#f4f2ec; --ink2:#c0bdb2; --muted:#8f8c83;
  --line:#2b2a27; --line2:#3a3934; --accent:#5598e7; --accent-soft:#1b2739;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
  --c1:#3987e5;--c2:#38ad38;--c3:#e87ba4;--c4:#eda100;--c5:#1baf7a;--c6:#eb6834;--c7:#9085e9;--c8:#e66767;
}
*{box-sizing:border-box}
body{margin:0;background:var(--plane);color:var(--ink);font-size:16px;
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.tnum{font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding:0 22px}
h1,h2{text-wrap:balance;margin:0;line-height:1.15}
a{color:var(--accent)}
.eyebrow{font:600 12px/1.4 ui-monospace,monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.themebtn{position:fixed;top:14px;right:14px;z-index:30;width:38px;height:38px;border-radius:10px;
  border:1px solid var(--line2);background:var(--card);color:var(--ink);cursor:pointer;font-size:16px;box-shadow:var(--shadow)}

header{border-bottom:1px solid var(--line);background:linear-gradient(180deg,var(--paper),var(--plane))}
.hero{padding:40px 0 26px;display:grid;gap:14px}
.hero h1{font-size:clamp(28px,4.2vw,46px);font-weight:800;letter-spacing:-.02em}
.hero h1 em{font-style:normal;color:var(--accent)}
.lead{max-width:66ch;color:var(--ink2);font-size:16.5px}

/* sticky control bar */
.bar{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--paper) 88%,transparent);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.bar-in{display:flex;flex-direction:column;align-items:flex-start;gap:10px;padding:10px 0}
.ctlrow{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:center;width:100%;
  border-top:1px solid var(--line);padding-top:10px}
.tabs{display:flex;gap:4px;background:var(--plane);border:1px solid var(--line);border-radius:11px;padding:4px}
.tab{border:0;background:transparent;color:var(--ink2);font:600 14px/1 system-ui;padding:8px 14px;
  border-radius:8px;cursor:pointer;display:flex;gap:7px;align-items:center}
.tab.on{background:var(--card);color:var(--ink);box-shadow:var(--shadow)}
.tab small{font:500 11px/1 ui-monospace,monospace;color:var(--muted)}
.seg{display:flex;background:var(--plane);border:1px solid var(--line);border-radius:11px;padding:4px}
.seg button{border:0;background:transparent;color:var(--ink2);font:600 13px/1 system-ui;padding:8px 13px;
  border-radius:8px;cursor:pointer}
.seg button.on{background:var(--card);color:var(--ink);box-shadow:var(--shadow)}
.seg.dim{opacity:.4;pointer-events:none}
.spacer{flex:1}
.ctl{display:flex;gap:8px;align-items:center;color:var(--ink2);font-size:13px}
.check{display:flex;align-items:center;gap:7px;cursor:pointer;user-select:none;font-size:13px;color:var(--ink2)}
.inp{background:var(--card);border:1px solid var(--line2);border-radius:9px;padding:7px 10px;color:var(--ink);font-size:13.5px;min-width:180px}
.inp:focus{outline:2px solid var(--accent);outline-offset:1px}

section{padding:26px 0 40px}
.hint{color:var(--muted);font-size:13px;margin:0 0 18px;max-width:80ch}
.hint b{color:var(--ink2)}

/* group filter chips */
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:18px}
.chip{border:1px solid var(--line2);background:var(--card);color:var(--ink2);border-radius:999px;
  padding:5px 11px;font-size:12.5px;cursor:pointer;display:flex;align-items:center;gap:6px;user-select:none}
.chip .sw{width:9px;height:9px;border-radius:2px}
.chip.on{color:#fff;border-color:transparent}

/* atlas grid */
.atlasctl{display:flex;flex-wrap:wrap;gap:10px 14px;align-items:center;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px}
/* atlas heatmap (one-screen) */
.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:1px 20px}
.hrow{display:grid;grid-template-columns:9px 1fr auto 132px;align-items:center;gap:7px;height:18px;cursor:default}
.hrow:hover{background:var(--accent-soft)}
.hsw{width:9px;height:9px;border-radius:2px}
.hnm{font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.hnum{font:600 11px/1 ui-monospace,monospace;color:var(--ink2);font-variant-numeric:tabular-nums}
.hcells{display:grid;grid-template-columns:repeat(12,1fr);gap:1px;height:12px}
.hcells i{border-radius:1px;display:block}
.mini{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:12px 12px 8px;
  cursor:pointer;box-shadow:var(--shadow);transition:border-color .12s,transform .12s}
.mini:hover{border-color:var(--line2);transform:translateY(-1px)}
.mini.sel{border-color:var(--accent);box-shadow:0 0 0 1.5px var(--accent),var(--shadow)}
.mini .top{display:flex;justify-content:space-between;align-items:baseline;gap:8px;margin-bottom:4px}
.mini .nm{font-size:13.5px;font-weight:650;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.mini .tot{font:600 12px/1 ui-monospace,monospace;color:var(--ink2);white-space:nowrap}
.mini .meta{display:flex;justify-content:space-between;font:11px/1.3 ui-monospace,monospace;color:var(--muted);margin-top:5px}
.mini svg{width:100%;height:52px;display:block}

/* big chart card */
.chartcard{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:18px 18px 10px;box-shadow:var(--shadow)}
.bigsvg{width:100%;height:440px;display:block;overflow:visible}
.legend{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:14px}
.lg{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink);background:var(--plane);
  border:1px solid var(--line);border-radius:999px;padding:4px 10px 4px 8px}
.lg .sw{width:11px;height:11px;border-radius:3px;flex:none}
.lg button{border:0;background:transparent;color:var(--muted);cursor:pointer;font-size:14px;line-height:1;padding:0 0 0 2px}
.lg button:hover{color:var(--c8)}
.emptysel{color:var(--muted);font-size:13px;padding:6px 0}
.axis{fill:var(--muted);font:11px ui-monospace,monospace}
.grid-l{stroke:var(--line);stroke-width:1}
.ln{fill:none;stroke-width:2}
.area{opacity:.14}
.dot{stroke:var(--card);stroke-width:1.5}
.cross{stroke:var(--line2);stroke-width:1;stroke-dasharray:3 3;opacity:0}
/* overlay: all lines + eye-toggle group legend */
.ovln{fill:none;stroke-width:1.6;opacity:.85;transition:opacity .1s,stroke-width .1s}
.ovhit{fill:none;stroke:transparent;stroke-width:9;cursor:pointer}
.eye{color:currentColor;flex:none} .eye .slash{display:none}
.glg{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink);background:var(--plane);
  border:1px solid var(--line);border-radius:999px;padding:3px 10px 3px 7px;cursor:pointer;user-select:none}
.glg .sw{width:11px;height:11px;border-radius:3px;flex:none}
.glg .ct{color:var(--muted);font:600 11px/1 ui-monospace,monospace;margin-left:2px}
.glg.off{opacity:.45} .glg.off .eye .slash{display:block}
.eyeall{display:flex;gap:6px;margin-right:2px}
.eyeall button{display:flex;align-items:center;gap:5px;font:600 12px/1 system-ui;color:var(--ink2);
  background:var(--card);border:1px solid var(--line2);border-radius:999px;padding:4px 10px;cursor:pointer}
.eyeall button:hover{color:var(--ink)}

#tip{position:fixed;z-index:40;pointer-events:none;opacity:0;transition:opacity .1s;background:var(--ink);
  color:var(--paper);padding:8px 11px;border-radius:9px;font-size:12.5px;box-shadow:var(--shadow);max-width:280px}
#tip .tv{font-weight:700} #tip .row{display:flex;justify-content:space-between;gap:14px}
#tip .sw{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px}
footer{padding:30px 0 60px;color:var(--muted);font-size:13px}
.addwrap{position:relative}
.menu{position:absolute;top:calc(100% + 4px);left:0;z-index:25;background:var(--card);border:1px solid var(--line2);
  border-radius:11px;box-shadow:var(--shadow);max-height:280px;overflow:auto;width:240px;display:none}
.menu.open{display:block}
.menu div{padding:8px 11px;font-size:13.5px;cursor:pointer;display:flex;align-items:center;gap:8px}
.menu div:hover{background:var(--accent-soft)}
.nav{display:flex;gap:6px;align-items:center;padding:10px 0}
.nav a{display:flex;align-items:center;gap:6px;text-decoration:none;font:600 13px/1 system-ui;
  color:var(--ink2);border:1px solid var(--line2);background:var(--card);border-radius:9px;padding:8px 12px}
.nav a.cur{color:var(--ink);border-color:var(--accent);background:var(--accent-soft)}
.nav .sep{flex:1}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<button class="themebtn" id="themebtn" aria-label="Toggle theme">◐</button>
<div id="tip"></div>

<div class="wrap"><nav class="nav">
  <a href="https://claude.ai/code/artifact/925356f2-6bd0-48bd-931e-4da6525c7b00">🧭 Word cloud</a>
  <a class="cur" href="#">📈 Trends</a>
  <a href="https://claude.ai/code/artifact/8f0e56b3-eed4-414d-8414-585d553a26fe">🗂️ Groupings</a>
  <span class="sep"></span><span class="eyebrow" style="align-self:center">Source</span>
  <div class="seg" id="srcseg"></div>
</nav></div>

<header><div class="wrap hero">
  <div class="eyebrow">arXiv · Semantic Scholar · time series 2015–2026</div>
  <h1>How AI-safety buzzwords <em>emerge &amp; shift</em></h1>
  <p class="lead">Each buzzword’s trajectory by year — how many papers use it and how much
  those papers are cited. Compare one, a few, or the whole field.
  <b>Citations note:</b> Semantic Scholar reports a paper’s current total, so “citations”
  here means the citations earned by papers <em>published</em> that year (cohort impact), not
  year-by-year accrual.</p>
</div></header>

<div class="bar"><div class="wrap bar-in">
  <div class="tabs" id="tabs">
    <button class="tab on" data-v="atlas">Atlas <small>each term</small></button>
    <button class="tab" data-v="overlay">Overlay <small>compare</small></button>
    <button class="tab" data-v="themes">Themes <small>the field</small></button>
  </div>
  <div class="ctlrow">
    <div class="ctl" id="sizewrap"><span class="eyebrow">Size</span><div class="seg" id="weightseg"></div></div>
    <div class="ctl" id="ctxctl"></div>
  </div>
</div></div>

<div class="wrap">
  <section id="view-atlas">
    <p class="hint" id="atlas-hint"></p>
    <div class="atlasctl"><div class="seg" id="atlasviewseg"></div><div class="chips" id="atlas-chips"></div></div>
    <div class="grid" id="atlas-grid"></div>
  </section>

  <section id="view-overlay" hidden>
    <p class="hint">Every buzzword’s curve at once, <b>coloured by the Colour lens</b>. Click a group’s
    <b>eye</b> to hide/show it, or <b>Show all / Hide all</b>. Hover a line to pick it out.
    <b>Normalise</b> rescales each line to its own peak so you compare <em>shape</em>, not size.</p>
    <div class="legend" id="ov-legend"></div>
    <div class="chartcard"><svg class="bigsvg" id="ov-svg" preserveAspectRatio="none"></svg></div>
  </section>

  <section id="view-themes" hidden>
    <p class="hint">Per year, stacked by group — the changing <b>composition</b> of safety research.
    <b>Size</b> switches papers ↔ citations; <b>Colour</b> switches the grouping (glossary themes,
    MIT risk domains, semantic clusters, or co-occurrence communities).</p>
    <div class="legend" id="th-legend"></div>
    <div class="chartcard"><svg class="bigsvg" id="th-svg" preserveAspectRatio="none"></svg></div>
  </section>
</div>

<footer><div class="wrap">
  Time series from the verified corpus · window 2015–2026 (2026 partial) ·
  metric toggles paper count ↔ cohort citations · buzzwords from
  <span class="mono">ai-safety-concepts-glossary.md</span>.
</div></footer>

<script>
const SOURCES = /*__DATA__*/;
let curSource='curated';
let D = SOURCES[curSource];
const CAT = ['--c1','--c2','--c3','--c4','--c5','--c6','--c7','--c8'];
const YEARS = []; for(let y=D.y0;y<=D.y1;y++) YEARS.push(y);
const cssv = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const isDark = () => document.documentElement.getAttribute('data-theme')==='dark' ||
  (!document.documentElement.getAttribute('data-theme') && matchMedia('(prefers-color-scheme:dark)').matches);
const fmt = n => n>=1000? (n/1000).toFixed(n>=10000?0:1)+'k' : ''+n;
const fmtf = n => n.toLocaleString('en-US');
let termMap = {};
function buildTermMap(){ termMap={}; D.terms.forEach(t=>termMap[t.term]=t); }
buildTermMap();

let state={view:'atlas',atlasView:'heat',weight:'papers',sort:'papers',groups:new Set(),
  lens:Object.keys(D.lens_meta)[0], hidden:new Set(), norm:false};

/* weight metrics — the card number + sort; the sparkline stays a time series */
const WSHORT = {papers:'Papers', citations:'Citations', cpp:'Cit/paper', recency:'Recency', momentum:'Momentum', debut:'Debut yr', peak:'Peak yr'};
const YEARM = k => k==='debut'||k==='peak';
const seriesKey = () => state.weight==='citations' ? 'c' : 'n';   // sparkline series
const wv = t => t.metrics[state.weight];                          // t is a term object
const sortVal = t => t.metrics[state.sort];
const wLabel = k => (D.weight_metrics.find(m=>m.key===k)||{}).label||k;
const wFmt = (k,v) => YEARM(k)?''+(v||'—'):k==='cpp'?(+v).toFixed(1):k==='recency'?v+'%':fmtf(v);

/* grouping-lens helpers (atlas colours + themes streamgraph) */
const lensColors = () => { const m=D.lens_meta[state.lens]; return isDark()?m.colors_dark:m.colors; };
const lensGroups = () => D.lens_meta[state.lens].groups;
const grpOf = term => { const t=termMap[term]; return (t.lenses&&t.lenses[state.lens])||t.group; };
const gc = () => lensColors();   // back-compat alias

const tip=document.getElementById('tip');
function showTip(html,x,y){tip.innerHTML=html;tip.style.opacity=1;
  const w=tip.offsetWidth,h=tip.offsetHeight;
  tip.style.left=Math.min(x+14,innerWidth-w-8)+'px';tip.style.top=Math.max(8,y-h-12)+'px';}
const hideTip=()=>tip.style.opacity=0;

/* ---------- mini sparkline (area+line) ---------- */
function miniSvg(series,color){
  const W=200,H=52,P=3;
  const vals=series.map(s=>s[seriesKey()]);
  const max=Math.max(1,...vals);
  const x=i=>P+i/(vals.length-1)*(W-2*P);
  const y=v=>H-P-v/max*(H-2*P);
  const line=vals.map((v,i)=>`${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
  const area=`${x(0)},${H-P} ${line} ${x(vals.length-1)},${H-P}`;
  const pk=vals.indexOf(Math.max(...vals));
  return `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <polygon class="area" points="${area}" fill="${color}"/>
    <polyline class="ln" points="${line}" stroke="${color}"/>
    <circle cx="${x(pk).toFixed(1)}" cy="${y(vals[pk]).toFixed(1)}" r="2.6" fill="${color}"/></svg>`;
}

/* ---------- ATLAS ---------- */
function renderAtlasChips(){
  const c=lensColors();
  const lbl=g=>state.lens==='semantic'?g:g.split(/[ ·,]/)[0];
  document.getElementById('atlas-chips').innerHTML=lensGroups().map(g=>
    `<span class="chip ${state.groups.has(g)?'on':''}" data-g="${g}"
      style="${state.groups.has(g)?`background:${c[g]}`:''}">
      <span class="sw" style="background:${c[g]}"></span>${lbl(g)}</span>`).join('');
  document.querySelectorAll('#atlas-chips .chip').forEach(ch=>ch.onclick=()=>{
    const g=ch.dataset.g; state.groups.has(g)?state.groups.delete(g):state.groups.add(g); renderAtlas();});
}
function buildAtlasViewSeg(){
  const el=document.getElementById('atlasviewseg');
  el.innerHTML=[['heat','Heatmap'],['cards','Cards']].map(([k,l])=>
    `<button data-a="${k}" class="${k===state.atlasView?'on':''}">${l}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>{state.atlasView=b.dataset.a;renderAtlas();});
}
function atlasTip(term){const t=termMap[term],mm=t.metrics;
  return `<span class="tv">${term}</span><br>${fmtf(mm.papers)} papers · ${fmtf(mm.citations)} citations · ${(+mm.cpp).toFixed(1)}/paper
    <br><span style="color:#bbb">${mm.recency}% since ’24 · debut ${t.debut} · peak ${t.peak_year}</span>`;}
function renderAtlas(){
  renderAtlasChips(); buildAtlasViewSeg();
  const c=lensColors();
  let ts=[...D.terms];
  if(state.groups.size) ts=ts.filter(t=>state.groups.has(grpOf(t.term)));
  ts.sort((a,b)=>(sortVal(b)-sortVal(a)) || (b.total_n-a.total_n));
  const grid=document.getElementById('atlas-grid');
  const seriesLbl=seriesKey()==='c'?'citations':'papers';
  if(state.atlasView==='heat'){
    document.getElementById('atlas-hint').innerHTML=
      `<b>${ts.length}</b> buzzwords on one screen · each row is a <b>heat-strip</b> 2015→2026, shaded by
       ${seriesLbl}/year (row-normalised, so darker = its own busy years); the number is <b>${wLabel(state.weight).toLowerCase()}</b>.`;
    grid.className='hgrid';
    grid.innerHTML=ts.map(t=>{
      const col=c[grpOf(t.term)]||'var(--muted)';
      const vals=t.series.map(s=>s[seriesKey()]), mx=Math.max(1,...vals);
      const cells=vals.map(v=>`<i style="background:${col};opacity:${(0.05+0.95*v/mx).toFixed(2)}"></i>`).join('');
      return `<div class="hrow" data-t="${t.term}"><span class="hsw" style="background:${col}"></span>
        <span class="hnm" title="${t.term}">${t.term}</span>
        <span class="hnum">${wFmt(state.weight,wv(t))}</span>
        <span class="hcells">${cells}</span></div>`;
    }).join('');
    grid.querySelectorAll('.hrow').forEach(r=>{
      r.onmousemove=e=>showTip(atlasTip(r.dataset.t),e.clientX,e.clientY);
      r.onmouseleave=hideTip;});
    return;
  }
  document.getElementById('atlas-hint').innerHTML=
    `<b>${ts.length}</b> buzzwords · each mini-chart is self-scaled to its own peak so you read
     the <b>shape</b> of its rise; the number is <b>${wLabel(state.weight).toLowerCase()}</b>. Dot marks the peak year.`;
  grid.className='grid';
  grid.innerHTML=ts.map(t=>{
    const col=c[grpOf(t.term)]||'var(--muted)', tot=wFmt(state.weight,wv(t));
    return `<div class="mini" data-t="${t.term}">
      <div class="top"><span class="nm" title="${t.term}">${t.term}</span>
        <span class="tot">${tot}</span></div>
      ${miniSvg(t.series,col)}
      <div class="meta"><span>debut ${t.debut}</span><span>peak ${t.peak_year}</span></div></div>`;
  }).join('');
  document.querySelectorAll('#atlas-grid .mini').forEach(m=>{
    m.onmousemove=e=>showTip(atlasTip(m.dataset.t),e.clientX,e.clientY);
    m.onmouseleave=hideTip;
  });
}

/* ---------- axis helper for big charts ---------- */
function axes(svg,W,H,PL,PR,PT,PB,maxV,fmtY){
  let g='';const ticks=[0,.25,.5,.75,1].map(f=>Math.round(maxV*f));
  [...new Set(ticks)].forEach(t=>{const yy=PT+(1-t/maxV)*(H-PT-PB);
    g+=`<line class="grid-l" x1="${PL}" x2="${W-PR}" y1="${yy}" y2="${yy}"/>
       <text class="axis" x="${PL-7}" y="${yy+3}" text-anchor="end">${fmtY(t)}</text>`;});
  YEARS.forEach((y,i)=>{const xx=PL+i/(YEARS.length-1)*(W-PL-PR);
    if(y%2===1||y===D.y1) g+=`<text class="axis" x="${xx}" y="${H-8}" text-anchor="middle">${y}</text>`;});
  return g;
}

/* ---------- OVERLAY (all lines, coloured by the Colour lens, groups toggled by eye) ---------- */
const EYE='<svg class="eye" viewBox="0 0 24 24" width="15" height="15"><path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12z" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="2.6" fill="currentColor"/><line class="slash" x1="4" y1="20" x2="20" y2="4" stroke="currentColor" stroke-width="1.8"/></svg>';
function renderOverlay(){
  const svg=document.getElementById('ov-svg');
  const W=svg.clientWidth||1000,H=420,PL=46,PR=18,PT=14,PB=28;
  const c=lensColors();
  const vis=D.terms.filter(t=>!state.hidden.has(grpOf(t.term)));   // terms whose colour-group is shown
  const seriesOf=t=>termMap[t.term].series.map(s=>s[seriesKey()]);
  const xi=i=>PL+i/(YEARS.length-1)*(W-PL-PR);
  let maxV = state.norm ? 100 : Math.max(1,...vis.flatMap(seriesOf));
  const yv=v=>PT+(1-v/maxV)*(H-PT-PB);
  let g=axes(svg,W,H,PL,PR,PT,PB,maxV,state.norm?(v=>v+'%'):(v=>fmt(v)));
  vis.forEach(t=>{
    let vals=seriesOf(t);
    if(state.norm){const mx=Math.max(1,...vals);vals=vals.map(v=>v/mx*100);}
    const pts=vals.map((v,i)=>`${xi(i)},${yv(v)}`).join(' ');
    const col=c[grpOf(t.term)]||'var(--muted)';
    g+=`<polyline class="ovln" data-t="${t.term}" points="${pts}" stroke="${col}"/>`+
       `<polyline class="ovhit" data-t="${t.term}" points="${pts}"/>`;   // fat transparent hit line
  });
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML=g;
  const lns=svg.querySelectorAll('.ovln');
  svg.querySelectorAll('.ovhit').forEach(h=>{
    const term=h.dataset.t, t=termMap[term];
    h.onmousemove=e=>{
      lns.forEach(l=>l.style.opacity=l.dataset.t===term?'1':'.08');
      const cur=[...lns].find(l=>l.dataset.t===term); if(cur){cur.style.strokeWidth='2.6';}
      const m=t.metrics;
      showTip(`<span class="tv">${term}</span><br>${fmtf(m.papers)} papers · ${fmtf(m.citations)} cit · peak ${t.peak_year}<br>
        <span style="color:#bbb"><span class="sw" style="background:${c[grpOf(term)]}"></span>${grpOf(term)}</span>`,e.clientX,e.clientY);
    };
    h.onmouseleave=()=>{lns.forEach(l=>{l.style.opacity='';l.style.strokeWidth='';});hideTip();};
  });
  // legend = colour-lens groups with eye toggles + show/hide all
  const groups=lensGroups();
  const cnt={}; D.terms.forEach(t=>{const gp=grpOf(t.term);cnt[gp]=(cnt[gp]||0)+1;});
  const lg=document.getElementById('ov-legend');
  lg.innerHTML=`<div class="eyeall"><button data-a="show">${EYE} Show all</button><button data-a="hide">${EYE} Hide all</button></div>`+
    groups.map(gp=>`<span class="glg ${state.hidden.has(gp)?'off':''}" data-g="${gp}">${EYE}
      <span class="sw" style="background:${c[gp]}"></span>${gp}<span class="ct">${cnt[gp]||0}</span></span>`).join('');
  lg.querySelectorAll('.glg').forEach(el=>el.onclick=()=>{
    const gp=el.dataset.g; state.hidden.has(gp)?state.hidden.delete(gp):state.hidden.add(gp); renderOverlay();});
  lg.querySelectorAll('.eyeall button').forEach(b=>b.onclick=()=>{
    if(b.dataset.a==='hide') groups.forEach(gp=>state.hidden.add(gp)); else state.hidden.clear(); renderOverlay();});
}

/* ---------- THEMES streamgraph (stacked area, per lens) ---------- */
function renderThemes(){
  const svg=document.getElementById('th-svg');
  const W=svg.clientWidth||1000,H=420,PL=46,PR=18,PT=14,PB=28;
  const cit=state.weight==='citations';
  const c=lensColors(),themes=lensGroups(),stream=(cit?D.streams_c:D.streams)[state.lens];
  const totals=stream.map(r=>themes.reduce((a,th)=>a+r[th],0));
  const maxV=Math.max(1,...totals);
  const xi=i=>PL+i/(YEARS.length-1)*(W-PL-PR);
  const yv=v=>PT+(1-v/maxV)*(H-PT-PB);
  let g=axes(svg,W,H,PL,PR,PT,PB,maxV,v=>fmt(v));
  // build cumulative bands
  const cum=stream.map(()=>0);
  themes.forEach(th=>{
    const top=stream.map((r,i)=>cum[i]+r[th]);
    const bot=[...cum];
    const pts=top.map((v,i)=>`${xi(i)},${yv(v)}`).join(' ')+' '+
      bot.map((v,i)=>`${xi(YEARS.length-1-i)},${yv(bot[YEARS.length-1-i])}`).join(' ');
    g+=`<polygon points="${pts}" fill="${c[th]}" opacity="0.9" stroke="var(--card)" stroke-width="1"/>`;
    stream.forEach((r,i)=>cum[i]=top[i]);
  });
  // hover columns
  YEARS.forEach((y,i)=>{g+=`<rect x="${xi(i)-(W-PL-PR)/YEARS.length/2}" y="${PT}"
    width="${(W-PL-PR)/YEARS.length}" height="${H-PT-PB}" fill="transparent" data-i="${i}"/>`;});
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML=g;
  svg.querySelectorAll('rect[data-i]').forEach(r=>{
    r.onmousemove=e=>{const i=+r.dataset.i,row=stream[i];
      const rows=[...themes].sort((a,b)=>row[b]-row[a]).map(th=>
        `<div class="row"><span><span class="sw" style="background:${c[th]}"></span>${th.split(/[,·]/)[0]}</span><b>${fmtf(row[th])}</b></div>`).join('');
      showTip(`<span class="tv">${YEARS[i]}</span> · ${fmtf(totals[i])} ${cit?'citations':'papers'}${rows}`,e.clientX,e.clientY);};
    r.onmouseleave=hideTip;});
  document.getElementById('th-legend').innerHTML=themes.map(th=>
    `<span class="lg"><span class="sw" style="background:${c[th]}"></span>${th}</span>`).join('');
}

/* ---------- context controls per view ---------- */
function lensSegHTML(){
  return `<span class="eyebrow">Colour</span><div class="seg" id="lensseg">`+
    Object.entries(D.lens_meta).map(([k,m])=>
      `<button data-l="${k}" class="${k===state.lens?'on':''}">${m.label.replace(' theme','').replace(' risk domain',' risk').replace(' cluster','').replace(' community','')}</button>`).join('')+
    `</div>`;
}
function wireLensSeg(after){
  document.querySelectorAll('#lensseg button').forEach(b=>b.onclick=()=>{
    state.lens=b.dataset.l; state.groups.clear(); state.hidden.clear(); after();});
}
function renderCtx(){
  const el=document.getElementById('ctxctl');
  if(state.view==='atlas'){
    el.innerHTML=`<span class="eyebrow">Sort</span><div class="seg" id="sortseg">`+
      D.weight_metrics.map(m=>`<button data-s="${m.key}" class="${m.key===state.sort?'on':''}">${WSHORT[m.key]}</button>`).join('')
      +`</div>`+ lensSegHTML();
    el.querySelectorAll('#sortseg button').forEach(b=>b.onclick=()=>{state.sort=b.dataset.s;renderAtlas();renderCtx();});
    wireLensSeg(()=>{renderAtlas();renderCtx();});
  }else if(state.view==='overlay'){
    el.innerHTML=`<label class="check"><input type="checkbox" id="normck" ${state.norm?'checked':''}> Normalise</label>`+ lensSegHTML();
    document.getElementById('normck').onchange=e=>{state.norm=e.target.checked;renderOverlay();};
    wireLensSeg(()=>{renderOverlay();renderCtx();});
  }else{  // themes
    el.innerHTML=lensSegHTML();
    wireLensSeg(()=>{renderThemes();renderCtx();});
  }
}

/* ---------- view switch ---------- */
function setView(v){
  state.view=v;
  document.querySelectorAll('#tabs .tab').forEach(t=>t.classList.toggle('on',t.dataset.v===v));
  document.getElementById('view-atlas').hidden=v!=='atlas';
  document.getElementById('view-overlay').hidden=v!=='overlay';
  document.getElementById('view-themes').hidden=v!=='themes';
  document.getElementById('sizewrap').style.display='flex';
  buildWeightSeg();
  renderCtx();
  if(v==='atlas')renderAtlas();else if(v==='overlay')renderOverlay();else renderThemes();
}
document.querySelectorAll('#tabs .tab').forEach(t=>t.onclick=()=>setView(t.dataset.v));
function buildWeightSeg(){
  const el=document.getElementById('weightseg');
  // Atlas: metric = card number/sort → all 7. Overlay/Themes plot a per-year
  // series (papers or citations) → only those two apply.
  const limited=state.view!=='atlas';
  if(limited && state.weight!=='papers' && state.weight!=='citations') state.weight='papers';
  const metrics=limited ? D.weight_metrics.filter(m=>m.key==='papers'||m.key==='citations') : D.weight_metrics;
  el.innerHTML=metrics.map(m=>
    `<button data-w="${m.key}" class="${m.key===state.weight?'on':''}">${WSHORT[m.key]}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    state.weight=b.dataset.w;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
    if(state.view==='atlas')renderAtlas();else if(state.view==='overlay')renderOverlay();else renderThemes();
  });
}
buildWeightSeg();

/* theme toggle */
document.getElementById('themebtn').onclick=()=>{const r=document.documentElement;
  const dark=r.getAttribute('data-theme')==='dark'||(!r.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);
  r.setAttribute('data-theme',dark?'light':'dark');rerender();};
function rerender(){if(state.view==='atlas')renderAtlas();else if(state.view==='overlay')renderOverlay();else renderThemes();renderCtx();}
matchMedia('(prefers-color-scheme:dark)').addEventListener('change',rerender);
addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(rerender,150);});
document.addEventListener('click',e=>{const m=document.getElementById('addmenu');
  if(m&&!e.target.closest('.addwrap'))m.classList.remove('open');});

/* source switcher */
function buildSrcSeg(){
  const el=document.getElementById('srcseg'); if(!el) return;
  el.innerHTML=Object.keys(SOURCES).map(s=>
    `<button data-s="${s}" class="${s===curSource?'on':''}">${SOURCES[s].label}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>setSource(b.dataset.s));
}
function setSource(src){
  curSource=src; D=SOURCES[src]; buildTermMap();
  state.lens=Object.keys(D.lens_meta)[0]; state.weight='papers'; state.sort='papers';
  state.groups.clear(); state.hidden.clear();
  document.querySelectorAll('#srcseg button').forEach(b=>b.classList.toggle('on',b.dataset.s===src));
  setView(state.view);
}
buildSrcSeg();
setView('atlas');
</script>
"""

if __name__ == "__main__":
    main()
