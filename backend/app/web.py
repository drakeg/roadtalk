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
  <title>RoadTalk</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #07141b;
      --panel: #10232e;
      --text: #eff8fb;
      --muted: #a7bdc7;
      --accent: #f2b84b;
      --ok: #69d391;
      --bad: #ff7b7b;
      --line: rgba(255,255,255,.10);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background:
        radial-gradient(circle at 80% 10%, rgba(242,184,75,.16), transparent 28rem),
        linear-gradient(145deg, #061118, var(--bg) 45%, #0a1c25);
      color: var(--text);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .wrap { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }
    header { padding: 28px 0 10px; }
    nav { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    .brand { display: flex; align-items: center; gap: 12px; font-weight: 800; letter-spacing: .02em; }
    .mark {
      width: 42px; height: 42px; border-radius: 14px; display: grid; place-items: center;
      background: var(--accent); color: #182028; font-size: 20px; box-shadow: 0 10px 32px rgba(242,184,75,.18);
    }
    .navlinks { display: flex; flex-wrap: wrap; gap: 10px; }
    a.button {
      color: var(--text); text-decoration: none; border: 1px solid var(--line); background: rgba(255,255,255,.04);
      padding: 10px 14px; border-radius: 10px; font-weight: 650;
    }
    a.button.primary { background: var(--accent); color: #172028; border-color: transparent; }
    main { padding: 58px 0 72px; }
    .hero { display: grid; grid-template-columns: 1.25fr .75fr; gap: 24px; align-items: stretch; }
    .hero-card, .status-card, .feature {
      border: 1px solid var(--line); background: rgba(16,35,46,.82); backdrop-filter: blur(12px);
      border-radius: 22px; box-shadow: 0 22px 70px rgba(0,0,0,.22);
    }
    .hero-card { padding: clamp(28px, 5vw, 54px); }
    .eyebrow { color: var(--accent); text-transform: uppercase; letter-spacing: .16em; font-size: 12px; font-weight: 800; }
    h1 { font-size: clamp(42px, 7vw, 76px); line-height: .98; margin: 14px 0 18px; letter-spacing: -.045em; }
    .lead { color: var(--muted); font-size: clamp(18px, 2.2vw, 23px); line-height: 1.5; max-width: 720px; }
    .actions { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 28px; }
    .status-card { padding: 26px; display: flex; flex-direction: column; justify-content: space-between; }
    .status-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
    .pill { display: inline-flex; align-items: center; gap: 8px; border-radius: 999px; padding: 8px 11px; background: rgba(255,255,255,.055); color: var(--muted); font-size: 13px; }
    .dot { width: 9px; height: 9px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 0 4px rgba(242,184,75,.12); }
    .dot.ok { background: var(--ok); box-shadow: 0 0 0 4px rgba(105,211,145,.12); }
    .dot.bad { background: var(--bad); box-shadow: 0 0 0 4px rgba(255,123,123,.12); }
    .kv { margin-top: 28px; display: grid; gap: 12px; }
    .kv-row { padding: 14px 0; border-bottom: 1px solid var(--line); display: flex; justify-content: space-between; gap: 18px; }
    .kv-row:last-child { border-bottom: 0; }
    .label { color: var(--muted); }
    .value { font-weight: 750; text-align: right; }
    .section-title { margin: 48px 0 16px; font-size: 24px; }
    .features { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    .feature { padding: 24px; }
    .feature h3 { margin: 10px 0 8px; }
    .feature p { color: var(--muted); line-height: 1.55; margin: 0; }
    .icon { font-size: 24px; }
    footer { color: var(--muted); border-top: 1px solid var(--line); padding: 24px 0 38px; font-size: 13px; }
    @media (max-width: 800px) {
      .hero { grid-template-columns: 1fr; }
      .features { grid-template-columns: 1fr; }
      nav { align-items: flex-start; flex-direction: column; }
    }
  </style>
</head>
<body>
  <header class="wrap">
    <nav>
      <div class="brand"><div class="mark">RT</div><span>RoadTalk</span></div>
      <div class="navlinks">
        <a class="button" href="/docs">API Docs</a>
        <a class="button" href="/redoc">ReDoc</a>
        <a class="button primary" href="/api/v1/system/version">API Version</a>
      </div>
    </nav>
  </header>

  <main class="wrap">
    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">Internet CB for modern travelers</div>
        <h1>Talk to the road around you.</h1>
        <p class="lead">RoadTalk is a location-aware, voice-first communication platform built for travelers, RVers, convoys, and communities on the move.</p>
        <div class="actions">
          <a class="button primary" href="/docs">Explore the API</a>
          <a class="button" href="/health/ready">Readiness check</a>
        </div>
      </div>

      <aside class="status-card">
        <div>
          <div class="status-head">
            <strong>Local service</strong>
            <span class="pill"><span id="status-dot" class="dot"></span><span id="status-text">Checking…</span></span>
          </div>
          <div class="kv">
            <div class="kv-row"><span class="label">Environment</span><span class="value" id="environment">—</span></div>
            <div class="kv-row"><span class="label">Version</span><span class="value" id="version">—</span></div>
            <div class="kv-row"><span class="label">API</span><span class="value">/api/v1</span></div>
          </div>
        </div>
        <p class="label">This is the first RoadTalk browser shell. Account, channel, map, and PTT controls will build on this surface.</p>
      </aside>
    </section>

    <h2 class="section-title">Platform foundation</h2>
    <section class="features">
      <article class="feature"><div class="icon">📻</div><h3>Channels</h3><p>General, RV, and invite-only private channels with server-authoritative membership and switching.</p></article>
      <article class="feature"><div class="icon">📍</div><h3>Nearby awareness</h3><p>Privacy-conscious proximity logic designed to connect relevant travelers without exposing exact coordinates.</p></article>
      <article class="feature"><div class="icon">🎙️</div><h3>Push-to-talk</h3><p>A voice-first architecture designed around deliberate PTT behavior, controlled media grants, and safe channel isolation.</p></article>
    </section>
  </main>

  <footer><div class="wrap">RoadTalk local alpha · Browser interface foundation</div></footer>

  <script>
    async function loadStatus() {
      const dot = document.getElementById('status-dot');
      const text = document.getElementById('status-text');
      try {
        const [healthResponse, versionResponse] = await Promise.all([
          fetch('/health/ready', {cache: 'no-store'}),
          fetch('/api/v1/system/version', {cache: 'no-store'})
        ]);
        if (!healthResponse.ok || !versionResponse.ok) throw new Error('service unavailable');
        const health = await healthResponse.json();
        const version = await versionResponse.json();
        document.getElementById('environment').textContent = version.environment;
        document.getElementById('version').textContent = version.version;
        const ready = health.status === 'ready';
        dot.className = 'dot ' + (ready ? 'ok' : 'bad');
        text.textContent = ready ? 'Ready' : 'Not ready';
      } catch (_) {
        dot.className = 'dot bad';
        text.textContent = 'Unavailable';
      }
    }
    loadStatus();
  </script>
</body>
</html>"""
    )
