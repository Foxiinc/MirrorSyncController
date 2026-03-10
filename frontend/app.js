const { invoke } = window.__TAURI__.core;

// ── State ──
const state = {
  devices: [],
  selectedSerial: null,
  broadcastMode: false,
  phoneScreens: {},
  refreshTimer: null,
  screenshotTimers: {},
};

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
  bindEvents();
  startPolling();
});

function bindEvents() {
  document.getElementById('btn-refresh').addEventListener('click', refreshDevices);
  document.getElementById('broadcast-checkbox').addEventListener('change', (e) => {
    state.broadcastMode = e.target.checked;
    log(state.broadcastMode ? 'Broadcast mode ON' : 'Broadcast mode OFF');
  });
  document.getElementById('btn-send-text').addEventListener('click', sendText);
  document.getElementById('text-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') sendText();
  });
  document.getElementById('btn-clear-log').addEventListener('click', () => {
    document.getElementById('log-output').innerHTML = '';
  });
  document.getElementById('btn-install-agent').addEventListener('click', installAgent);
  document.getElementById('btn-start-mirror').addEventListener('click', startMirror);
  document.getElementById('btn-stop-mirror').addEventListener('click', stopMirror);

  document.querySelectorAll('.btn-control').forEach((btn) => {
    btn.addEventListener('click', () => {
      const keyCode = parseInt(btn.dataset.key);
      sendKeyCommand(keyCode);
    });
  });
}

function startPolling() {
  refreshDevices();
  state.refreshTimer = setInterval(refreshDevices, 3000);
}

// ── Device Management ──
async function refreshDevices() {
  try {
    const devices = await invoke('list_devices');
    state.devices = devices;
    renderDeviceList(devices);
    updateStatusBar(devices);
    syncPhoneScreens(devices);
  } catch (e) {
    console.error('Failed to list devices:', e);
  }
}

function renderDeviceList(devices) {
  const list = document.getElementById('device-list');
  list.innerHTML = '';

  for (const dev of devices) {
    const card = document.createElement('div');
    card.className = 'device-card' + (dev.serial === state.selectedSerial ? ' selected' : '');
    card.innerHTML = `
      <span class="agent-dot ${dev.agent_connected ? 'connected' : 'disconnected'}"></span>
      <div class="device-info">
        <div class="device-model">${escapeHtml(dev.model || 'Unknown')}</div>
        <div class="device-serial">${escapeHtml(dev.serial)}</div>
      </div>
    `;
    card.addEventListener('click', () => selectDevice(dev.serial));
    list.appendChild(card);
  }
}

function updateStatusBar(devices) {
  const count = devices.length;
  const connected = devices.filter((d) => d.agent_connected).length;
  document.getElementById('device-count').textContent = `${connected}/${count} devices`;

  const dot = document.getElementById('status-indicator');
  dot.className = 'status-dot ' + (connected > 0 ? 'online' : 'offline');
}

function selectDevice(serial) {
  state.selectedSerial = serial;
  renderDeviceList(state.devices);
  activatePhoneTab(serial);
}

// ── Phone Screens ──
function syncPhoneScreens(devices) {
  const currentSerials = new Set(Object.keys(state.phoneScreens));
  const newSerials = new Set(devices.map((d) => d.serial));

  for (const dev of devices) {
    if (!currentSerials.has(dev.serial)) {
      addPhoneScreen(dev);
    }
  }

  for (const serial of currentSerials) {
    if (!newSerials.has(serial)) {
      removePhoneScreen(serial);
    }
  }

  const placeholder = document.getElementById('no-device-placeholder');
  placeholder.style.display = devices.length > 0 ? 'none' : 'flex';

  if (!state.selectedSerial && devices.length > 0) {
    selectDevice(devices[0].serial);
  }
}

function addPhoneScreen(device) {
  const serial = device.serial;
  const shortSerial = serial.slice(-4);

  // Tab
  const tab = document.createElement('div');
  tab.className = 'phone-tab';
  tab.dataset.serial = serial;
  tab.textContent = device.model ? `${device.model}` : `Dev …${shortSerial}`;
  tab.addEventListener('click', () => selectDevice(serial));
  document.getElementById('phone-tabs').appendChild(tab);

  // Screen
  const screen = document.createElement('div');
  screen.className = 'phone-screen';
  screen.dataset.serial = serial;

  const wrapper = document.createElement('div');
  wrapper.className = 'screen-wrapper';

  const canvas = document.createElement('canvas');
  canvas.width = 360;
  canvas.height = 780;
  setupCanvasEvents(canvas, serial);
  wrapper.appendChild(canvas);

  const actions = document.createElement('div');
  actions.className = 'screen-actions';

  const screenshotBtn = document.createElement('button');
  screenshotBtn.className = 'btn btn-secondary';
  screenshotBtn.textContent = 'Screenshot';
  screenshotBtn.addEventListener('click', () => takeScreenshot(serial));
  actions.appendChild(screenshotBtn);

  const autoBtn = document.createElement('button');
  autoBtn.className = 'btn btn-secondary';
  autoBtn.dataset.auto = 'off';
  autoBtn.textContent = 'Auto refresh: OFF';
  autoBtn.addEventListener('click', () => toggleAutoScreenshot(serial, autoBtn));
  actions.appendChild(autoBtn);

  const hint = document.createElement('span');
  hint.className = 'swipe-hint';
  hint.textContent = 'Click = tap · Drag = swipe';
  actions.appendChild(hint);

  screen.appendChild(wrapper);
  screen.appendChild(actions);
  document.getElementById('phone-screens-container').appendChild(screen);

  state.phoneScreens[serial] = { canvas, tab, screen, wrapper };
  log(`Device added: ${device.model || serial}`);
}

