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
    if (!window.isSecureContext) {
      return 'Browser microphone and location require a secure origin. Use http://127.0.0.1 on this computer, or the RoadTalk HTTPS LAN gateway on another device.';
    }
    if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== 'function') {
      return 'This browser does not provide microphone access to RoadTalk. Try a current Chrome, Edge, Firefox, or Safari release.';
    }
    if (!navigator.geolocation || typeof navigator.geolocation.getCurrentPosition !== 'function') {
      return 'This browser does not provide location access to RoadTalk.';
    }
    return null;
  }

  function position(options) {
    return new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, options);
    });
  }

  async function resilientPosition() {
    if (prefetchedPosition) {
      const value = prefetchedPosition;
      prefetchedPosition = null;
      return value;
    }
    try {
      return await position({ enableHighAccuracy: true, maximumAge: 5000, timeout: 8000 });
    } catch (error) {
      if (error && error.code === 1) throw error;
      return position({ enableHighAccuracy: false, maximumAge: 60000, timeout: 12000 });
    }
  }

  async function microphonePreflight() {
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      setBadge('mic-permission', 'Granted', 'ok');
    } catch (error) {
      setBadge('mic-permission', 'Blocked', 'bad');
      if (error && (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError')) {
        throw new Error('Microphone permission is blocked. Allow microphone access for this site in your browser settings, then try Start RoadTalk again.');
      }
      throw new Error('RoadTalk could not open a microphone on this system. Check that a microphone is connected, enabled, and not exclusively in use by another application.');
    } finally {
      if (stream) stream.getTracks().forEach((track) => track.stop());
    }
  }

  async function locationPreflight() {
    try {
      prefetchedPosition = await resilientPosition();
      setBadge('location-permission', 'Granted', 'ok');
    } catch (error) {
      setBadge('location-permission', 'Blocked', 'bad');
      if (error && error.code === 1) {
        throw new Error('Location permission is blocked. Allow location access for this site in your browser settings, then try Start RoadTalk again.');
      }
      throw new Error('RoadTalk could not determine your location. Check your operating-system location service and try again.');
    }
  }

  // The existing radio code calls getPosition() during startup and refresh. Replace
  // that single brittle high-accuracy request with a bounded high-accuracy attempt
  // followed by a cached/lower-power fallback. Permission denial never falls back.
  getPosition = resilientPosition;

  startButton.addEventListener('click', async (event) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    const problem = capabilityError();
    if (problem) {
      setBadge('mic-permission', 'Unavailable', 'bad');
      setBadge('location-permission', 'Unavailable', 'bad');
      setMessage(problem, true);
      return;
    }

    startButton.disabled = true;
    setMessage('Checking microphone and location permissions…');
    try {
      // Keep both permission prompts directly inside the user's Start gesture.
      await microphonePreflight();
      await locationPreflight();
      await start();
    } catch (error) {
      setMessage(error && error.message ? error.message : String(error), true);
      startButton.disabled = false;
    }
  }, { capture: true });

  const initialProblem = capabilityError();
  if (initialProblem) {
    setBadge('mic-permission', 'Unavailable', 'bad');
    setBadge('location-permission', 'Unavailable', 'bad');
    setMessage(initialProblem, true);
  } else {
    setMessage('Ready to request microphone and foreground location when you press Start RoadTalk.');
  }
})();
</script>
"""


@router.get("/", response_class=HTMLResponse)
async def hardened_radio_console() -> HTMLResponse:
    response = await radio_console()
    html = bytes(response.body).decode("utf-8")
    html = html.replace(
        '<div class="navlinks"><a class="button" href="/ops">Operations</a>',
        '<div class="navlinks"><a class="button" href="/audience">Audience</a><a class="button" href="/ops">Operations</a>',
        1,
    )
    html = html.replace("</body>", f"{_RADIO_HARDENING}</body>", 1)
    return HTMLResponse(html)


@router.get("/ops", response_class=HTMLResponse)
async def hardened_operations_dashboard() -> HTMLResponse:
    response = await web_home()
    html = bytes(response.body).decode("utf-8")
    html = html.replace(
        '<div class="navlinks"><a class="button" href="/docs">Swagger</a>',
        '<div class="navlinks"><a class="button" href="/">Web Radio</a><a class="button" href="/audience">Audience Mode</a><a class="button" href="/docs">Swagger</a>',
        1,
    )
    return HTMLResponse(html)
