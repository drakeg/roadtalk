from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from app.browser_hardening import hardened_radio_console

router = APIRouter(include_in_schema=False)

_DESKTOP_WELCOME_STYLES = r"""
<style id="roadtalk-desktop-welcome-styles">
  .desktop-welcome{display:none}
  @media(min-width:851px){
    .desktop-welcome{display:block;padding:28px 0 38px}
    .desktop-welcome-shell{position:relative;overflow:hidden;border:1px solid var(--line);border-radius:28px;background:linear-gradient(135deg,rgba(16,35,46,.98),rgba(7,20,27,.98));box-shadow:0 30px 90px rgba(0,0,0,.24)}
    .desktop-welcome-shell:before{content:"";position:absolute;inset:-35% auto auto 50%;width:520px;height:520px;border-radius:50%;background:radial-gradient(circle,rgba(242,184,75,.2),rgba(242,184,75,0) 68%);pointer-events:none}
    .desktop-welcome-hero{position:relative;display:grid;grid-template-columns:minmax(0,1.25fr) minmax(320px,.75fr);gap:42px;align-items:center;padding:54px}
    .desktop-welcome-kicker{color:var(--accent);font-size:12px;font-weight:900;letter-spacing:.18em;text-transform:uppercase;margin-bottom:14px}
    .desktop-welcome h1{font-size:clamp(48px,6vw,76px);line-height:.98;letter-spacing:-.055em;margin:0 0 20px;max-width:760px}
    .desktop-welcome-lead{font-size:19px;line-height:1.65;color:var(--muted);max-width:720px;margin:0 0 26px}
    .desktop-welcome-actions{display:flex;gap:12px;flex-wrap:wrap}
    .desktop-welcome-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:46px;border-radius:12px;padding:0 17px;text-decoration:none;font-weight:850;border:1px solid var(--line);color:var(--text);background:rgba(255,255,255,.045)}
    .desktop-welcome-actions a.primary{background:var(--accent);border-color:transparent;color:#172028}
    .desktop-welcome-radio{position:relative;border:1px solid rgba(242,184,75,.22);border-radius:22px;padding:24px;background:rgba(5,16,23,.72);box-shadow:inset 0 1px 0 rgba(255,255,255,.04)}
    .desktop-welcome-radio .radio-label{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);font-weight:800}
    .desktop-welcome-radio .radio-channel{font-size:26px;font-weight:900;margin:9px 0 4px}
    .desktop-welcome-radio .radio-status{display:flex;align-items:center;gap:9px;color:var(--green);font-size:14px;font-weight:750;margin-bottom:22px}
    .desktop-welcome-radio .radio-dot{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 18px rgba(112,218,150,.7)}
    .desktop-welcome-radio .mini-ptt{width:118px;height:118px;border-radius:50%;margin:0 auto;display:grid;place-items:center;text-align:center;background:radial-gradient(circle at 35% 28%,#ffd77c,#e7a934 65%,#b57914);border:7px solid rgba(242,184,75,.14);color:#172028;font-size:16px;line-height:1.15;font-weight:950;letter-spacing:.04em;box-shadow:0 18px 42px rgba(242,184,75,.16)}
    .desktop-welcome-features{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;border-top:1px solid var(--line);background:var(--line)}
    .desktop-welcome-feature{min-height:170px;padding:25px;background:rgba(9,25,34,.96)}
    .desktop-welcome-feature strong{display:block;font-size:17px;margin:9px 0 8px}
    .desktop-welcome-feature p{color:var(--muted);font-size:14px;line-height:1.55;margin:0}
    .desktop-welcome-icon{font-size:23px;line-height:1}
    .desktop-how{display:grid;grid-template-columns:250px 1fr;gap:36px;padding:34px 8px 6px}
    .desktop-how h2{font-size:28px;margin:0 0 8px}.desktop-how>div>p{color:var(--muted);line-height:1.55;margin:0}
    .desktop-steps{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;counter-reset:roadtalk-step}
    .desktop-step{counter-increment:roadtalk-step;border:1px solid var(--line);border-radius:15px;padding:18px;background:rgba(255,255,255,.025)}
    .desktop-step:before{content:counter(roadtalk-step);display:grid;place-items:center;width:30px;height:30px;border-radius:50%;background:rgba(242,184,75,.14);color:var(--accent);font-weight:900;margin-bottom:12px}
    .desktop-step strong{display:block;margin-bottom:6px}.desktop-step span{display:block;color:var(--muted);font-size:13px;line-height:1.45}
    #radio-console{scroll-margin-top:88px}
    #radio-console .ptt{width:230px}
  }
  @media(min-width:851px) and (max-width:1080px){
    .desktop-welcome-hero{grid-template-columns:1fr;padding:42px}.desktop-welcome-radio{display:none}
    .desktop-welcome-features{grid-template-columns:repeat(2,1fr)}
    .desktop-how{grid-template-columns:1fr}.desktop-steps{grid-template-columns:repeat(2,1fr)}
  }
</style>
"""