function removePhoneScreen(serial) {
  const ps = state.phoneScreens[serial];
  if (!ps) return;
  ps.tab.remove();
  ps.screen.remove();
  if (state.screenshotTimers[serial]) {
    clearInterval(state.screenshotTimers[serial]);
    delete state.screenshotTimers[serial];
  }
  delete state.phoneScreens[serial];
  if (state.selectedSerial === serial) {
    state.selectedSerial = null;
    const remaining = Object.keys(state.phoneScreens);
    if (remaining.length > 0) selectDevice(remaining[0]);
  }
  log(`Device removed: ${serial}`);
}

function activatePhoneTab(serial) {
  document.querySelectorAll('.phone-tab').forEach((t) => t.classList.remove('active'));
  document.querySelectorAll('.phone-screen').forEach((s) => s.classList.remove('active'));

  const ps = state.phoneScreens[serial];
  if (ps) {
    ps.tab.classList.add('active');
    ps.screen.classList.add('active');
  }
}

// ── Canvas Events (Tap/Swipe) ──
function setupCanvasEvents(canvas, serial) {
  let startPos = null;
  let isDragging = false;

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    startPos = {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    };
    isDragging = true;
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!isDragging || !startPos) return;
    const rect = canvas.getBoundingClientRect();
    const endX = (e.clientX - rect.left) / rect.width;
    const endY = (e.clientY - rect.top) / rect.height;
    drawSwipeLine(canvas, startPos.x, startPos.y, endX, endY);
  });

  canvas.addEventListener('mouseup', (e) => {
    if (!startPos) return;
    const rect = canvas.getBoundingClientRect();
    const endX = (e.clientX - rect.left) / rect.width;
    const endY = (e.clientY - rect.top) / rect.height;

    const dx = (endX - startPos.x) * canvas.width;
    const dy = (endY - startPos.y) * canvas.height;
    const dist = Math.sqrt(dx * dx + dy * dy);

    const sx = clamp(startPos.x, 0, 1);
    const sy = clamp(startPos.y, 0, 1);
    const ex = clamp(endX, 0, 1);
    const ey = clamp(endY, 0, 1);

    if (dist < 8) {
      sendTapCommand(serial, sx, sy);
    } else {
      sendSwipeCommand(serial, sx, sy, ex, ey);
    }

    startPos = null;
    isDragging = false;
    redrawCanvas(canvas, serial);
  });

  canvas.addEventListener('mouseleave', () => {
    if (isDragging) {
      startPos = null;
      isDragging = false;
      redrawCanvas(canvas, serial);
    }
  });
}

function drawSwipeLine(canvas, x1, y1, x2, y2) {
  const ps = Object.values(state.phoneScreens).find((p) => p.canvas === canvas);
  redrawCanvas(canvas, ps ? findSerialByCanvas(canvas) : null);

  const ctx = canvas.getContext('2d');
  ctx.strokeStyle = '#f85149';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.beginPath();
  ctx.moveTo(x1 * canvas.width, y1 * canvas.height);
  ctx.lineTo(x2 * canvas.width, y2 * canvas.height);
  ctx.stroke();

  ctx.fillStyle = '#f85149';
  ctx.beginPath();
  ctx.arc(x2 * canvas.width, y2 * canvas.height, 5, 0, Math.PI * 2);
  ctx.fill();
}

function redrawCanvas(canvas, serial) {
  const ctx = canvas.getContext('2d');
  const ps = serial ? state.phoneScreens[serial] : null;

  if (ps && ps.screenshotImg) {
    ctx.drawImage(ps.screenshotImg, 0, 0, canvas.width, canvas.height);
  } else {
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#484f58';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No screenshot', canvas.width / 2, canvas.height / 2);
  }
}

function findSerialByCanvas(canvas) {
  for (const [serial, ps] of Object.entries(state.phoneScreens)) {
    if (ps.canvas === canvas) return serial;
  }
  return null;
}

// ── Commands ──
async function sendTapCommand(serial, x, y) {
  const targets = state.broadcastMode ? [] : [serial];
  try {
    const result = await invoke('send_command', {
      cmdType: 'TAP', x, y,
      endX: 0, endY: 0, durationMs: 0,
      text: null, keyCode: 0,
      targetDevices: targets,
      tapViewId: null, tapText: null, tapContentDesc: null,
    });
    log(`${result.success ? '✓' : '✗'} Tap (${x.toFixed(2)}, ${y.toFixed(2)})`, result.success);
  } catch (e) {
    log(`✗ Tap error: ${e}`, false);
  }
}

