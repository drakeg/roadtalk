from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(include_in_schema=False)


@router.get("/profile", response_class=HTMLResponse)
async def profile_page() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoadTalk | Profile</title>
  <style>
    :root{color-scheme:dark;--bg:#07141b;--panel:#10232e;--text:#f2f7f9;--muted:#8fa7b2;--accent:#f2b84b;--green:#70da96;--red:#ff7979;--line:rgba(255,255,255,.1)}
    *{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 20% 0,rgba(242,184,75,.12),transparent 35rem),var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;min-height:100vh}.wrap{width:min(980px,calc(100% - 28px));margin:auto}header{border-bottom:1px solid var(--line);background:rgba(7,20,27,.86);backdrop-filter:blur(14px);position:sticky;top:0}nav{min-height:68px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{font-weight:850}.navlinks{display:flex;gap:8px;flex-wrap:wrap}a,button,input{font:inherit}.button,button{border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--text);text-decoration:none;padding:10px 13px;border-radius:10px;cursor:pointer}.primary{background:var(--accent);color:#172028;border:0;font-weight:900}main{padding:34px 0 64px}h1{font-size:clamp(34px,5vw,52px);letter-spacing:-.04em;margin:5px 0}.subtitle,.notice{color:var(--muted)}.card{margin-top:22px;border:1px solid var(--line);background:linear-gradient(180deg,rgba(16,35,46,.96),rgba(11,28,37,.94));border-radius:20px;padding:22px}.row{display:grid;grid-template-columns:1fr auto;gap:10px}input{width:100%;background:#081820;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:11px 12px}.avatars{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.avatar{display:flex;align-items:center;gap:12px;text-align:left;padding:12px;border-radius:14px}.avatar.selected{outline:2px solid var(--accent);background:rgba(242,184,75,.08)}.glyph{width:48px;height:48px;border-radius:50%;display:grid;place-items:center;font-weight:900;flex:0 0 auto}.avatar small{display:block;color:var(--muted);margin-top:3px}.status{margin-top:14px}.good{color:var(--green)}.bad{color:var(--red)}@media(max-width:700px){.avatars{grid-template-columns:1fr 1fr}}@media(max-width:480px){.avatars{grid-template-columns:1fr}.row{grid-template-columns:1fr}}
  </style>
</head>
<body>
<header><div class="wrap"><nav><div class="brand">RoadTalk <span style="color:var(--muted);font-weight:600">Profile</span></div><div class="navlinks"><a class="button" href="/">Radio</a><a class="button" href="/ops">Operations</a></div></nav></div></header>
<main class="wrap">
  <div class="eyebrow" style="color:var(--accent);font-size:11px;font-weight:900;letter-spacing:.16em;text-transform:uppercase">Your identity</div>
  <h1>Choose how you appear on RoadTalk.</h1>
  <p class="subtitle">Set a call sign and avatar. Both are required before your profile is considered complete.</p>
  <section class="card">
    <h2>Call sign</h2>
    <div class="row"><input id="callsign" maxlength="128" autocomplete="nickname" placeholder="Choose a call sign"><button id="save" class="primary">Save profile</button></div>
    <p class="notice">Your call sign is visible to other RoadTalk users. No email address is required for this local alpha flow.</p>
  </section>
  <section class="card">
    <h2>Avatar</h2>
    <div id="avatars" class="avatars"></div>
    <p class="notice">Only active avatars can be selected. Your current selection is highlighted.</p>
  </section>
  <p id="status" class="status notice">Loading your profile…</p>
</main>
<script>
const state={access:null,refresh:null,profile:null,avatars:[],selectedAvatar:null};
const $=id=>document.getElementById(id);
const headers=()=>state.access?{Authorization:`Bearer ${state.access}`}:{ };
function show(text,bad=false){$('status').textContent=text;$('status').className='status '+(bad?'bad':'good');}
async function raw(path,opts={}){return fetch(path,{...opts,headers:{'Content-Type':'application/json',...(opts.headers||{}),...headers()}});}
async function refresh(){if(!state.refresh)return false;const r=await fetch('/api/v1/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:state.refresh})});if(!r.ok)return false;const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh);return true;}
async function api(path,opts={}){let r=await raw(path,opts);if(r.status===401&&await refresh())r=await raw(path,opts);if(!r.ok){let detail=`HTTP ${r.status}`;try{const b=await r.json();detail=b.detail?.detail||b.detail||b.title||detail}catch{}throw new Error(typeof detail==='string'?detail:JSON.stringify(detail));}return r.status===204?null:r.json();}
async function ensureSession(){state.access=localStorage.getItem('rt_access');state.refresh=localStorage.getItem('rt_refresh');if(state.access){try{await api('/api/v1/auth/session');return}catch{}}const install=localStorage.getItem('rt_install')||`web-${crypto.randomUUID()}`;localStorage.setItem('rt_install',install);const r=await fetch('/api/v1/auth/anonymous',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({installation_id:install,platform:'web'})});if(!r.ok)throw new Error('Unable to create browser session.');const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh);}
function renderAvatars(){const root=$('avatars');root.innerHTML='';for(const avatar of state.avatars.filter(a=>a.selectable)){const button=document.createElement('button');button.type='button';button.className='avatar'+(avatar.id===state.selectedAvatar?' selected':'');button.dataset.avatarId=avatar.id;button.innerHTML=`<span class="glyph" style="background:${avatar.background_color};color:${avatar.foreground_color}">${avatar.glyph}</span><span><strong>${avatar.label}</strong><small>${avatar.id}</small></span>`;button.addEventListener('click',()=>{state.selectedAvatar=avatar.id;renderAvatars();});root.appendChild(button);}}
async function load(){await ensureSession();const [profile,catalog]=await Promise.all([api('/api/v1/me/profile'),api('/api/v1/avatars')]);state.profile=profile;state.avatars=catalog.avatars;state.selectedAvatar=profile.identity.avatar_id||state.avatars.find(a=>a.selectable)?.id||null;$('callsign').value=profile.identity.callsign||'';renderAvatars();show(profile.setup_completed?'Profile complete. You can return to the radio.':'Choose a call sign and avatar, then save your profile.');}
async function save(){try{$('save').disabled=true;const callsign=$('callsign').value.trim();if(!callsign)throw new Error('Enter a call sign.');if(!state.selectedAvatar)throw new Error('Choose an avatar.');const check=await api(`/api/v1/callsigns/availability?callsign=${encodeURIComponent(callsign)}`);if(!check.available&&callsign!==state.profile.identity.callsign)throw new Error(`That call sign is ${check.reason}.`);state.profile=await api('/api/v1/me/profile',{method:'PATCH',body:JSON.stringify({version:state.profile.version,callsign,avatar_id:state.selectedAvatar})});show(state.profile.setup_completed?'Profile saved. You are ready to use RoadTalk.':'Profile saved, but setup is still incomplete.',!state.profile.setup_completed);}catch(e){show(e.message||String(e),true);}finally{$('save').disabled=false;}}
$('save').addEventListener('click',save);$('callsign').addEventListener('keydown',e=>{if(e.key==='Enter')save()});load().catch(e=>show(e.message||String(e),true));
</script>
</body>
</html>"""
    )