_DESKTOP_WELCOME = r"""
<section class="desktop-welcome" aria-labelledby="roadtalk-welcome-title">
  <div class="desktop-welcome-shell">
    <div class="desktop-welcome-hero">
      <div>
        <div class="desktop-welcome-kicker">Nearby push-to-talk for the road</div>
        <h1 id="roadtalk-welcome-title">The familiar feel of CB radio, built for connected travelers.</h1>
        <p class="desktop-welcome-lead">RoadTalk helps drivers and travelers hear and talk with nearby RoadTalk users through simple channels, a persistent call sign, foreground location awareness, and push-to-talk audio.</p>
        <div class="desktop-welcome-actions">
          <a class="primary" href="#radio-console">Open the radio</a>
          <a href="/map">See nearby awareness</a>
          <a href="/account">Manage your account</a>
        </div>
      </div>
      <div class="desktop-welcome-radio" aria-hidden="true">
        <div class="radio-label">RoadTalk channel</div>
        <div class="radio-channel">General</div>
        <div class="radio-status"><span class="radio-dot"></span>Ready when you are</div>
        <div class="mini-ptt">HOLD TO<br>TALK</div>
      </div>
    </div>
    <div class="desktop-welcome-features">
      <div class="desktop-welcome-feature"><div class="desktop-welcome-icon">◉</div><strong>Nearby conversations</strong><p>RoadTalk uses your foreground location to determine who is nearby without turning the web app into a background tracker.</p></div>
      <div class="desktop-welcome-feature"><div class="desktop-welcome-icon">⌁</div><strong>Choose a channel</strong><p>Listen on shared channels and use push-to-talk when you want to join the conversation.</p></div>
      <div class="desktop-welcome-feature"><div class="desktop-welcome-icon">RT</div><strong>Your call sign follows you</strong><p>Sign in to your RoadTalk account and your public call sign and profile come back with you.</p></div>
      <div class="desktop-welcome-feature"><div class="desktop-welcome-icon">⌖</div><strong>Awareness, not tracking</strong><p>The map shows privacy-limited nearby awareness rather than exposing another user's precise location or route.</p></div>
    </div>
  </div>
  <div class="desktop-how">
    <div><h2>How it works</h2><p>Getting on RoadTalk should feel more like picking up a radio than configuring an app.</p></div>
    <div class="desktop-steps">
      <div class="desktop-step"><strong>Sign in</strong><span>Your account restores your profile and call sign.</span></div>
      <div class="desktop-step"><strong>Allow access</strong><span>Grant foreground location and microphone permission when you start.</span></div>
      <div class="desktop-step"><strong>Pick a channel</strong><span>Choose where you want to listen and talk.</span></div>
      <div class="desktop-step"><strong>Hold to talk</strong><span>Listen normally; press and hold PTT when you want to speak.</span></div>
    </div>
  </div>
</section>
"""


@router.get("/", response_class=HTMLResponse)
async def desktop_web_radio() -> HTMLResponse:
    response = await hardened_radio_console()
    html = bytes(response.body).decode("utf-8")
    html = html.replace("</head>", f"{_DESKTOP_WELCOME_STYLES}</head>", 1)
    html = html.replace('<main class="wrap">', f'<main class="wrap">{_DESKTOP_WELCOME}', 1)
    html = html.replace('<section class="grid">', '<section id="radio-console" class="grid">', 1)
    return HTMLResponse(html)
