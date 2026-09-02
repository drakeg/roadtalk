# ruff: noqa: E501

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.radio import radio_console
from app.web import web_home

router = APIRouter(include_in_schema=False)

_RADIO_HARDENING = r"""
<script id="roadtalk-browser-hardening">
(() => {
  const startButton = document.getElementById('start');
  if (!startButton) return;

  let prefetchedPosition = null;
  const setBadge = (id, text, kind = '') => {
    const element = document.getElementById(id);
    if (!element) return;
    element.textContent = text;
    element.className = 'badge ' + kind;
  };
  const setMessage = (text, bad = false) => {
    const element = document.getElementById('message');
    if (!element) return;
    element.textContent = text;
    element.className = 'notice ' + (bad ? 'error' : '');
  };

  function capabilityError() {
    if (!window.isSecureContext) return 'Browser microphone and location require a secure origin. Use http://127.0.0.1 on this computer, or the RoadTalk HTTPS LAN gateway on another device.';
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== 'function') return 'This browser does not provide microphone access to RoadTalk. Try a current Chrome, Edge, Firefox, or Safari release.';
    if (!navigator.geolocation || typeof navigator.geolocation.getCurrentPosition !== 'function') return 'This browser does not provide location access to RoadTalk.';
    return null;
  }

  function position(options) { return new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, options)); }
  async function resilientPosition() {
    if (prefetchedPosition) { const value = prefetchedPosition; prefetchedPosition = null; return value; }
    try { return await position({ enableHighAccuracy: true, maximumAge: 5000, timeout: 8000 }); }
    catch (error) { if (error && error.code === 1) throw error; return position({ enableHighAccuracy: false, maximumAge: 60000, timeout: 12000 }); }
  }
  async function microphonePreflight() {
    let stream;
    try { stream = await navigator.mediaDevices.getUserMedia({audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }}); setBadge('mic-permission', 'Granted', 'ok'); }
    catch (error) { setBadge('mic-permission', 'Blocked', 'bad'); if (error && (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError')) throw new Error('Microphone permission is blocked. Allow microphone access for this site in your browser settings, then try Start RoadTalk again.'); throw new Error('RoadTalk could not open a microphone on this system. Check that a microphone is connected, enabled, and not exclusively in use by another application.'); }
    finally { if (stream) stream.getTracks().forEach((track) => track.stop()); }
  }
  async function locationPreflight() {
    try { prefetchedPosition = await resilientPosition(); setBadge('location-permission', 'Granted', 'ok'); }
    catch (error) { setBadge('location-permission', 'Blocked', 'bad'); if (error && error.code === 1) throw new Error('Location permission is blocked. Allow location access for this site in your browser settings, then try Start RoadTalk again.'); throw new Error('RoadTalk could not determine your location. Check your operating-system location service and try again.'); }
  }
  async function browserSessionError(response) {
    let detail = `HTTP ${response.status}`; let code = null;
    try { const body = await response.json(); code = body.detail?.code ?? body.code ?? null; detail = body.detail?.detail ?? body.detail ?? body.title ?? detail; } catch {}
    const error = new Error(typeof detail === 'string' ? detail : JSON.stringify(detail)); error.code = code;
    if (code === 'DEVICE_ALREADY_REGISTERED') error.message = 'This browser is already registered, but its saved session could not be recovered.';
    return error;
  }
  function resetBrowserIdentity() { localStorage.removeItem('rt_access'); localStorage.removeItem('rt_refresh'); localStorage.removeItem('rt_install'); localStorage.removeItem('rt_location_seq'); state.access = null; state.refresh = null; state.seq = 0; }
  ensureSession = async function recoverBrowserSession(allowIdentityReset = true) {
    state.access = localStorage.getItem('rt_access'); state.refresh = localStorage.getItem('rt_refresh');
    if (state.access) { try { await api('/api/v1/auth/session'); return; } catch {} }
    if (state.refresh) { try { if (await refresh()) { await api('/api/v1/auth/session'); return; } } catch {} }
    const install = localStorage.getItem('rt_install') || `web-${crypto.randomUUID()}`; localStorage.setItem('rt_install', install);
    const response = await fetch('/api/v1/auth/anonymous', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({installation_id:install,platform:'web'})});
    if (!response.ok) {
      const error = await browserSessionError(response);
      if (error.code === 'DEVICE_ALREADY_REGISTERED' && allowIdentityReset) {
        const startFresh = window.confirm('RoadTalk cannot recover this browser\'s saved guest identity. Press OK to start a new guest identity, or Cancel and use Account to log in to your persistent RoadTalk account.');
        if (startFresh) { resetBrowserIdentity(); return recoverBrowserSession(false); }
        error.message = 'The existing guest identity was preserved. Open Account to log in to your persistent RoadTalk account.';
      }
      throw error;
    }
    const body = await response.json(); state.access = body.access_token; state.refresh = body.refresh_token; localStorage.setItem('rt_access', state.access); localStorage.setItem('rt_refresh', state.refresh);
  };
  getPosition = resilientPosition;
  startButton.addEventListener('click', async (event) => {
    event.preventDefault(); event.stopImmediatePropagation(); const problem = capabilityError();
    if (problem) { setBadge('mic-permission', 'Unavailable', 'bad'); setBadge('location-permission', 'Unavailable', 'bad'); setMessage(problem, true); return; }
    startButton.disabled = true; setMessage('Checking microphone and location permissions…');
    try { await microphonePreflight(); await locationPreflight(); await start(); }
    catch (error) { setMessage(error && error.message ? error.message : String(error), true); startButton.disabled = false; }
  }, { capture: true });
  const initialProblem = capabilityError();
  if (initialProblem) { setBadge('mic-permission', 'Unavailable', 'bad'); setBadge('location-permission', 'Unavailable', 'bad'); setMessage(initialProblem, true); }
  else setMessage('Ready to request microphone and foreground location when you press Start RoadTalk.');
})();
</script>
"""

