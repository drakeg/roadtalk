from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.web import web_home

router = APIRouter(include_in_schema=False)


@router.get("/ops", response_class=HTMLResponse)
async def operations_dashboard() -> HTMLResponse:
    return await web_home()


@router.get("/", response_class=HTMLResponse)
async def radio_console() -> HTMLResponse:
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>RoadTalk | Web Radio</title>
  <script src="https://cdn.jsdelivr.net/npm/livekit-client@2.21.0/dist/livekit-client.umd.min.js"></script>
  <style>
    :root{color-scheme:dark;--bg:#07141b;--panel:#10232e;--panel2:#0b1c25;--text:#f2f7f9;--muted:#8fa7b2;--accent:#f2b84b;--green:#70da96;--red:#ff7979;--line:rgba(255,255,255,.1)}
    *{box-sizing:border-box} body{margin:0;background:radial-gradient(circle at 20% 0,rgba(242,184,75,.12),transparent 35rem),var(--bg);color:var(--text);font-family:Inter,system-ui,sans-serif;min-height:100vh}
    header{border-bottom:1px solid var(--line);background:rgba(7,20,27,.86);backdrop-filter:blur(14px);position:sticky;top:0;z-index:5}.wrap{width:min(1180px,calc(100% - 28px));margin:auto}nav{height:68px;display:flex;align-items:center;justify-content:space-between;gap:16px}.brand{display:flex;align-items:center;gap:12px;font-weight:850}.mark{width:42px;height:42px;border-radius:14px;background:var(--accent);color:#172028;display:grid;place-items:center;font-weight:950}.navlinks{display:flex;gap:8px;flex-wrap:wrap}a,button,select{font:inherit}a.button,.small-button{border:1px solid var(--line);background:rgba(255,255,255,.04);color:var(--text);text-decoration:none;padding:9px 12px;border-radius:10px;cursor:pointer}
    main{padding:34px 0 64px}.hero{display:flex;align-items:end;justify-content:space-between;gap:20px;margin-bottom:20px}.eyebrow{color:var(--accent);font-size:11px;font-weight:900;letter-spacing:.16em;text-transform:uppercase}h1{font-size:clamp(32px,5vw,52px);letter-spacing:-.04em;margin:7px 0}.subtitle{color:var(--muted);margin:0;max-width:700px}.status{display:flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:999px;padding:9px 12px;color:var(--muted)}.dot{width:9px;height:9px;border-radius:50%;background:var(--accent)}.dot.ok{background:var(--green)}.dot.bad{background:var(--red)}
    .grid{display:grid;grid-template-columns:1.3fr .7fr;gap:16px}.card{border:1px solid var(--line);background:linear-gradient(180deg,rgba(16,35,46,.96),rgba(11,28,37,.94));border-radius:20px;box-shadow:0 22px 70px rgba(0,0,0,.2)}.radio{padding:24px;text-align:center}.channel-row{display:flex;gap:10px;align-items:center;justify-content:center;margin:10px 0 28px}.channel-row select{min-width:220px;background:#081820;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:10px 12px}.ptt{width:min(310px,75vw);aspect-ratio:1;border-radius:50%;border:10px solid rgba(242,184,75,.15);background:radial-gradient(circle at 35% 28%,#ffd77c,#e7a934 65%,#b57914);color:#172028;font-size:29px;font-weight:950;letter-spacing:.05em;cursor:pointer;box-shadow:0 20px 55px rgba(242,184,75,.22),inset 0 -12px 28px rgba(0,0,0,.18);touch-action:none;user-select:none}.ptt:active,.ptt.tx{transform:scale(.97);box-shadow:0 5px 25px rgba(242,184,75,.16),inset 0 8px 26px rgba(0,0,0,.2)}.ptt[disabled]{filter:grayscale(.75);opacity:.52;cursor:not-allowed}.hint{color:var(--muted);font-size:13px;margin-top:18px}.meter{height:8px;background:#071017;border-radius:99px;overflow:hidden;margin:20px auto 4px;max-width:380px}.meter>span{display:block;height:100%;width:0;background:var(--green);transition:width .08s linear}
    .side{display:grid;gap:16px}.panel{padding:20px}.panel h2{margin:0 0 15px;font-size:16px}.metric{display:flex;justify-content:space-between;padding:11px 0;border-bottom:1px solid var(--line);gap:20px}.metric:last-child{border-bottom:0}.key{color:var(--muted)}.value{font-weight:800;text-align:right}.start{width:100%;border:0;background:var(--accent);color:#172028;font-weight:900;padding:13px;border-radius:11px;cursor:pointer}.start.secondary{background:rgba(255,255,255,.06);color:var(--text);border:1px solid var(--line)}.notice{font-size:12px;color:var(--muted);line-height:1.5;margin-top:12px}.listeners{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.listener{border:1px solid var(--line);border-radius:12px;padding:14px 8px;text-align:center;background:rgba(255,255,255,.025)}.listener strong{display:block;font-size:23px;margin-top:4px}.error{color:var(--red)}.good{color:var(--green)}#audio-bin{display:none}
    @media(max-width:850px){.grid{grid-template-columns:1fr}.hero{align-items:flex-start;flex-direction:column}}@media(max-width:560px){.listeners{grid-template-columns:1fr}.channel-row{flex-direction:column}.channel-row select{width:100%}nav{height:auto;padding:12px 0;align-items:flex-start;flex-direction:column}}
  </style>
</head>
<body>
<header><div class="wrap"><nav><div class="brand"><div class="mark">RT</div><div>RoadTalk <span style="color:var(--muted);font-weight:600">Web Radio</span></div></div><div class="navlinks"><a class="button" href="/ops">Operations</a><a class="button" href="/docs">API</a></div></nav></div></header>
<main class="wrap">
  <section class="hero"><div><div class="eyebrow">Internet CB radio</div><h1>Talk to the road around you.</h1><p class="subtitle">Use your computer microphone and speakers to listen and push-to-talk with nearby RoadTalk users on your selected channel.</p></div><div class="status"><span id="state-dot" class="dot"></span><span id="state-text">Not connected</span></div></section>
  <section class="grid">
    <article class="card radio">
      <div class="channel-row"><label for="channel">Channel</label><select id="channel" disabled><option>General</option></select></div>
      <button id="ptt" class="ptt" disabled>HOLD TO<br>TALK</button>
      <div class="meter"><span id="meter-bar"></span></div>
      <div id="ptt-state" class="hint">Start RoadTalk to enable the radio.</div>
    </article>
    <aside class="side">
      <article class="card panel"><h2>Radio session</h2><button id="start" class="start">Start RoadTalk</button><button id="stop" class="start secondary" style="display:none;margin-top:8px">Disconnect</button><div id="message" class="notice">Your browser will request location and microphone access. RoadTalk uses current location for proximity eligibility; it does not display your exact coordinates here.</div></article>
      <article class="card panel"><h2>Nearby</h2><div class="listeners"><div class="listener"><span class="key">Area</span><strong id="nearby">—</strong></div><div class="listener"><span class="key">Audio</span><strong id="audio">Off</strong></div><div class="listener"><span class="key">Mic</span><strong id="mic">Off</strong></div></div></article>
      <article class="card panel"><h2>Connection</h2><div class="metric"><span class="key">API</span><span id="api-status" class="value">Checking</span></div><div class="metric"><span class="key">Media</span><span id="media-status" class="value">Checking</span></div><div class="metric"><span class="key">Selected channel</span><span id="selected-channel" class="value">General</span></div></article>
    </aside>
  </section>
</main>
<div id="audio-bin"></div>
<script>
const LK=window.LivekitClient; const state={access:null,refresh:null,config:null,room:null,receive:null,transmit:null,seq:0,watch:null,tx:false};
const $=id=>document.getElementById(id); const headers=()=>state.access?{Authorization:`Bearer ${state.access}`}:{ };
function msg(text,bad=false){$('message').textContent=text;$('message').className='notice '+(bad?'error':'');}
function status(text,kind=''){$('state-text').textContent=text;$('state-dot').className='dot '+kind;}
function key(){return crypto.randomUUID().replaceAll('-','')+crypto.randomUUID().replaceAll('-','');}
async function raw(path,opts={}){return fetch(path,{...opts,headers:{'Content-Type':'application/json',...(opts.headers||{}),...headers()}});}
async function refresh(){if(!state.refresh)return false;const r=await fetch('/api/v1/auth/refresh',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({refresh_token:state.refresh})});if(!r.ok)return false;const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh);return true;}
async function api(path,opts={}){let r=await raw(path,opts);if(r.status===401&&await refresh())r=await raw(path,opts);if(!r.ok){let detail=`HTTP ${r.status}`;try{const b=await r.json();detail=b.detail?.detail||b.detail||b.title||detail}catch{}throw new Error(typeof detail==='string'?detail:JSON.stringify(detail));}return r.status===204?null:r.json();}
async function ensureSession(){state.access=localStorage.getItem('rt_access');state.refresh=localStorage.getItem('rt_refresh');if(state.access){try{await api('/api/v1/auth/session');return}catch{}}const install=localStorage.getItem('rt_install')||`web-${crypto.randomUUID()}`;localStorage.setItem('rt_install',install);const r=await fetch('/api/v1/auth/anonymous',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({installation_id:install,platform:'web'})});if(!r.ok)throw new Error('Unable to create browser session.');const b=await r.json();state.access=b.access_token;state.refresh=b.refresh_token;localStorage.setItem('rt_access',state.access);localStorage.setItem('rt_refresh',state.refresh);}
async function getPosition(){return new Promise((resolve,reject)=>navigator.geolocation.getCurrentPosition(resolve,reject,{enableHighAccuracy:true,maximumAge:5000,timeout:15000}));}
async function updateLocation(){const p=await getPosition();if(state.seq===0){await api('/api/v1/me/location-consent',{method:'PUT',body:JSON.stringify({policy_version:state.config.location_policy_version,disclosure_version:state.config.location_disclosure_version})});}state.seq++;await api('/api/v1/me/location',{method:'PUT',body:JSON.stringify({observed_at:new Date(p.timestamp).toISOString(),latitude:p.coords.latitude,longitude:p.coords.longitude,horizontal_accuracy_m:p.coords.accuracy,heading_deg:Number.isFinite(p.coords.heading)?p.coords.heading:null,speed_mps:Number.isFinite(p.coords.speed)?Math.max(0,p.coords.speed):null,client_sequence:state.seq,consent_policy_version:state.config.location_policy_version})});}
async function loadChannels(){const b=await api('/api/v1/channels');const sel=$('channel');sel.innerHTML='';for(const c of b.items){const o=document.createElement('option');o.value=c.id;o.textContent=c.display_label;o.selected=c.selected;sel.appendChild(o);if(c.selected)$('selected-channel').textContent=c.display_label;}sel.disabled=false;}
async function connectMedia(){state.receive=await api('/api/v1/ptt/grants',{method:'POST',headers:{'Idempotency-Key':key()},body:JSON.stringify({mode:'receive'})});state.room=new LK.Room();state.room.on(LK.RoomEvent.TrackSubscribed,(track)=>{if(track.kind===LK.Track.Kind.Audio){const el=track.attach();el.autoplay=true;$('audio-bin').appendChild(el);$('audio').textContent='On';}});state.room.on(LK.RoomEvent.TrackUnsubscribed,(track)=>{track.detach().forEach(el=>el.remove());});state.room.on(LK.RoomEvent.Disconnected,()=>{$('audio').textContent='Off';});await state.room.connect(state.receive.server_url,state.receive.participant_token,{autoSubscribe:false});await state.room.startAudio().catch(()=>{});$('audio').textContent='On';}
async function nearby(){try{const b=await api('/api/v1/nearby/summary');$('nearby').textContent=b.bucket}catch{$('nearby').textContent='—'}}
async function start(){try{$('start').disabled=true;status('Starting…');state.config=await (await fetch('/api/v1/system/client-config')).json();$('api-status').textContent='Online';$('media-status').textContent=state.config.media_provider_enabled?'Enabled':'Disabled';if(!state.config.media_provider_enabled)throw new Error('Voice media is disabled. Enable the local LiveKit voice profile in .env and Docker Compose.');await ensureSession();await updateLocation();state.watch=setInterval(()=>updateLocation().catch(()=>{}),30000);await loadChannels();await connectMedia();await nearby();setInterval(nearby,10000);$('ptt').disabled=false;$('stop').style.display='block';$('start').style.display='none';status('Listening','ok');msg('RoadTalk is listening. Hold the PTT button while you speak.');}catch(e){status('Unable to connect','bad');msg(e.message||String(e),true);$('start').disabled=false;}}
async function beginTx(){if(state.tx||!state.room||!state.receive)return;state.tx=true;try{$('ptt').classList.add('tx');$('ptt-state').textContent='Transmitting…';status('Transmitting','ok');state.transmit=await api(`/api/v1/ptt/grants/${state.receive.grant_id}/transmit`,{method:'POST',headers:{'Idempotency-Key':key()},body:'{}'});const pub=await state.room.localParticipant.setMicrophoneEnabled(true,{echoCancellation:true,noiseSuppression:true,autoGainControl:true});$('mic').textContent='Live';const sid=pub?.trackSid||pub?.track?.sid;if(!sid)throw new Error('Microphone track did not publish.');await api(`/api/v1/ptt/grants/${state.transmit.grant_id}/publication`,{method:'POST',body:JSON.stringify({track_ref:sid})});}catch(e){msg(e.message||String(e),true);await endTx();}}
async function endTx(){if(!state.tx)return;state.tx=false;try{if(state.room)await state.room.localParticipant.setMicrophoneEnabled(false);$('mic').textContent='Off';if(state.transmit){await api(`/api/v1/ptt/grants/${state.transmit.grant_id}`,{method:'DELETE',headers:{'Idempotency-Key':key()}}).catch(()=>{});state.transmit=null;}}finally{$('ptt').classList.remove('tx');$('ptt-state').textContent='Hold the button while speaking.';status('Listening','ok');}}
async function stop(){await endTx();if(state.watch)clearInterval(state.watch);state.watch=null;if(state.room){state.room.disconnect();state.room=null;}if(state.receive){await api(`/api/v1/ptt/grants/${state.receive.grant_id}`,{method:'DELETE',headers:{'Idempotency-Key':key()}}).catch(()=>{});state.receive=null;}$('ptt').disabled=true;$('channel').disabled=true;$('audio').textContent='Off';$('mic').textContent='Off';$('start').style.display='block';$('start').disabled=false;$('stop').style.display='none';status('Disconnected');msg('Disconnected from RoadTalk.');}
$('channel').addEventListener('change',async e=>{try{await api(`/api/v1/channels/${e.target.value}/select`,{method:'POST'});$('selected-channel').textContent=e.target.options[e.target.selectedIndex].text;await stop();await start();}catch(err){msg(err.message||String(err),true)}});
$('ptt').addEventListener('pointerdown',e=>{e.preventDefault();beginTx()});['pointerup','pointercancel','pointerleave'].forEach(ev=>$('ptt').addEventListener(ev,e=>{e.preventDefault();endTx()}));$('start').addEventListener('click',start);$('stop').addEventListener('click',stop);fetch('/health/ready').then(r=>{$('api-status').textContent=r.ok?'Online':'Degraded'}).catch(()=>{$('api-status').textContent='Offline'});
</script>
</body>
</html>"""
    )
