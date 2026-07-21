# -*- coding: utf-8 -*-
"""Assemble the self-contained dashboard artifact (index.html) from viz_data.json.
The word clouds are rendered in-page as interactive SVGs (DATA.cloud_svgs), not
embedded images. Embeds top-1200 papers for the in-page table; the full
4212-row corpus stays in data/papers.csv."""
import json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SOURCE_LABELS = {"curated": "Curated", "raw2": "Mined phrases", "openalex": "OpenAlex keywords"}


def main():
    curated = json.load(open(os.path.join(HERE, "data", "viz_data.json")))
    curated.pop("papers", None)
    curated["label"] = SOURCE_LABELS["curated"]
    sources = {"curated": curated}
    for s in ("raw2", "openalex"):
        p = os.path.join(HERE, "data", "src_" + s, "viz_data.json")
        if os.path.exists(p):
            sd = json.load(open(p)); sd.pop("papers", None); sd["label"] = SOURCE_LABELS[s]
            sources[s] = sd

    payload = json.dumps(sources, ensure_ascii=False, separators=(",", ":"))
    html = TEMPLATE.replace("/*__DATA__*/", payload)
    out = os.path.join(HERE, "web", "index.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"wrote {out}  ({os.path.getsize(out)/1024:.0f} KB)")


TEMPLATE = r"""<title>AI Safety Buzzwords — arXiv 2005–2026</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{
  --paper:#faf9f6; --plane:#f2f1ec; --card:#ffffff;
  --ink:#171613; --ink2:#57544d; --muted:#8a877f;
  --line:#e4e1d8; --line2:#d3cfc4;
  --accent:#1f5fb0; --accent-soft:#e7eef8;
  --g1:#1f5fb0; --g2:#1f7a1f; --g3:#b03a6e; --g4:#9a6a00;
  --g5:#0f7a58; --g6:#c14a1f; --g7:#4a3aa7; --g8:#b3332f;
  --shadow:0 1px 2px rgba(23,22,19,.05),0 8px 24px -12px rgba(23,22,19,.12);
}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme=light])){
  --paper:#141413; --plane:#0e0e0d; --card:#1c1c1a;
  --ink:#f4f2ec; --ink2:#c0bdb2; --muted:#8f8c83;
  --line:#2b2a27; --line2:#3a3934;
  --accent:#5598e7; --accent-soft:#1b2739;
  --g1:#5598e7; --g2:#38ad38; --g3:#e87ba4; --g4:#eda100;
  --g5:#1baf7a; --g6:#eb6834; --g7:#9085e9; --g8:#e66767;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
}}
:root[data-theme=dark]{
  --paper:#141413; --plane:#0e0e0d; --card:#1c1c1a;
  --ink:#f4f2ec; --ink2:#c0bdb2; --muted:#8f8c83;
  --line:#2b2a27; --line2:#3a3934;
  --accent:#5598e7; --accent-soft:#1b2739;
  --g1:#5598e7; --g2:#38ad38; --g3:#e87ba4; --g4:#eda100;
  --g5:#1baf7a; --g6:#eb6834; --g7:#9085e9; --g8:#e66767;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px -14px rgba(0,0,0,.6);
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
/* cross-artifact nav */
.nav{display:flex;gap:6px;align-items:center;padding:10px 0}
.nav a{display:flex;align-items:center;gap:6px;text-decoration:none;font:600 13px/1 system-ui;
  color:var(--ink2);border:1px solid var(--line2);background:var(--card);border-radius:9px;padding:8px 12px}
.nav a.cur{color:var(--ink);border-color:var(--accent);background:var(--accent-soft)}
.nav a:hover{color:var(--ink)}
.nav .sep{flex:1}
/* group-by segmented control */
.seg{display:inline-flex;background:var(--plane);border:1px solid var(--line);border-radius:10px;padding:3px;flex-wrap:wrap}
.seg button{border:0;background:transparent;color:var(--ink2);font:600 12.5px/1 system-ui;padding:7px 11px;border-radius:7px;cursor:pointer}
.seg button.on{background:var(--card);color:var(--ink);box-shadow:var(--shadow)}
.barlegend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:14px 2px 2px}
.barlegend .it{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--ink2)}
.barlegend .sw{width:11px;height:11px;border-radius:3px}
body{margin:0;background:var(--plane);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.55;
  font-size:16px;-webkit-font-smoothing:antialiased}
.mono{font-family:ui-monospace,"SF Mono",Menlo,Consolas,monospace}
.wrap{max-width:1120px;margin:0 auto;padding:0 22px}
h1,h2,h3{text-wrap:balance;line-height:1.15;margin:0}
a{color:var(--accent)}
.eyebrow{font:600 12px/1.4 ui-monospace,monospace;letter-spacing:.14em;
  text-transform:uppercase;color:var(--muted)}
.tnum{font-variant-numeric:tabular-nums}

/* header */
header{border-bottom:1px solid var(--line);background:
  linear-gradient(180deg,var(--paper),var(--plane))}
.hero{padding:46px 0 30px;display:grid;gap:16px}
.hero h1{font-size:clamp(30px,4.6vw,50px);font-weight:800;letter-spacing:-.02em}
.hero h1 em{font-style:normal;color:var(--accent)}
.lead{max-width:64ch;color:var(--ink2);font-size:17px}
.themebtn{position:fixed;top:14px;right:14px;z-index:20;width:38px;height:38px;
  border-radius:10px;border:1px solid var(--line2);background:var(--card);
  color:var(--ink);cursor:pointer;font-size:16px;box-shadow:var(--shadow)}

/* stat tiles */
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0 4px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:16px 16px 14px;box-shadow:var(--shadow)}
.tile .k{font:800 clamp(24px,3.4vw,34px)/1 system-ui;letter-spacing:-.02em}
.tile .l{margin-top:6px;color:var(--ink2);font-size:13px}
.tile .s{color:var(--muted);font-size:12px;margin-top:2px}

section{padding:40px 0}
section+section{border-top:1px solid var(--line)}
.sec-h{display:flex;align-items:baseline;justify-content:space-between;
  gap:14px;margin-bottom:6px;flex-wrap:wrap}
.sec-h h2{font-size:clamp(20px,2.6vw,27px);font-weight:750;letter-spacing:-.01em}
.sec-sub{color:var(--ink2);max-width:70ch;font-size:15px;margin:2px 0 22px}

/* word cloud (interactive SVG, recoloured by grouping) */
.cloud{border:1px solid var(--line);border-radius:16px;overflow:hidden;
  background:var(--card);box-shadow:var(--shadow);padding:6px;line-height:0}
.cloud svg{display:block;width:100%;height:auto}
.cloud text{cursor:default;transition:fill .15s,opacity .1s}
.legend{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:16px}
.legend .it{display:flex;align-items:center;gap:7px;font-size:13px;color:var(--ink2)}
.legend .sw{width:12px;height:12px;border-radius:3px;flex:none}

/* charts */
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;
  padding:20px 20px 8px;box-shadow:var(--shadow)}
.bars{display:grid;gap:7px}
.bar-row{display:grid;grid-template-columns:172px 1fr;align-items:center;gap:12px;
  cursor:default}
.bar-row .name{font-size:13.5px;text-align:right;color:var(--ink);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar-track{position:relative;height:22px;border-radius:5px;background:var(--plane)}
.bar-fill{position:absolute;inset:0 auto 0 0;border-radius:5px;min-width:2px;
  transition:filter .12s}
.bar-row:hover .bar-fill{filter:brightness(1.08)}
.bar-val{position:absolute;top:50%;transform:translateY(-50%);left:calc(100% + 8px);
  font:600 12.5px/1 ui-monospace,monospace;color:var(--ink2);white-space:nowrap}
.bar-val.inside{left:auto;right:8px;color:#fff}

/* timeline svg */
.tl{width:100%;height:260px;display:block;overflow:visible}
.tl .grid{stroke:var(--line);stroke-width:1}
.tl .axis{fill:var(--muted);font:11px ui-monospace,monospace}
.tl .area{fill:var(--accent);opacity:.16}
.tl .ln{fill:none;stroke:var(--accent);stroke-width:2}
.tl .dot{fill:var(--accent)}
.tl .hit{fill:transparent;cursor:pointer}
.tl .hit:hover + .mk,.tl .mk.on{opacity:1}
.tl .mk{opacity:0}
.tl .mkln{stroke:var(--line2);stroke-width:1;stroke-dasharray:3 3}

/* tables */
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:14px}
.inp{background:var(--card);border:1px solid var(--line2);border-radius:9px;
  padding:8px 11px;color:var(--ink);font-size:14px;min-width:210px}
.inp:focus{outline:2px solid var(--accent);outline-offset:1px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px solid var(--line2);background:var(--card);color:var(--ink2);
  border-radius:999px;padding:5px 11px;font-size:12.5px;cursor:pointer;
  display:flex;align-items:center;gap:6px;user-select:none}
.chip .sw{width:9px;height:9px;border-radius:2px}
.chip.on{color:#fff;border-color:transparent}
.tbl-scroll{overflow-x:auto;border:1px solid var(--line);border-radius:14px;
  box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;font-size:13.5px;background:var(--card)}
thead th{position:sticky;top:0;background:var(--card);z-index:1;
  text-align:left;padding:11px 12px;font:600 12px/1.2 system-ui;color:var(--ink2);
  border-bottom:1px solid var(--line2);cursor:pointer;white-space:nowrap;
  letter-spacing:.02em}
thead th .ar{color:var(--muted);font-size:10px}
tbody td{padding:9px 12px;border-bottom:1px solid var(--line)}
tbody tr:hover{background:var(--accent-soft)}
tbody tr:last-child td{border-bottom:none}
td.num{text-align:right;font-variant-numeric:tabular-nums;font-family:ui-monospace,monospace;color:var(--ink2)}
td.title a{color:var(--ink);text-decoration:none}
td.title a:hover{color:var(--accent);text-decoration:underline}
.gtag{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:6px;
  vertical-align:middle}
.termtags{display:flex;flex-wrap:wrap;gap:4px}
.tt{font:11px ui-monospace,monospace;background:var(--plane);color:var(--ink2);
  padding:1px 6px;border-radius:5px;white-space:nowrap}
.more{color:var(--muted);font-size:11px;text-align:center;padding:12px}

/* tooltip */
#tip{position:fixed;z-index:30;pointer-events:none;opacity:0;transition:opacity .1s;
  background:var(--ink);color:var(--paper);padding:7px 10px;border-radius:8px;
  font-size:12.5px;box-shadow:var(--shadow);max-width:260px}
#tip .tv{font-weight:700}

footer{padding:34px 0 60px;color:var(--muted);font-size:13px}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--accent);
  border-radius:12px;padding:14px 16px;color:var(--ink2);font-size:14px;margin-top:18px}
.note b{color:var(--ink)}
@media (max-width:720px){
  .tiles{grid-template-columns:repeat(2,1fr)}
  .bar-row{grid-template-columns:118px 1fr}
  .bar-row .name{font-size:12px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<button class="themebtn" id="themebtn" aria-label="Toggle theme">◐</button>
<div id="tip"></div>

<div class="wrap"><nav class="nav">
  <a class="cur" href="#">🧭 Word cloud</a>
  <a href="https://claude.ai/code/artifact/77473750-146a-4348-a4c1-5d476b986789">📈 Trends</a>
  <a href="https://claude.ai/code/artifact/8f0e56b3-eed4-414d-8414-585d553a26fe">🗂️ Groupings</a>
  <span class="sep"></span>
  <span class="eyebrow" style="align-self:center">Source</span>
  <div class="seg" id="srcseg"></div>
</nav></div>

<header><div class="wrap hero">
  <div class="eyebrow">arXiv · Semantic Scholar · 2005–2026</div>
  <h1>The vocabulary of <em>AI safety</em>, counted</h1>
  <p class="lead" id="lead"></p>
</div></header>

<div class="wrap">

  <section id="overview" style="border-top:none">
    <div class="tiles" id="tiles"></div>
    <div class="note">
      <b>How to read this.</b> arXiv has no keyword field, so “keyword” here means the buzzword
      appears in a paper’s title or abstract. Each term was retrieved from Semantic Scholar
      (Computer Science, 2005+), then <b>verified by exact phrase match</b> to strip out
      stemming noise (e.g.&nbsp;“scheme”≠“scheming”). Bar sizes count <b>distinct arXiv papers</b>;
      generic words like <span class="mono">bias</span> still catch some off-topic uses.
    </div>
  </section>

  <section id="cloud">
    <div class="sec-h"><h2>Buzzword cloud</h2></div>
    <p class="sec-sub"><b>Size</b> = <span id="sizecap">papers</span>; <b>colour</b> = grouping.
    Switch either below — size by any of 7 metrics (mentions, citations, impact, recency,
    momentum, debut/peak year); colour by any lens. (Size ≈ √metric.)</p>
    <div class="controls">
      <span class="eyebrow">Size</span>
      <div class="seg" id="cloudsizeseg"></div>
      <span class="eyebrow" style="margin-left:6px">Colour</span>
      <div class="seg" id="cloudlensseg"></div>
    </div>
    <div class="cloud" id="cloudbox" role="img" aria-label="Word cloud of AI safety buzzwords sized by paper count"></div>
    <div class="legend" id="legend"></div>
  </section>

  <section id="ranking">
    <div class="sec-h"><h2>Most-used buzzwords</h2>
      <span class="eyebrow" id="rankmode">by paper count</span></div>
    <p class="sec-sub">Top 26 terms by the chosen <b>weight</b> (papers, citations, citations/paper,
    recency or momentum); bar <b>colour</b> by any grouping lens.</p>
    <div class="controls">
      <span class="eyebrow">Size</span>
      <div class="seg" id="rankchips"></div>
      <span class="eyebrow" style="margin-left:6px">Colour</span>
      <div class="seg" id="lensseg"></div>
    </div>
    <div class="card"><div class="bars" id="bars"></div></div>
    <div class="barlegend" id="barlegend"></div>
  </section>

</div>

<footer><div class="wrap">
  Generated <span id="gen" class="mono"></span> · source: Semantic Scholar Graph API
  (Computer Science, year ≥ 2005) · matches verified by exact-phrase in title+abstract ·
  buzzwords from <span class="mono">ai-safety-concepts-glossary.md</span>.
</div></footer>

<script>
const SOURCES = /*__DATA__*/;
let curSource='curated';
let DATA = SOURCES[curSource];
const LEADS={
  curated:'<b id="leadn">—</b> canonical buzzwords curated from an AI-safety glossary, matched across arXiv abstracts by exact phrase — papers, dates and citations pulled from Semantic Scholar.',
  raw2:'<b id="leadn">—</b> candidate phrases discovered <b>bottom-up</b> from safety-paper abstracts (frequent n-grams), run through the same S2 pipeline. Noisier than the curated set — a look at what the corpus surfaces on its own.',
  openalex:'<b id="leadn">—</b> keywords/topics harvested <b>bottom-up</b> from <b>OpenAlex</b> for safety papers, run through the same S2 pipeline. Broad academic labels, not curated concepts.'};
const TILE1={curated:'from the glossary',raw2:'mined from abstracts',openalex:'OpenAlex keywords'};
const isDark = () => document.documentElement.getAttribute('data-theme')==='dark' ||
  (!document.documentElement.getAttribute('data-theme') && matchMedia('(prefers-color-scheme:dark)').matches);
const GC = () => isDark() ? DATA.group_color_dark : DATA.group_color;
/* grouping-lens helpers */
let curLens=Object.keys(DATA.lens_meta)[0];
const lensColors = () => { const m=DATA.lens_meta[curLens]; return isDark()?m.colors_dark:m.colors; };
const lensGroups = () => DATA.lens_meta[curLens].groups;
const grpOf = s => (s.lenses && s.lenses[curLens]) || s.group;
let statMap = {};
function buildStatMap(){ statMap={}; DATA.stats.forEach(s=>statMap[s.term]=s); }
buildStatMap();
const grpOfTerm = term => { const s=statMap[term]; return s?grpOf(s):null; };
const fmt = n => n.toLocaleString('en-US');
/* weight metrics (cloud size + bar length + sorting) */
const MFIELD = {papers:'n_papers', citations:'sum_citations', cpp:'cpp', recency:'recency', momentum:'momentum', debut:'debut', peak:'peak'};
const YEARM = k => k==='debut'||k==='peak';
const mVal = (s,k) => s[MFIELD[k]];
const sizeVal = (s,k) => YEARM(k) ? Math.max((mVal(s,k)||2005)-2004,1) : (mVal(s,k)||0);  // year -> years-since-2004
const mFmt = (k,v) => YEARM(k)?''+(v||'—'):k==='cpp'?(+v).toFixed(1):k==='recency'?v+'%':fmt(v);
const mLabel = k => (DATA.cloud_metrics.find(m=>m.key===k)||{}).label||k;
let curSize='papers';
const WSHORT={papers:'Papers',citations:'Citations',cpp:'Cit/paper',recency:'Recency',momentum:'Momentum',debut:'Debut yr',peak:'Peak yr'};
const LSHORT={glossary:'Glossary',mit:'MIT risk',semantic:'Semantic',cooccur:'Co-occurrence'};
const tip = document.getElementById('tip');
function showTip(html,x,y){tip.innerHTML=html;tip.style.opacity=1;
  const w=tip.offsetWidth,h=tip.offsetHeight;
  tip.style.left=Math.min(x+14,innerWidth-w-8)+'px';
  tip.style.top=Math.max(8,y-h-12)+'px';}
function hideTip(){tip.style.opacity=0;}

/* theme toggle */
const btn=document.getElementById('themebtn');
btn.onclick=()=>{const r=document.documentElement;
  const dark=r.getAttribute('data-theme')==='dark' ||
    (!r.getAttribute('data-theme')&&matchMedia('(prefers-color-scheme:dark)').matches);
  r.setAttribute('data-theme',dark?'light':'dark');renderAll();};

/* tiles */
function tiles(){
  const t=[
    ['n_buzzwords_v', DATA.n_buzzwords, curSource==='curated'?'buzzwords tracked':'candidate terms', TILE1[curSource]||''],
    ['p', fmt(DATA.n_papers), 'arXiv papers', 'deduplicated corpus'],
    ['c', fmt(DATA.total_citations), 'total citations', 'across the corpus'],
    ['y', DATA.year_min+'–'+DATA.year_max, 'year span', 'peak 2023→'],
  ];
  document.getElementById('tiles').innerHTML=t.map(x=>
    `<div class="tile"><div class="k tnum">${x[1]}</div><div class="l">${x[2]}</div>
     <div class="s">${x[3]}</div></div>`).join('');
}

/* interactive SVG cloud — sized by the selected metric, recoloured by the selected grouping */
function cloudTip(s){
  return `<span class="tv">${s.term}</span><br>
    ${fmt(s.n_papers)} papers · ${fmt(s.sum_citations)} citations · ${(+s.cpp).toFixed(1)}/paper<br>
    <span style="color:var(--muted)">${s.recency}% since ’24 · ${grpOf(s)}</span>`;
}
function renderCloud(){
  const box=document.getElementById('cloudbox');
  if(box.dataset.metric!==curSize){                 // swap layout when the size metric changes
    box.innerHTML=DATA.cloud_svgs[curSize]; box.dataset.metric=curSize;
    box.querySelectorAll('text[data-term]').forEach(t=>{
      const s=statMap[t.getAttribute('data-term')]; if(!s) return;
      t.onmousemove=e=>showTip(cloudTip(s),e.clientX,e.clientY);
      t.onmouseleave=hideTip;
    });
  }
  const lc=lensColors();
  box.querySelectorAll('text[data-term]').forEach(t=>{
    const g=grpOfTerm(t.getAttribute('data-term'));
    t.style.fill=g?(lc[g]||'var(--muted)'):'var(--muted)';
  });
  document.getElementById('sizecap').textContent=mLabel(curSize).toLowerCase();
}
function buildSizeSeg(){
  const el=document.getElementById('cloudsizeseg');
  el.innerHTML=DATA.cloud_metrics.map(m=>
    `<button data-s="${m.key}" class="${m.key===curSize?'on':''}">${WSHORT[m.key]}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    curSize=b.dataset.s;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
    renderCloud();
  });
}
/* legend under the cloud — follows the current grouping */
function legend(){
  const lc=lensColors();
  document.getElementById('legend').innerHTML=lensGroups().map(g=>
    `<span class="it"><span class="sw" style="background:${lc[g]}"></span>${g}</span>`).join('');
}

/* ranking bars */
let rankMode='papers';
function bars(){
  const lc=lensColors();
  const rows=[...DATA.stats].sort((a,b)=>sizeVal(b,rankMode)-sizeVal(a,rankMode)).slice(0,26);
  const max=Math.max(...rows.map(r=>sizeVal(r,rankMode)))||1;
  const el=document.getElementById('bars');
  el.innerHTML=rows.map(r=>{
    const pct=Math.max(1.5,sizeVal(r,rankMode)/max*86);   // cap so the value label fits outside
    return `<div class="bar-row" data-t="${r.term}">
      <div class="name" title="${r.term}">${r.term}</div>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${lc[grpOf(r)]||'var(--muted)'}"></div>
      <span class="bar-val" style="left:calc(${pct}% + 8px)">${mFmt(rankMode,mVal(r,rankMode))}</span></div></div>`;
  }).join('');
  el.querySelectorAll('.bar-row').forEach(row=>{
    const s=statMap[row.dataset.t];
    row.onmousemove=e=>showTip(
      `<span class="tv">${s.term}</span><br>${fmt(s.n_papers)} papers · ${fmt(s.sum_citations)} citations · ${(+s.cpp).toFixed(1)}/paper<br>
       <span style="color:var(--muted)">${s.recency}% since ’24 · ${grpOf(s)}</span>`,e.clientX,e.clientY);
    row.onmouseleave=hideTip;
  });
  document.getElementById('rankmode').textContent='by '+mLabel(rankMode).toLowerCase();
}
function barLegend(){
  const lc=lensColors();
  document.getElementById('barlegend').innerHTML=lensGroups().map(g=>
    `<span class="it"><span class="sw" style="background:${lc[g]}"></span>${g}</span>`).join('');
}
function buildRankChips(){
  const el=document.getElementById('rankchips');
  el.innerHTML=DATA.cloud_metrics.map(m=>
    `<button data-m="${m.key}" class="${m.key===rankMode?'on':''}">${WSHORT[m.key]}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>{
    rankMode=b.dataset.m;
    el.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
    bars();
  });
}
/* grouping-lens selector — one control mirrored on the cloud and the ranking;
   recolours cloud + legend + bars + table together */
function buildLensSegs(){
  ['cloudlensseg','lensseg'].forEach(id=>{
    const el=document.getElementById(id); if(!el) return;
    el.innerHTML=Object.entries(DATA.lens_meta).map(([k,m])=>
      `<button data-l="${k}" class="${k===curLens?'on':''}">${LSHORT[k]}</button>`).join('');
    el.querySelectorAll('button').forEach(b=>b.onclick=()=>setLens(b.dataset.l));
  });
}
function setLens(lens){
  curLens=lens;
  document.querySelectorAll('#cloudlensseg button, #lensseg button')
    .forEach(x=>x.classList.toggle('on',x.dataset.l===lens));
  renderCloud();legend();bars();barLegend();
}

/* timeline */
function timeline(){
  const svg=document.getElementById('tl');
  const W=svg.clientWidth||900,H=240,PL=38,PR=14,PT=12,PB=26;
  const yr=DATA.yearly.filter(d=>d.year>=2005);
  const xs=v=>PL+(v-yr[0].year)/(yr[yr.length-1].year-yr[0].year)*(W-PL-PR);
  const maxN=Math.max(...yr.map(d=>d.n));
  const ys=v=>PT+(1-v/maxN)*(H-PT-PB);
  let g='';
  const ticks=[0,Math.round(maxN/2),maxN];
  ticks.forEach(t=>{g+=`<line class="grid" x1="${PL}" x2="${W-PR}" y1="${ys(t)}" y2="${ys(t)}"/>
    <text class="axis" x="${PL-6}" y="${ys(t)+3}" text-anchor="end">${fmt(t)}</text>`;});
  yr.forEach(d=>{if(d.year%3===0||d.year===yr[yr.length-1].year)
    g+=`<text class="axis" x="${xs(d.year)}" y="${H-8}" text-anchor="middle">${d.year}</text>`;});
  const pts=yr.map(d=>`${xs(d.year)},${ys(d.n)}`).join(' ');
  g+=`<polygon class="area" points="${PL},${ys(0)} ${pts} ${W-PR},${ys(0)}"/>`;
  g+=`<polyline class="ln" points="${pts}"/>`;
  yr.forEach(d=>{
    g+=`<circle class="dot" cx="${xs(d.year)}" cy="${ys(d.n)}" r="2.5"/>`;
    g+=`<g class="mk"><line class="mkln" x1="${xs(d.year)}" x2="${xs(d.year)}" y1="${PT}" y2="${H-PB}"/>
      <circle cx="${xs(d.year)}" cy="${ys(d.n)}" r="4.5" fill="var(--accent)" stroke="var(--card)" stroke-width="2"/></g>`;
    g+=`<rect class="hit" x="${xs(d.year)-((W-PL-PR)/yr.length)/2}" y="${PT}"
      width="${(W-PL-PR)/yr.length}" height="${H-PT-PB}"
      data-y="${d.year}" data-n="${d.n}"/>`;
  });
  svg.setAttribute('viewBox',`0 0 ${W} ${H}`);svg.innerHTML=g;
  svg.querySelectorAll('.hit').forEach(h=>{
    h.onmousemove=e=>showTip(`<span class="tv">${h.dataset.y}</span><br>${fmt(h.dataset.n)} papers`,e.clientX,e.clientY);
    h.onmouseleave=hideTip;
  });
}

function renderAll(){document.getElementById('lead').innerHTML=LEADS[curSource]||LEADS.curated;
  tiles();buildLensSegs();buildSizeSeg();buildRankChips();renderCloud();legend();bars();barLegend();
  document.getElementById('leadn').textContent=DATA.n_buzzwords;}
/* source switcher (curated vs candidate corpora) */
function buildSrcSeg(){
  const el=document.getElementById('srcseg'); if(!el) return;
  el.innerHTML=Object.keys(SOURCES).map(s=>
    `<button data-s="${s}" class="${s===curSource?'on':''}">${SOURCES[s].label}</button>`).join('');
  el.querySelectorAll('button').forEach(b=>b.onclick=()=>setSource(b.dataset.s));
}
function setSource(src){
  curSource=src; DATA=SOURCES[src];
  curLens=Object.keys(DATA.lens_meta)[0]; curSize='papers'; rankMode='papers';
  buildStatMap();
  document.querySelectorAll('#srcseg button').forEach(b=>b.classList.toggle('on',b.dataset.s===src));
  document.getElementById('cloudbox').dataset.metric='';   // force cloud SVG re-inject
  renderAll();
}
document.getElementById('gen').textContent=DATA.generated;
buildSrcSeg();
renderAll();
matchMedia('(prefers-color-scheme:dark)').addEventListener('change',renderAll);
</script>
"""

if __name__ == "__main__":
    main()
