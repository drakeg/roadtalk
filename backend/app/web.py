from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)


@router.get("/", response_class=HTMLResponse)
async def web_home() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoadTalk | Local Operations Dashboard</title>
  <style>
    :root { color-scheme:dark; --bg:#07141b; --panel:#10232e; --panel2:#0c1c25; --text:#eff8fb; --muted:#91aab5; --accent:#f2b84b; --ok:#69d391; --bad:#ff7b7b; --info:#77b9ff; --line:rgba(255,255,255,.10); }
    * { box-sizing:border-box; }
    body { margin:0; min-height:100vh; background:radial-gradient(circle at 80% 0,rgba(242,184,75,.12),transparent 30rem),linear-gradient(145deg,#061118,var(--bg) 48%,#091b24); color:var(--text); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
    .wrap { width:min(1240px,calc(100% - 32px)); margin:0 auto; }
    header { padding:22px 0 12px; position:sticky; top:0; z-index:10; backdrop-filter:blur(16px); background:rgba(7,20,27,.78); border-bottom:1px solid var(--line); }
    nav,.row,.card-head,.metric-line { display:flex; align-items:center; justify-content:space-between; gap:14px; }
    .brand { display:flex; align-items:center; gap:12px; font-weight:850; font-size:18px; }
    .mark { width:42px; height:42px; border-radius:13px; display:grid; place-items:center; background:var(--accent); color:#172028; font-weight:900; box-shadow:0 8px 28px rgba(242,184,75,.18); }
    .navlinks { display:flex; flex-wrap:wrap; gap:8px; }
    a.button { color:var(--text); text-decoration:none; border:1px solid var(--line); background:rgba(255,255,255,.035); padding:9px 12px; border-radius:9px; font-weight:650; font-size:13px; }
    a.button:hover { background:rgba(255,255,255,.075); }
    main { padding:34px 0 70px; }
    .title-row { margin-bottom:22px; }
    .eyebrow { color:var(--accent); font-size:11px; font-weight:850; letter-spacing:.16em; text-transform:uppercase; }
    h1 { margin:7px 0 7px; font-size:clamp(30px,4vw,46px); letter-spacing:-.035em; }
    .subtitle { color:var(--muted); margin:0; }
    .status-pill { display:inline-flex; align-items:center; gap:8px; border:1px solid var(--line); background:rgba(255,255,255,.04); padding:9px 12px; border-radius:999px; color:var(--muted); font-weight:700; }
    .dot { width:9px; height:9px; border-radius:50%; background:var(--accent); box-shadow:0 0 0 4px rgba(242,184,75,.11); }
    .dot.ok { background:var(--ok); box-shadow:0 0 0 4px rgba(105,211,145,.11); }
    .dot.bad { background:var(--bad); box-shadow:0 0 0 4px rgba(255,123,123,.11); }
    .metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:14px; }
    .card { border:1px solid var(--line); background:linear-gradient(180deg,rgba(16,35,46,.92),rgba(12,28,37,.88)); border-radius:17px; box-shadow:0 18px 54px rgba(0,0,0,.18); }
    .metric { padding:19px; }
    .metric-label { color:var(--muted); font-size:12px; font-weight:700; }
    .metric-value { font-size:29px; font-weight:850; margin-top:7px; letter-spacing:-.03em; }
    .metric-foot { color:var(--muted); font-size:11px; margin-top:5px; }
    .grid-main { display:grid; grid-template-columns:1.45fr .85fr; gap:14px; }
    .panel { padding:20px; min-width:0; }
    .card-head { margin-bottom:18px; }
    .card-head h2 { margin:0; font-size:17px; }
    .tag { font-size:11px; color:var(--muted); border:1px solid var(--line); border-radius:999px; padding:6px 9px; }
    .chart-wrap { height:260px; position:relative; }
    canvas { width:100%; height:100%; display:block; }
    .service-list { display:grid; gap:10px; }
    .service { padding:13px 14px; border:1px solid var(--line); border-radius:12px; background:rgba(255,255,255,.025); }
    .service-name { font-weight:750; }
    .service-detail { color:var(--muted); font-size:12px; margin-top:4px; }
    .mini-dot { width:8px; height:8px; border-radius:50%; background:var(--muted); flex:0 0 auto; }
    .mini-dot.ok { background:var(--ok); } .mini-dot.bad { background:var(--bad); }
    .lower { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:14px; }
    .log { height:270px; overflow:auto; background:#071017; border:1px solid var(--line); border-radius:12px; padding:12px; font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:12px; line-height:1.6; }
    .log-entry { display:grid; grid-template-columns:74px 55px 1fr; gap:8px; border-bottom:1px solid rgba(255,255,255,.045); padding:4px 0; }
    .log-time { color:#708996; } .log-info { color:var(--info); } .log-ok { color:var(--ok); } .log-error { color:var(--bad); }
    .details { display:grid; gap:0; }
    .metric-line { padding:12px 0; border-bottom:1px solid var(--line); }
    .metric-line:last-child { border-bottom:0; }
    .details .key { color:var(--muted); }
    .details .val { font-weight:750; text-align:right; overflow-wrap:anywhere; }
    footer { color:var(--muted); border-top:1px solid var(--line); padding:22px 0 35px; font-size:12px; }
    @media(max-width:900px){ .metrics{grid-template-columns:repeat(2,1fr)} .grid-main,.lower{grid-template-columns:1fr} }
    @media(max-width:600px){ .metrics{grid-template-columns:1fr} nav,.title-row{align-items:flex-start;flex-direction:column} .log-entry{grid-template-columns:66px 48px 1fr} }
  </style>
</head>
<body>
<header><div class="wrap"><nav><div class="brand"><div class="mark">RT</div><div>RoadTalk <span style="color:var(--muted);font-weight:600">Local Ops</span></div></div><div class="navlinks"><a class="button" href="/docs">Swagger</a><a class="button" href="/redoc">ReDoc</a><a class="button" href="/health/ready">Raw readiness</a><a class="button" href="/api/v1/system/version">Version JSON</a></div></nav></div></header>
<main class="wrap">
  <section class="title-row row"><div><div class="eyebrow">Local operations dashboard</div><h1>RoadTalk service overview</h1><p class="subtitle">Live local health, latency, environment, and browser-observed operational events.</p></div><div class="status-pill"><span id="status-dot" class="dot"></span><span id="status-text">Checking services…</span></div></section>

  <section class="metrics">
    <article class="card metric"><div class="metric-label">API readiness</div><div class="metric-value" id="ready-value">—</div><div class="metric-foot" id="ready-foot">Waiting for first poll</div></article>
    <article class="card metric"><div class="metric-label">Latest latency</div><div class="metric-value"><span id="latency-value">—</span><span style="font-size:14px;color:var(--muted)"> ms</span></div><div class="metric-foot">Readiness + version round trip</div></article>
    <article class="card metric"><div class="metric-label">Successful polls</div><div class="metric-value" id="poll-value">0</div><div class="metric-foot">Refreshes every 5 seconds</div></article>
    <article class="card metric"><div class="metric-label">Dashboard uptime</div><div class="metric-value" id="uptime-value">00:00</div><div class="metric-foot">Since this page was opened</div></article>
  </section>

  <section class="grid-main">
    <article class="card panel"><div class="card-head"><h2>API response latency</h2><span class="tag">last 30 samples</span></div><div class="chart-wrap"><canvas id="latency-chart" aria-label="API response latency graph"></canvas></div></article>
    <article class="card panel"><div class="card-head"><h2>Service health</h2><span class="tag">live</span></div><div class="service-list">
      <div class="service"><div class="row"><div><div class="service-name">FastAPI</div><div class="service-detail">/health/live</div></div><span id="api-dot" class="mini-dot"></span></div></div>
      <div class="service"><div class="row"><div><div class="service-name">Database readiness</div><div class="service-detail">Registered readiness dependency</div></div><span id="db-dot" class="mini-dot"></span></div></div>
      <div class="service"><div class="row"><div><div class="service-name">Version endpoint</div><div class="service-detail">/api/v1/system/version</div></div><span id="version-dot" class="mini-dot"></span></div></div>
      <div class="service"><div class="row"><div><div class="service-name">PTT media provider</div><div class="service-detail">Expected disabled for $0 local mode</div></div><span class="mini-dot"></span></div></div>
    </div></article>
  </section>

  <section class="lower">
    <article class="card panel"><div class="card-head"><h2>Operational event log</h2><span class="tag">browser-observed</span></div><div id="event-log" class="log"><div class="log-entry"><span class="log-time">--:--:--</span><span class="log-info">INFO</span><span>Dashboard initialized; waiting for service poll.</span></div></div></article>
    <article class="card panel"><div class="card-head"><h2>Runtime details</h2><span class="tag">current</span></div><div class="details">
      <div class="metric-line"><span class="key">Environment</span><span class="val" id="environment">—</span></div>
      <div class="metric-line"><span class="key">RoadTalk version</span><span class="val" id="version">—</span></div>
      <div class="metric-line"><span class="key">API base</span><span class="val">/api/v1</span></div>
      <div class="metric-line"><span class="key">Database check</span><span class="val" id="database-status">—</span></div>
      <div class="metric-line"><span class="key">Current browser endpoint</span><span class="val" id="browser-endpoint">—</span></div>
      <div class="metric-line"><span class="key">Last refresh</span><span class="val" id="last-refresh">—</span></div>
    </div></article>
  </section>
</main>
<footer><div class="wrap">RoadTalk local alpha · No external monitoring service required · Data shown here comes from local RoadTalk endpoints and this browser session.</div></footer>
<script>
  const startTime=Date.now(); const samples=[]; let successPolls=0; let lastState='';
  const $=id=>document.getElementById(id);
  function timestamp(){return new Date().toLocaleTimeString([], {hour12:false});}
  function log(level,message){const box=$('event-log'); const row=document.createElement('div'); row.className='log-entry'; const cls=level==='OK'?'log-ok':level==='ERROR'?'log-error':'log-info'; row.innerHTML=`<span class="log-time">${timestamp()}</span><span class="${cls}">${level}</span><span></span>`; row.lastElementChild.textContent=message; box.appendChild(row); while(box.children.length>60)box.removeChild(box.firstChild); box.scrollTop=box.scrollHeight;}
  function setDot(id,state){const el=$(id); el.className='mini-dot '+(state?'ok':'bad');}
  function drawChart(){const canvas=$('latency-chart'); const ratio=window.devicePixelRatio||1; const rect=canvas.getBoundingClientRect(); canvas.width=Math.max(1,rect.width*ratio); canvas.height=Math.max(1,rect.height*ratio); const ctx=canvas.getContext('2d'); ctx.scale(ratio,ratio); const w=rect.width,h=rect.height,pad=28; ctx.clearRect(0,0,w,h); ctx.strokeStyle='rgba(255,255,255,.08)'; ctx.lineWidth=1; for(let i=0;i<4;i++){const y=pad+(h-pad*2)*(i/3); ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke();} if(samples.length<2)return; const max=Math.max(50,...samples.map(x=>x.ms))*1.15; ctx.strokeStyle='#f2b84b';ctx.lineWidth=2.2;ctx.beginPath(); samples.forEach((s,i)=>{const x=pad+(w-pad*2)*(i/Math.max(1,samples.length-1));const y=h-pad-(h-pad*2)*(s.ms/max); if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);});ctx.stroke(); ctx.fillStyle='#91aab5';ctx.font='11px system-ui';ctx.fillText(`${Math.round(max)} ms`,2,pad+4);ctx.fillText('0 ms',7,h-pad+4);}
  async function poll(){const started=performance.now(); try{const [liveResp,readyResp,versionResp]=await Promise.all([fetch('/health/live',{cache:'no-store'}),fetch('/health/ready',{cache:'no-store'}),fetch('/api/v1/system/version',{cache:'no-store'})]); const elapsed=Math.round(performance.now()-started); if(!liveResp.ok||!readyResp.ok||!versionResp.ok)throw new Error('One or more RoadTalk endpoints returned an error'); const live=await liveResp.json();const ready=await readyResp.json();const version=await versionResp.json(); const healthy=live.status==='ok'&&ready.status==='ready'; successPolls++; samples.push({ms:elapsed}); if(samples.length>30)samples.shift(); $('latency-value').textContent=elapsed;$('poll-value').textContent=successPolls;$('ready-value').textContent=healthy?'READY':'DEGRADED';$('ready-foot').textContent=healthy?'All registered checks passed':'One or more checks failed'; $('environment').textContent=version.environment;$('version').textContent=version.version;$('last-refresh').textContent=timestamp(); const db=ready.checks&&Object.prototype.hasOwnProperty.call(ready.checks,'database')?ready.checks.database:'not registered'; $('database-status').textContent=db; setDot('api-dot',live.status==='ok');setDot('version-dot',true);setDot('db-dot',db==='ready'||db==='not registered'); $('status-dot').className='dot '+(healthy?'ok':'bad');$('status-text').textContent=healthy?'RoadTalk ready':'RoadTalk degraded'; if(lastState!==String(healthy)){log(healthy?'OK':'ERROR',healthy?'RoadTalk readiness is healthy.':'RoadTalk readiness is degraded.');lastState=String(healthy);} else {log('INFO',`Health poll completed in ${elapsed} ms; database=${db}.`);} drawChart(); }catch(err){samples.push({ms:Math.round(performance.now()-started)});if(samples.length>30)samples.shift();$('ready-value').textContent='DOWN';$('ready-foot').textContent='Health poll failed';$('status-dot').className='dot bad';$('status-text').textContent='RoadTalk unavailable';setDot('api-dot',false);setDot('db-dot',false);setDot('version-dot',false);log('ERROR',err.message||'Health poll failed.');drawChart();}}
  function tick(){const sec=Math.floor((Date.now()-startTime)/1000);const m=Math.floor(sec/60);const s=sec%60;$('uptime-value').textContent=`${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;}
  $('browser-endpoint').textContent=window.location.origin; poll(); setInterval(poll,5000); setInterval(tick,1000); window.addEventListener('resize',drawChart);
</script>
</body>
</html>"""
    )