_ACCOUNT_PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RoadTalk | Account</title>
<style>:root{color-scheme:dark;--bg:#07141b;--panel:#10232e;--text:#f2f7f9;--muted:#8fa7b2;--accent:#f2b84b;--green:#70da96;--red:#ff7979;--line:rgba(255,255,255,.1)}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif}.wrap{width:min(780px,calc(100% - 28px));margin:auto}header{border-bottom:1px solid var(--line);padding:18px 0}.nav{display:flex;justify-content:space-between;align-items:center;gap:12px}.links{display:flex;gap:8px;flex-wrap:wrap}a,button,input{font:inherit}a,button{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:rgba(255,255,255,.04);color:var(--text);text-decoration:none;cursor:pointer}button.primary{background:var(--accent);color:#172028;font-weight:900;border:0}main{padding:36px 0}.card{border:1px solid var(--line);background:var(--panel);border-radius:18px;padding:22px;margin-bottom:16px}h1{margin-top:0}.muted{color:var(--muted)}.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}label{display:grid;gap:6px;color:var(--muted)}input{width:100%;background:#081820;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:11px}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.good{color:var(--green)}.bad{color:var(--red)}@media(max-width:620px){.grid{grid-template-columns:1fr}}</style></head>
<body><header><div class="wrap nav"><strong>RoadTalk Account</strong><div class="links"><a href="/">Web Radio</a><a href="/notifications">Notifications</a><a href="/map">Map</a><a href="/audience">Audience</a></div></div></header><main class="wrap">
<div class="card"><h1>Your RoadTalk account</h1><p class="muted">Your private username and password identify your account. Your public call sign belongs to that account profile and comes back every time you log in.</p><p id="status">Checking saved session…</p><p>Call sign: <strong id="callsign">—</strong></p></div>
<div class="card"><h2>Log in or create your account</h2><div class="grid"><label>Username<input id="username" autocomplete="username" minlength="3" maxlength="64"></label><label>Password<input id="password" type="password" autocomplete="current-password" minlength="12" maxlength="256"></label></div><div class="actions"><button id="login" class="primary">Log in</button><button id="register">Create / protect this account</button><button id="logout">Log out</button></div><p id="message" class="muted">If this browser currently has a guest profile and call sign, Create / protect this account upgrades that same account instead of creating another one.</p></div>
</main><script>
const $=id=>document.getElementById(id);let access=localStorage.getItem('rt_access'),refreshToken=localStorage.getItem('rt_refresh');
function install(){let value=localStorage.getItem('rt_install');if(!value){value=`web-${crypto.randomUUID()}`;localStorage.setItem('rt_install',value)}return value}
function freshInstall(){const value=`web-${crypto.randomUUID()}`;localStorage.setItem('rt_install',value);return value}
function store(body){access=body.access_token;refreshToken=body.refresh_token;localStorage.setItem('rt_access',access);localStorage.setItem('rt_refresh',refreshToken)}
async function problem(response){let body={};try{body=await response.json()}catch{}const error=new Error(body.detail?.detail||body.detail||`HTTP ${response.status}`);error.code=body.detail?.code||body.code;return error}
async function session(){if(!access)return null;let r=await fetch('/api/v1/auth/session',{headers:{Authorization:`Bearer ${access}`}});if(r.status===401&&refreshToken){const rr=await fetch('/api/v1/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:refreshToken})});if(rr.ok){store(await rr.json());r=await fetch('/api/v1/auth/session',{headers:{Authorization:`Bearer ${access}`}})}}return r.ok?r.json():null}
async function profile(){if(!access)return null;const r=await fetch('/api/v1/me/profile',{headers:{Authorization:`Bearer ${access}`}});return r.ok?r.json():null}
async function paint(){const s=await session();$('status').textContent=s?`Signed in: ${s.account_type} account`:'Not signed in';$('status').className=s?'good':'muted';const p=s?await profile():null;$('callsign').textContent=p?.identity?.callsign||'Not set';return s}
async function authenticate(path,retry=true){const payload={username:$('username').value.trim(),password:$('password').value,installation_id:install(),platform:'web'};let r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok){const e=await problem(r);if(e.code==='DEVICE_ALREADY_REGISTERED'&&retry){payload.installation_id=freshInstall();r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!r.ok)throw await problem(r)}else throw e}store(await r.json());await paint();location.href='/'}
$('login').onclick=async()=>{try{$('message').textContent='Logging in…';await authenticate('/api/v1/auth/login')}catch(e){$('message').textContent=e.message;$('message').className='bad'}};
$('register').onclick=async()=>{try{$('message').textContent='Creating account…';const s=await session();if(s&&s.account_type==='anonymous'){const r=await fetch('/api/v1/auth/promote',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${access}`},body:JSON.stringify({username:$('username').value.trim(),password:$('password').value})});if(!r.ok)throw await problem(r);await paint();location.href='/';return}if(s&&s.account_type==='registered')throw new Error('This RoadTalk account is already registered.');await authenticate('/api/v1/auth/register')}catch(e){$('message').textContent=e.message;$('message').className='bad'}};
$('logout').onclick=async()=>{try{if(access)await fetch('/api/v1/auth/logout',{method:'POST',headers:{Authorization:`Bearer ${access}`}})}finally{localStorage.removeItem('rt_access');localStorage.removeItem('rt_refresh');access=null;refreshToken=null;await paint();$('message').textContent='Logged out. Your account and call sign are unchanged.'}};
paint();
</script></body></html>"""


@router.get("/account", response_class=HTMLResponse)
async def account_console() -> HTMLResponse:
    return HTMLResponse(_ACCOUNT_PAGE)


@router.get("/", response_class=HTMLResponse)
async def hardened_radio_console() -> HTMLResponse:
    response = await radio_console()
    html = bytes(response.body).decode("utf-8")
    html = html.replace("<head>", "<head><script>if(!localStorage.getItem('rt_access')&&!localStorage.getItem('rt_refresh'))location.replace('/account');</script>", 1)
    html = html.replace('<div class="navlinks"><a class="button" href="/ops">Operations</a>', '<div class="navlinks"><a class="button" href="/account">Account</a><a class="button" href="/notifications">Notifications</a><a class="button" href="/map">Map</a><a class="button" href="/audience">Audience</a><a class="button" href="/ops">Operations</a>', 1)
    html = html.replace("</body>", f"{_RADIO_HARDENING}</body>", 1)
    return HTMLResponse(html)


@router.get("/ops", response_class=HTMLResponse)
async def hardened_operations_dashboard() -> HTMLResponse:
    response = await web_home()
    html = bytes(response.body).decode("utf-8")
    html = html.replace('<div class="navlinks"><a class="button" href="/docs">Swagger</a>', '<div class="navlinks"><a class="button" href="/">Web Radio</a><a class="button" href="/account">Account</a><a class="button" href="/notifications">Notifications</a><a class="button" href="/map">Map Awareness</a><a class="button" href="/audience">Audience Mode</a><a class="button" href="/docs">Swagger</a>', 1)
    return HTMLResponse(html)