async function sendSwipeCommand(serial, x1, y1, x2, y2) {
  const targets = state.broadcastMode ? [] : [serial];
  try {
    const result = await invoke('send_command', {
      cmdType: 'SWIPE', x: x1, y: y1,
      endX: x2, endY: y2, durationMs: 500,
      text: null, keyCode: 0,
      targetDevices: targets,
      tapViewId: null, tapText: null, tapContentDesc: null,
    });
    log(`${result.success ? '✓' : '✗'} Swipe (${x1.toFixed(2)},${y1.toFixed(2)})→(${x2.toFixed(2)},${y2.toFixed(2)})`, result.success);
  } catch (e) {
    log(`✗ Swipe error: ${e}`, false);
  }
}

async function sendKeyCommand(keyCode) {
  const keyNames = { 3: 'HOME', 4: 'BACK', 82: 'MENU', 187: 'RECENT' };
  const targets = getTargetDevices();
  try {
    const result = await invoke('send_command', {
      cmdType: 'KEY', x: 0, y: 0,
      endX: 0, endY: 0, durationMs: 0,
      text: null, keyCode,
      targetDevices: targets,
      tapViewId: null, tapText: null, tapContentDesc: null,
    });
    log(`${result.success ? '✓' : '✗'} ${keyNames[keyCode] || 'KEY_' + keyCode}`, result.success);
  } catch (e) {
    log(`✗ Key error: ${e}`, false);
  }
}

async function sendText() {
  const input = document.getElementById('text-input');
  const text = input.value.trim();
  if (!text) return;
  const targets = getTargetDevices();
  try {
    const result = await invoke('send_command', {
      cmdType: 'TEXT', x: 0, y: 0,
      endX: 0, endY: 0, durationMs: 0,
      text, keyCode: 0,
      targetDevices: targets,
      tapViewId: null, tapText: null, tapContentDesc: null,
    });
    log(`${result.success ? '✓' : '✗'} Text: ${text}`, result.success);
    input.value = '';
  } catch (e) {
    log(`✗ Text error: ${e}`, false);
  }
}

// ── Screenshots ──
async function takeScreenshot(serial) {
  try {
    const result = await invoke('get_screenshot', { serial });
    displayScreenshot(serial, result);
  } catch (e) {
    log(`✗ Screenshot error: ${e}`, false);
  }
}

function displayScreenshot(serial, data) {
  const ps = state.phoneScreens[serial];
  if (!ps) return;

  const img = new Image();
  img.onload = () => {
    ps.screenshotImg = img;

    if (data.width > 0 && data.height > 0) {
      const aspect = data.width / data.height;
      ps.canvas.width = Math.round(ps.canvas.height * aspect);
    }

    redrawCanvas(ps.canvas, serial);
  };
  img.src = `data:image/jpeg;base64,${data.base64}`;
}

function toggleAutoScreenshot(serial, btn) {
  if (state.screenshotTimers[serial]) {
    clearInterval(state.screenshotTimers[serial]);
    delete state.screenshotTimers[serial];
    btn.textContent = 'Auto refresh: OFF';
    btn.dataset.auto = 'off';
  } else {
    takeScreenshot(serial);
    state.screenshotTimers[serial] = setInterval(() => takeScreenshot(serial), 1000);
    btn.textContent = 'Auto refresh: ON';
    btn.dataset.auto = 'on';
  }
}

// ── Mirror ──
async function startMirror() {
  const serial = state.selectedSerial;
  if (!serial) return log('Select a device first', false);
  try {
    await invoke('start_mirror', { serial });
    log(`Mirror started for ${serial}`, true);
  } catch (e) {
    log(`✗ Mirror error: ${e}`, false);
  }
}

async function stopMirror() {
  const serial = state.selectedSerial;
  if (!serial) return log('Select a device first', false);
  try {
    await invoke('stop_mirror', { serial });
    log(`Mirror stopped for ${serial}`, true);
  } catch (e) {
    log(`✗ Stop mirror error: ${e}`, false);
  }
}

// ── Install Agent ──
async function installAgent() {
  const serial = state.selectedSerial;
  if (!serial) return log('Select a device first', false);
  log(`Installing agent on ${serial}...`);
  try {
    const result = await invoke('install_agent', { serial });
    log(result.message, result.success);
  } catch (e) {
    log(`✗ Install error: ${e}`, false);
  }
}

// ── Helpers ──
function getTargetDevices() {
  if (state.broadcastMode) return [];
  return state.selectedSerial ? [state.selectedSerial] : [];
}

function log(message, success = null) {
  const output = document.getElementById('log-output');
  const entry = document.createElement('div');
  entry.className = 'log-entry' + (success === true ? ' success' : success === false ? ' error' : '');
  const now = new Date();
  const time = [now.getHours(), now.getMinutes(), now.getSeconds()]
    .map((n) => String(n).padStart(2, '0'))
    .join(':');
  entry.innerHTML = `<span class="log-time">${time}</span>${escapeHtml(message)}`;
  output.appendChild(entry);
  output.scrollTop = output.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function clamp(val, min, max) {
  return Math.max(min, Math.min(max, val));
}
