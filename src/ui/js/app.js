/**
 * S_Audio_Pin_Linux — Frontend Application Controller
 */

// State
let selectedSourceIds = new Set();
let currentConfig = {
  format: 'mp3',
  bitrate: '320k',
  mode: 'single_mix',
  output_dir: '',
  sample_rate: 48000
};
let isRecording = false;
let recordTimerInterval = null;
let recordingStartTime = 0;
let ws = null;
let reconnectTimer = null;

// DOM Elements
const appsListEl = document.getElementById('appsList');
const micsListEl = document.getElementById('micsList');
const armedCountEl = document.getElementById('armedCount');
const configFormatTagEl = document.getElementById('configFormatTag');
const configModeTagEl = document.getElementById('configModeTag');
const btnRecordToggle = document.getElementById('btnRecordToggle');
const recordBtnLabel = document.getElementById('recordBtnLabel');
const recTimerEl = document.getElementById('recTimer');
const recBadgeEl = document.getElementById('recBadge');
const wsStatusEl = document.getElementById('wsStatus');
const quickModeToggle = document.getElementById('quickModeToggle');
const quickModeLabel = document.getElementById('quickModeLabel');

// Settings Modal Elements
const settingsModal = document.getElementById('settingsModal');
const btnOpenSettings = document.getElementById('btnOpenSettings');
const btnCloseSettings = document.getElementById('btnCloseSettings');
const btnCancelSettings = document.getElementById('btnCancelSettings');
const btnSaveSettings = document.getElementById('btnSaveSettings');
const settingBitrate = document.getElementById('settingBitrate');
const settingOutputDir = document.getElementById('settingOutputDir');
const bitrateGroup = document.getElementById('bitrateGroup');

// Toast
const completionToast = document.getElementById('completionToast');
const toastTitle = document.getElementById('toastTitle');
const toastDetails = document.getElementById('toastDetails');
const btnToastOpenFolder = document.getElementById('btnToastOpenFolder');
const btnToastDismiss = document.getElementById('btnToastDismiss');

// Init
document.addEventListener('DOMContentLoaded', () => {
  loadConfig();
  fetchSources();
  initWebSocket();
  setupEventListeners();

  // Periodic source refresh (e.g. apps opening/closing)
  setInterval(fetchSources, 2000);
});

// Setup Events
function setupEventListeners() {
  btnRecordToggle.addEventListener('click', toggleRecording);
  
  document.getElementById('btnSelectAllApps').addEventListener('click', () => selectAll('app', true));
  document.getElementById('btnDeselectAllApps').addEventListener('click', () => selectAll('app', false));
  document.getElementById('btnSelectAllMics').addEventListener('click', () => selectAll('mic', true));
  document.getElementById('btnDeselectAllMics').addEventListener('click', () => selectAll('mic', false));

  document.getElementById('btnOpenRecordings').addEventListener('click', () => openFolder());
  btnToastOpenFolder.addEventListener('click', () => openFolder());
  btnToastDismiss.addEventListener('click', () => { completionToast.style.display = 'none'; });

  // Quick Mode Switch in bottom bar
  quickModeToggle.addEventListener('change', async (e) => {
    const newMode = e.target.checked ? 'multi_stem' : 'single_mix';
    currentConfig.mode = newMode;
    updateModeDisplay();
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: newMode })
    });
  });

  // Settings modal
  btnOpenSettings.addEventListener('click', openSettings);
  btnCloseSettings.addEventListener('click', closeSettings);
  btnCancelSettings.addEventListener('click', closeSettings);
  btnSaveSettings.addEventListener('click', saveSettings);
  document.getElementById('btnOpenFolderPicker').addEventListener('click', () => openFolder());

  // Quit Application
  const btnQuitApp = document.getElementById('btnQuitApp');
  if (btnQuitApp) {
    btnQuitApp.addEventListener('click', async () => {
      let msg = 'Повністю вимкнути додаток (зупинити фоновий сервер)?';
      if (isRecording) {
        msg = '⚠️ Увага: Запис ще триває!\nЗупинити запис, зберегти аудіо та повністю вимкнути додаток?';
      }
      if (!confirm(msg)) return;

      document.body.innerHTML = `
        <div style="height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0b0f19; color: #94a3b8; font-family: system-ui, -apple-system, sans-serif; gap: 1.2rem; text-align: center; padding: 2rem;">
          <div style="font-size: 3.5rem;">🎙️</div>
          <h2 style="color: #f8fafc; margin: 0; font-size: 1.6rem;">Завершення роботи...</h2>
          <p style="margin: 0; color: #64748b;">Зупиняємо аудіопотоки та вимикаємо додаток.</p>
        </div>
      `;

      // Send shutdown request via fetch and sendBeacon
      try {
        if (navigator.sendBeacon) {
          navigator.sendBeacon('/api/shutdown');
        }
        await fetch('/api/shutdown', { method: 'POST', keepalive: true });
      } catch (e) {
        // Expected as server terminates
      }
    });
  }

  // Format radio change in settings
  document.querySelectorAll('input[name="audioFormat"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      bitrateGroup.style.display = e.target.value === 'mp3' ? 'flex' : 'none';
    });
  });
}

