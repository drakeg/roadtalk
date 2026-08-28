# ruff: noqa: E501

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)


@router.get("/audience", response_class=HTMLResponse)
async def audience_mode_page() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoadTalk | Audience Mode</title>
  <style>
    :root{color-scheme:dark;--bg:#07141b;--panel:#10232e;--text:#f2f7f9;--muted:#8fa7b2;--accent:#f2b84b;--green:#70da96;--red:#ff7979;--line:rgba(255,255,255,.1)}
    *{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;min-height:100vh}.wrap{width:min(760px,calc(100% - 28px));margin:auto}header{border-bottom:1px solid var(--line);padding:18px 0}.nav{display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-weight:850}.navlinks{display:flex;gap:12px;flex-wrap:wrap}a{color:var(--text)}main{padding:38px 0}.card{border:1px solid var(--line);background:var(--panel);border-radius:18px;padding:22px;margin-bottom:16px}.eyebrow{color:var(--accent);font-size:11px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(30px,6vw,46px);margin:8px 0 12px}.body{color:var(--muted);line-height:1.6}.options{display:grid;gap:12px}.option{width:100%;text-align:left;border:2px solid var(--line);background:rgba(255,255,255,.025);color:var(--text);padding:18px;border-radius:14px;cursor:pointer}.option[aria-pressed="true"]{border-color:var(--accent)}.option:disabled{opacity:.55;cursor:not-allowed}.option strong{display:block;font-size:19px;margin-bottom:6px}.status{font-weight:750}.good{color:var(--green)}.bad{color:var(--red)}
  </style>
</head>
<body>
<header><div class="wrap nav"><div class="brand">RoadTalk · Audience Mode</div><div class="navlinks"><a href="/">Web Radio</a><a href="/map">Map</a><a href="/ops">Operations</a></div></div></header>
<main class="wrap">
  <div class="eyebrow">Who should you hear?</div>
  <h1>Nearby or Same road</h1>
  <p class="body">Nearby is the default. Same road only narrows the already-authorized nearby audience when RoadTalk can safely match current route context. RoadTalk never shows a road name, direction, exact distance, who matched, or why someone did not match.</p>
  <section class="card" aria-live="polite"><div id="status" class="status">Loading audience mode…</div><p class="body">If Same road becomes unavailable, RoadTalk fails closed instead of silently widening your audience back to Nearby.</p></section>
  <section class="card options" aria-label="Audience mode">
    <button id="nearby" class="option" type="button" aria-pressed="false"><strong>Nearby</strong><span class="body">Hear eligible RoadTalk users nearby on your selected channel.</span></button>
    <button id="same-road" class="option" type="button" aria-pressed="false"><strong>Same road</strong><span class="body">Restrict eligible nearby audio to users RoadTalk can safely match to current route context.</span></button>
  </section>
</main>
<script>
const state={access:null,refresh:null,receipt:null,changing:false};
const $=id=>document.getElementById(id);
function headers(){return state.access?{Authorization:`Bearer ${state.access}`}:{}}
async function refresh(){if(!state.refresh)return false;const r=await fetch('/api/v1/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:state.refresh})});if(!r.ok)return false;const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh);return true}
async function raw(path,opts={}){return fetch(path,{...opts,headers:{Accept:'application/json','Content-Type':'application/json',...(opts.headers||{}),...headers()}})}
async function api(path,opts={}){let r=await raw(path,opts);if(r.status===401&&await refresh())r=await raw(path,opts);if(!r.ok)throw new Error('request failed');const b=await r.json();for(const key of ['road_name','route','provider','provider_corridor_ref','corridor_digest','direction','latitude','longitude','distance_m','bearing','account_id','device_id','participant_ref','eligibility_reason'])if(key in b)throw new Error('invalid response');return b}
async function ensureSession(){state.access=localStorage.getItem('rt_access');state.refresh=localStorage.getItem('rt_refresh');if(state.access){try{await api('/api/v1/auth/session');return}catch{}}const install=localStorage.getItem('rt_install')||`web-${crypto.randomUUID()}`;localStorage.setItem('rt_install',install);const r=await fetch('/api/v1/auth/anonymous',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({installation_id:install,platform:'web'})});if(!r.ok)throw new Error('session unavailable');const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh)}
function render(){const r=state.receipt;$('nearby').disabled=state.changing||!r;$('same-road').disabled=state.changing||!r;$('nearby').setAttribute('aria-pressed',String(r?.mode==='nearby'));$('same-road').setAttribute('aria-pressed',String(r?.mode==='same_road'));const text=state.changing?'Matching…':!r?'Audience mode unavailable.':r.mode==='same_road'&&r.availability==='unavailable'?'Same road is unavailable right now.':r.mode==='same_road'?'Same road is active.':'Nearby is active.';$('status').textContent=text;$('status').className='status '+(r&&(!state.changing)&&(r.mode==='nearby'||r.availability==='available')?'good':r&&!state.changing?'bad':'')}
async function load(){try{await ensureSession();state.receipt=await api('/api/v1/me/route-mode');render()}catch{$('status').textContent='Audience mode is unavailable right now.';$('status').className='status bad'}}
async function choose(mode){if(!state.receipt||state.changing||state.receipt.mode===mode)return;state.changing=true;render();try{state.receipt=await api('/api/v1/me/route-mode',{method:'PUT',body:JSON.stringify({mode,expected_version:state.receipt.version})})}catch{$('status').textContent='RoadTalk could not update your audience mode.';$('status').className='status bad'}finally{state.changing=false;render()}}
$('nearby').addEventListener('click',()=>void choose('nearby'));$('same-road').addEventListener('click',()=>void choose('same_road'));void load();
</script>
</body>
</html>"""
    )
