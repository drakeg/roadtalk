# ruff: noqa: E501

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)

_DASHBOARD = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>RoadTalk | Home</title>
  <style>
    :root{color-scheme:dark;--bg:#07141b;--panel:#10232e;--text:#f2f7f9;--muted:#abc0c9;--accent:#f2b84b;--green:#70da96;--line:rgba(255,255,255,.12)}
    *{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(circle at 75% 0,rgba(242,184,75,.16),transparent 34rem),var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}.wrap{width:min(1120px,calc(100% - 32px));margin:auto}header{border-bottom:1px solid var(--line);background:rgba(7,20,27,.86);backdrop-filter:blur(14px)}nav{min-height:72px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-size:20px;font-weight:900;letter-spacing:-.02em}.navlinks{display:flex;gap:8px;flex-wrap:wrap}a{color:inherit}.button,.card{text-decoration:none;border:1px solid var(--line);border-radius:13px;background:rgba(255,255,255,.04)}.button{padding:9px 13px;font-weight:750}.button.primary{background:var(--accent);color:#172028;border-color:transparent}main{padding:64px 0 72px}.hero{display:grid;grid-template-columns:1.4fr .75fr;gap:28px;align-items:end;margin-bottom:42px}.eyebrow{color:var(--accent);font-size:12px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(42px,7vw,74px);line-height:1;letter-spacing:-.055em;margin:12px 0 18px}.lead{color:var(--muted);font-size:19px;line-height:1.6;max-width:720px}.status{padding:22px;border:1px solid var(--line);border-radius:18px;background:rgba(16,35,46,.8)}.status h2{margin:0 0 14px;font-size:15px}.line{display:flex;justify-content:space-between;gap:16px;padding:10px 0;border-top:1px solid var(--line)}.label{color:var(--muted)}.value{font-weight:800;text-align:right}.ok{color:var(--green)}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.card{display:block;padding:23px;min-height:170px;transition:transform .15s,border-color .15s}.card:hover{transform:translateY(-2px);border-color:rgba(242,184,75,.55)}.card .icon{font-size:23px;color:var(--accent)}.card h2{margin:20px 0 8px;font-size:21px}.card p{margin:0;color:var(--muted);line-height:1.5}.card.primary-card{background:linear-gradient(145deg,rgba(242,184,75,.18),rgba(16,35,46,.88))}.privacy{margin-top:28px;color:var(--muted);font-size:13px;line-height:1.55}.privacy strong{color:var(--text)}
    @media(max-width:820px){.hero{grid-template-columns:1fr}.grid{grid-template-columns:repeat(2,1fr)}main{padding-top:40px}}@media(max-width:560px){nav{align-items:flex-start;flex-direction:column;padding:17px 0}.grid{grid-template-columns:1fr}h1{font-size:46px}}
  </style>
</head>
<body>
<header><div class="wrap"><nav aria-label="RoadTalk"><div class="brand">RoadTalk</div><div class="navlinks"><a class="button" href="/account">Account</a><a class="button primary" href="/radio">Open radio</a></div></nav></div></header>
<main class="wrap">
  <section class="hero"><div><div class="eyebrow">Your RoadTalk dashboard</div><h1>Ready for the road.</h1><p class="lead">Start a nearby conversation, check privacy-limited map awareness, or manage the RoadTalk identity that travels with you.</p></div><aside class="status" aria-labelledby="status-title"><h2 id="status-title">Current status</h2><div class="line"><span class="label">Service</span><span id="service" class="value">Checking…</span></div><div class="line"><span class="label">Session</span><span id="session" class="value">Checking…</span></div><div class="line"><span class="label">Call sign</span><span id="callsign" class="value">—</span></div></aside></section>
  <section class="grid" aria-label="RoadTalk destinations">
    <a class="card primary-card" href="/radio"><span class="icon">◉</span><h2>Radio</h2><p>Choose a channel, listen nearby, and hold to talk.</p></a>
    <a class="card" href="/map"><span class="icon">⌖</span><h2>Map</h2><p>See privacy-limited awareness without exposing precise routes.</p></a>
    <a class="card" href="/audience"><span class="icon">⌁</span><h2>Audience</h2><p>Follow route context and listen without transmitting.</p></a>
    <a class="card" href="/account"><span class="icon">RT</span><h2>Account</h2><p>Log in, create an account, or protect a guest profile.</p></a>
    <a class="card" href="/notifications"><span class="icon">◇</span><h2>Notifications</h2><p>Review safety-focused alerts and delivery status.</p></a>
    <a class="card" href="/ops"><span class="icon">⚙</span><h2>Operations</h2><p>Open the local service dashboard for operators.</p></a>
  </section>
  <p class="privacy"><strong>Privacy by design:</strong> this dashboard shows only service readiness, session type, and your public call sign. It does not display coordinates, routes, account identifiers, device identifiers, or session identifiers.</p>
</main>
<script>
const $=id=>document.getElementById(id),access=()=>localStorage.getItem('rt_access'),refreshToken=()=>localStorage.getItem('rt_refresh');
async function refresh(){const token=refreshToken();if(!token)return false;const r=await fetch('/api/v1/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:token})});if(!r.ok)return false;const b=await r.json();localStorage.setItem('rt_access',b.access_token);localStorage.setItem('rt_refresh',b.refresh_token);return true}
async function auth(path){let token=access();if(!token)return null;let r=await fetch(path,{headers:{Authorization:`Bearer ${token}`}});if(r.status===401&&await refresh()){token=access();r=await fetch(path,{headers:{Authorization:`Bearer ${token}`}})}return r.ok?await r.json():null}
async function paint(){try{const r=await fetch('/health/ready',{headers:{Accept:'application/json'}});$('service').textContent=r.ok?'Ready':'Unavailable';$('service').className='value '+(r.ok?'ok':'')}catch{$('service').textContent='Unavailable'}
if(!access()&&!refreshToken()){$('session').textContent='Signed out';$('callsign').innerHTML='<a href="/account">Log in or create account</a>';return}const session=await auth('/api/v1/auth/session');if(!session){$('session').textContent='Sign-in required';$('callsign').innerHTML='<a href="/account">Continue to account</a>';return}$('session').textContent=session.account_type==='registered'?'Registered account':'Guest profile';const profile=await auth('/api/v1/me/profile');$('callsign').textContent=profile?.identity?.callsign||'Not chosen'}
paint();
</script>
</body></html>"""


@router.get("/", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    return HTMLResponse(_DASHBOARD)