// Fetch Config
async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    if (res.ok) {
      currentConfig = await res.json();
      updateModeDisplay();
    }
  } catch (err) {
    console.error('Error loading config:', err);
  }
}

function updateModeDisplay() {
  const isMp3 = currentConfig.format === 'mp3';
  configFormatTagEl.textContent = isMp3 ? `MP3 • ${currentConfig.bitrate}` : 'WAV • Lossless';
  configModeTagEl.textContent = currentConfig.mode === 'multi_stem' ? 'Окремі стеми' : 'Зведений мікс';
  quickModeToggle.checked = currentConfig.mode === 'multi_stem';
}

// Fetch Sources
async function fetchSources() {
  try {
    const res = await fetch('/api/sources');
    if (res.ok) {
      const data = await res.json();
      renderSourcesList(appsListEl, data.apps || [], 'app');
      renderSourcesList(micsListEl, data.mics || [], 'mic');
      updateArmedCount();
    }
  } catch (err) {
    console.error('Error fetching sources:', err);
  }
}

// Render Source Cards
function renderSourcesList(container, sources, type) {
  if (sources.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>${type === 'app' ? 'Немає активних програм з аудіо' : 'Не виявлено підключених мікрофонів'}</p>
      </div>
    `;
    return;
  }

  // Preserve existing canvas elements if source list hasn't changed structure
  const existingIds = new Set(Array.from(container.querySelectorAll('.source-card')).map(el => el.dataset.sourceId));
  const newIds = new Set(sources.map(s => s.id));
  
  const isStructureEqual = existingIds.size === newIds.size && [...existingIds].every(id => newIds.has(id));

  if (!isStructureEqual) {
    container.innerHTML = '';
    sources.forEach(src => {
      const card = createSourceCard(src);
      container.appendChild(card);
    });
  } else {
    // Just update values and selection
    sources.forEach(src => {
      const card = container.querySelector(`[data-source-id="${src.id}"]`);
      if (card) {
        const checkbox = card.querySelector('.custom-checkbox');
        checkbox.checked = selectedSourceIds.has(src.id);
        card.classList.toggle('selected', selectedSourceIds.has(src.id));
      }
    });
  }
}

function createSourceCard(src) {
  const card = document.createElement('div');
  card.className = 'source-card' + (selectedSourceIds.has(src.id) ? ' selected' : '');
  card.dataset.sourceId = src.id;

  const isApp = src.type === 'app';
  const iconEmoji = isApp ? '🎵' : '🎙️';
  const pidTag = src.pid ? `<span class="tag-pid">PID: ${src.pid}</span>` : '';
  const streamBadge = (isApp && src.stream_count > 1) ? `<span class="tag-streams">${src.stream_count} аудіопотоки</span>` : '';
  const micBadge = !isApp ? `<span class="tag-mic">Вхідний мікрофон</span>` : '';

  card.innerHTML = `
    <div class="source-avatar">${iconEmoji}</div>
    <div class="source-info">
      <div class="source-name" title="${src.name}">${src.name}</div>
      <div class="source-meta">
        ${pidTag}
        ${streamBadge}
        ${micBadge}
        <span>${src.channels === 1 ? 'Моно' : 'Стерео'} • ${src.sample_rate} Hz</span>
      </div>
    </div>
    <div class="meter-container">
      <div class="meter-labels">
        <span>-48dB</span>
        <span>-12dB</span>
        <span>0dB</span>
      </div>
      <canvas class="meter-canvas" id="canvas_${src.id.replace(':', '_')}"></canvas>
    </div>
    <div class="checkbox-wrapper">
      <input type="checkbox" class="custom-checkbox" ${selectedSourceIds.has(src.id) ? 'checked' : ''}>
    </div>
  `;

  // Toggle selection on card click
  card.addEventListener('click', (e) => {
    if (e.target.tagName !== 'INPUT') {
      const checkbox = card.querySelector('.custom-checkbox');
      checkbox.checked = !checkbox.checked;
    }
    const isChecked = card.querySelector('.custom-checkbox').checked;
    if (isChecked) {
      selectedSourceIds.add(src.id);
      card.classList.add('selected');
    } else {
      selectedSourceIds.delete(src.id);
      card.classList.remove('selected');
    }
    updateArmedCount();
  });

  // Register canvas with visualizer engine after DOM append
  setTimeout(() => {
    const canvas = card.querySelector('.meter-canvas');
    if (canvas && window.visualizerEngine) {
      window.visualizerEngine.registerCanvas(src.id, canvas);
    }
  }, 10);

  return card;
}

function selectAll(type, select) {
  const container = type === 'app' ? appsListEl : micsListEl;
  container.querySelectorAll('.source-card').forEach(card => {
    const id = card.dataset.sourceId;
    const checkbox = card.querySelector('.custom-checkbox');
    checkbox.checked = select;
    if (select) {
      selectedSourceIds.add(id);
      card.classList.add('selected');
    } else {
      selectedSourceIds.delete(id);
      card.classList.remove('selected');
    }
  });
  updateArmedCount();
}

function updateArmedCount() {
  armedCountEl.textContent = selectedSourceIds.size;
  if (!isRecording) {
    recBadgeEl.textContent = selectedSourceIds.size > 0 ? `${selectedSourceIds.size} ГОТОВО` : 'ОЧІКУВАННЯ';
  }
}

// WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    wsStatusEl.classList.remove('disconnected');
    wsStatusEl.querySelector('.status-text').textContent = 'Підключено';
    if (reconnectTimer) {
      clearInterval(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'audio_meters') {
        // Feed real-time peaks into 60fps visualizer engine
        if (data.peaks && window.visualizerEngine) {
          for (const [sourceId, level] of Object.entries(data.peaks)) {
            window.visualizerEngine.updatePeak(sourceId, level);
          }
        }

        // Update recording state & timer from server
        if (data.recording) {
          syncRecordingState(data.recording);
        }
      }
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };

  ws.onclose = () => {
    wsStatusEl.classList.add('disconnected');
    wsStatusEl.querySelector('.status-text').textContent = 'Відключено';
    if (!reconnectTimer) {
      reconnectTimer = setInterval(initWebSocket, 2000);
    }
  };

  ws.onerror = () => {
    ws.close();
  };
}

function syncRecordingState(rec) {
  if (rec.is_recording && !isRecording) {
    isRecording = true;
    btnRecordToggle.classList.add('recording');
    recordBtnLabel.textContent = 'Зупинити запис';
    recBadgeEl.className = 'rec-status-badge active';
    recBadgeEl.textContent = 'ЗАПИС';
  } else if (!rec.is_recording && isRecording) {
    isRecording = false;
    btnRecordToggle.classList.remove('recording');
    recordBtnLabel.textContent = 'Почати запис';
    recBadgeEl.className = 'rec-status-badge idle';
    recBadgeEl.textContent = 'ГОТОВИЙ';
  }

  if (rec.is_recording && rec.duration_secs !== undefined) {
    recTimerEl.textContent = formatDuration(rec.duration_secs);
  }
}

function formatDuration(totalSeconds) {
  const s = Math.floor(totalSeconds % 60);
  const m = Math.floor((totalSeconds / 60) % 60);
  const h = Math.floor(totalSeconds / 3600);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

// Recording Controls
async function toggleRecording() {
  if (!isRecording) {
    if (selectedSourceIds.size === 0) {
      alert('Будь ласка, оберіть хоча б одну програму або мікрофон для запису!');
      return;
    }

    try {
      const res = await fetch('/api/record/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_ids: Array.from(selectedSourceIds),
          format: currentConfig.format,
          bitrate: currentConfig.bitrate,
          mode: currentConfig.mode
        })
      });

      if (!res.ok) {
        const err = await res.json();
        alert(`Помилка початку запису: ${err.detail || 'Невідома помилка'}`);
      }
    } catch (err) {
      alert(`Помилка запису: ${err}`);
    }

  } else {
    // Stop recording
    recBadgeEl.textContent = 'ФІНАЛІЗАЦІЯ...';
    try {
      const res = await fetch('/api/record/stop', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        showCompletionToast(data);
      }
    } catch (err) {
      console.error('Stop record error:', err);
    }
  }
}

function showCompletionToast(data) {
  const mb = (data.total_bytes / (1024 * 1024)).toFixed(1);
  toastTitle.textContent = 'Запис успішно збережено!';
  toastDetails.textContent = `Тривалість: ${formatDuration(data.duration_secs)} • Розмір: ${mb} MB • Файлів: ${data.output_files.length}`;
  completionToast.style.display = 'flex';
}

// Open Folder
async function openFolder() {
  try {
    await fetch('/api/open-folder', { method: 'POST' });
  } catch (err) {
    console.error('Error opening folder:', err);
  }
}

// Settings Modal
function openSettings() {
  document.querySelector(`input[name="audioFormat"][value="${currentConfig.format}"]`).checked = true;
  document.querySelector(`input[name="recordMode"][value="${currentConfig.mode}"]`).checked = true;
  settingBitrate.value = currentConfig.bitrate || '320k';
  settingOutputDir.value = currentConfig.output_dir || '';
  bitrateGroup.style.display = currentConfig.format === 'mp3' ? 'flex' : 'none';
  settingsModal.style.display = 'flex';
}

function closeSettings() {
  settingsModal.style.display = 'none';
}

async function saveSettings() {
  const format = document.querySelector('input[name="audioFormat"]:checked').value;
  const mode = document.querySelector('input[name="recordMode"]:checked').value;
  const bitrate = settingBitrate.value;

  currentConfig.format = format;
  currentConfig.mode = mode;
  currentConfig.bitrate = bitrate;

  try {
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format, mode, bitrate })
    });
    updateModeDisplay();
    closeSettings();
  } catch (err) {
    alert(`Помилка збереження налаштувань: ${err}`);
  }
}
