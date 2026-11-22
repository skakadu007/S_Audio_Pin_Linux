/**
 * S_Audio_Pin_Linux — Frontend Application Controller
 */

const TRANSLATIONS = {
  uk: {
    connected: 'Підключено',
    disconnected: 'Відключено',
    langToggleTitle: 'Перемкнути мову (UK / EN)',
    historyTitle: 'Історія збережених записів',
    historyBtn: 'Історія',
    openFolderTitle: 'Відкрити папку записів',
    recordingsBtn: 'Записи',
    settingsTitle: 'Налаштування запису',
    settingsLockedTitle: 'Налаштування недоступні під час запису',
    quitTitle: 'Повністю вимкнути додаток',
    hideLabel: 'Сховати',
    appsHeading: 'Програми',
    appsDesc: 'Активні аудіопотоки системи',
    micsHeading: 'Мікрофони',
    micsDesc: 'Фізичні та віртуальні входи',
    selectAll: 'Обрати всі',
    deselectAll: 'Зняти',
    searchingApps: 'Пошук активних програм із аудіо...',
    detectingMics: 'Виявлення мікрофонів...',
    noApps: 'Немає активних програм з аудіо',
    noMics: 'Не виявлено підключених мікрофонів',
    sourcesSuffix: 'джерел',
    modeMix: 'Зведений мікс',
    modeStems: 'Стеми',
    startRecord: 'Почати запис',
    stopRecord: 'Зупинити запис',
    stemsToggle: 'Стеми (Окремі)',
    statusReady: 'ГОТОВИЙ',
    statusWaiting: 'ОЧІКУВАННЯ',
    statusArmedCount: '{count} ГОТОВО',
    statusRecording: 'ЗАПИС',
    statusFinalizing: 'ФІНАЛІЗАЦІЯ...',
    openFolderBtn: 'Відкрити папку',
    closeBtn: 'Закрити',
    settingsHeading: 'Налаштування запису',
    audioFormatLabel: 'Формат аудіо',
    bitrateLabel: 'Бітрейт',
    bitrate128: '128 kbps (Стандарт)',
    bitrate192: '192 kbps (Висока якість)',
    bitrate256: '256 kbps (Дуже висока)',
    bitrate320: '320 kbps (Максимум)',
    sampleRateLabel: 'Частота дискретизації',
    sr48000: '48000 Hz (Студія)',
    sr44100: '44100 Hz (CD)',
    recordModeLabel: 'Режим запису до файлу',
    modeSingleOption: 'Один майстер-мікс (Single Mix)',
    modeMultiOption: 'Окремі файли (Stems)',
    modeHint: 'У режимі "Stems" кожна програма та мікрофон записуються в індивідуальний синхронізований файл для монтажу.',
    outputDirLabel: 'Папка для збереження записів',
    browseBtn: 'Огляд',
    cancelBtn: 'Скасувати',
    saveBtn: 'Зберегти',
    historyHeading: 'Історія записів',
    loadingHistory: 'Завантаження списку записів...',
    noHistory: 'Ще немає збережених записів',
    confirmHeading: 'Підтвердження',
    confirmBtn: 'Підтвердити',
    streamsTag: '{count} стрім.',
    btTag: 'BT • HFP при записі',
    btTitle: 'Bluetooth-мікрофон активується лише під час запису, щоб не перемикати навушники в HFP',
    micArmedHint: 'Вхід (при ARM)',
    micArmedTitle: 'Мікрофон активується при виборі ARM',
    micActive: 'Вхід',
    armTitle: 'Вибрати це джерело для запису (ARM)',
    missingDeps: 'Відсутні системні утиліти для запису: {deps}. Встановіть їх у системі.',
    quitTitleModal: 'Вимкнути додаток',
    quitMsgRecording: 'Увага: запис ще триває! Зупинити запис, зберегти аудіо та повністю вимкнути додаток?',
    quitMsgIdle: 'Повністю вимкнути додаток і зупинити фоновий моніторинг?',
    quitBtnSave: 'Зберегти і вимкнути',
    quitBtn: 'Вимкнути',
    shuttingDownTitle: 'Завершення роботи...',
    shuttingDownDesc: 'Зупиняємо аудіопотоки та вимикаємо сервер S_Audio_Pin.',
    streamRestoredTitle: 'Аудіопотік відновлено ({count})',
    streamRestoredDefault: 'Аудіопотік автоматично перепідключено після зміни пристрою.',
    noSourcesTitle: 'Джерела не обрано',
    noSourcesDesc: 'Оберіть хоча б одну програму або мікрофон (ARM) перед початком запису.',
    startFailedTitle: 'Не вдалося почати запис',
    startErrTitle: 'Помилка запуску запису',
    stopFailedTitle: 'Помилка фіналізації запису',
    stopFailedFallback: 'Не вдалося зберегти запис.',
    stopErrTitle: 'Помилка зупинки запису',
    unknownServerErr: 'Невідома помилка сервера',
    recSavedTitle: 'Запис успішно збережено!',
    recSavedWarnTitle: 'Запис збережено (з попередженнями)',
    recSavedDetails: 'Тривалість: {dur} • Розмір: {size} • Файлів: {files}',
    recSavedReconn: ' • Перепідключень: {count}',
    openDirErrTitle: 'Не вдалося відкрити папку',
    openDirErrDesc: 'Помилка відкриття директорії',
    pickerErrTitle: 'Не вдалося відкрити діалог вибору папки',
    invalidPathTitle: 'Некоректний шлях',
    invalidPathDesc: 'Вкажіть папку для збереження записів.',
    saveSettingsErrTitle: 'Помилка збереження налаштувань',
    saveSettingsErrDesc: 'Перевірте права доступу до папки',
    kindDir: 'Стеми (папка)',
    kindFile: 'Аудіофайл',
    openBtn: 'Відкрити',
    deleteBtn: 'Видалити',
    deleteTitle: 'Видалити запис',
    deleteMsg: 'Видалити "{name}" з диска назавжди?',
    deleteErrTitle: 'Помилка видалення',
    deleteErrDesc: 'Не вдалося видалити запис',
    historyErr: 'Помилка завантаження історії: {err}'
  },
  en: {
    connected: 'Connected',
    disconnected: 'Disconnected',
    langToggleTitle: 'Switch language (UK / EN)',
    historyTitle: 'Saved recordings history',
    historyBtn: 'History',
    openFolderTitle: 'Open recordings folder',
    recordingsBtn: 'Recordings',
    settingsTitle: 'Recording settings',
    settingsLockedTitle: 'Settings are unavailable while recording',
    quitTitle: 'Quit application completely',
    hideLabel: 'Hide',
    appsHeading: 'Applications',
    appsDesc: 'Active system audio streams',
    micsHeading: 'Microphones',
    micsDesc: 'Hardware and virtual inputs',
    selectAll: 'Select all',
    deselectAll: 'Clear',
    searchingApps: 'Scanning for active audio applications...',
    detectingMics: 'Detecting microphones...',
    noApps: 'No active audio applications found',
    noMics: 'No connected microphones detected',
    sourcesSuffix: 'sources',
    modeMix: 'Master Mix',
    modeStems: 'Stems',
    startRecord: 'Start Recording',
    stopRecord: 'Stop Recording',
    stemsToggle: 'Stems (Separate)',
    statusReady: 'READY',
    statusWaiting: 'IDLE',
    statusArmedCount: '{count} ARMED',
    statusRecording: 'REC',
    statusFinalizing: 'FINALIZING...',
    openFolderBtn: 'Open Folder',
    closeBtn: 'Close',
    settingsHeading: 'Recording Settings',
    audioFormatLabel: 'Audio Format',
    bitrateLabel: 'Bitrate',
    bitrate128: '128 kbps (Standard)',
    bitrate192: '192 kbps (High quality)',
    bitrate256: '256 kbps (Very high)',
    bitrate320: '320 kbps (Maximum)',
    sampleRateLabel: 'Sample Rate',
    sr48000: '48000 Hz (Studio)',
    sr44100: '44100 Hz (CD)',
    recordModeLabel: 'Recording Output Mode',
    modeSingleOption: 'Single Master Mix',
    modeMultiOption: 'Separate Files (Stems)',
    modeHint: 'In "Stems" mode, each application and microphone is saved into its own synchronized track for editing.',
    outputDirLabel: 'Recordings Output Folder',
    browseBtn: 'Browse',
    cancelBtn: 'Cancel',
    saveBtn: 'Save',
    historyHeading: 'Recordings History',
    loadingHistory: 'Loading recordings...',
    noHistory: 'No saved recordings yet',
    confirmHeading: 'Confirmation',
    confirmBtn: 'Confirm',
    streamsTag: '{count} streams',
    btTag: 'BT • HFP when rec',
    btTitle: 'Bluetooth mic activates only during recording to keep headphones in A2DP mode',
    micArmedHint: 'Input (on ARM)',
    micArmedTitle: 'Microphone activates when armed',
    micActive: 'Input',
    armTitle: 'Arm this source for recording (ARM)',
    missingDeps: 'Missing required recording tools: {deps}. Please install them on your system.',
    quitTitleModal: 'Quit Application',
    quitMsgRecording: 'Warning: recording is still active! Stop recording, save audio, and quit?',
    quitMsgIdle: 'Quit the application and stop background monitoring?',
    quitBtnSave: 'Save & Quit',
    quitBtn: 'Quit',
    shuttingDownTitle: 'Shutting down...',
    shuttingDownDesc: 'Stopping audio streams and shutting down S_Audio_Pin.',
    streamRestoredTitle: 'Audio stream recovered ({count})',
    streamRestoredDefault: 'Audio stream automatically reconnected after device change.',
    noSourcesTitle: 'No sources selected',
    noSourcesDesc: 'Please arm at least one application or microphone before recording.',
    startFailedTitle: 'Could not start recording',
    startErrTitle: 'Recording start error',
    stopFailedTitle: 'Finalization error',
    stopFailedFallback: 'Failed to save recording.',
    stopErrTitle: 'Error stopping recording',
    unknownServerErr: 'Unknown server error',
    recSavedTitle: 'Recording saved!',
    recSavedWarnTitle: 'Recording saved (with warnings)',
    recSavedDetails: 'Duration: {dur} • Size: {size} • Files: {files}',
    recSavedReconn: ' • Reconnections: {count}',
    openDirErrTitle: 'Could not open folder',
    openDirErrDesc: 'Failed to open directory',
    pickerErrTitle: 'Could not open folder picker dialog',
    invalidPathTitle: 'Invalid path',
    invalidPathDesc: 'Please specify an output folder for recordings.',
    saveSettingsErrTitle: 'Failed to save settings',
    saveSettingsErrDesc: 'Check folder write permissions',
    kindDir: 'Stems (folder)',
    kindFile: 'Audio file',
    openBtn: 'Open',
    deleteBtn: 'Delete',
    deleteTitle: 'Delete Recording',
    deleteMsg: 'Permanently delete "{name}" from disk?',
    deleteErrTitle: 'Delete failed',
    deleteErrDesc: 'Could not delete recording',
    historyErr: 'Failed to load history: {err}'
  }
};

function detectInitialLang() {
  try {
    const saved = localStorage.getItem('s_audio_pin_lang');
    if (saved === 'uk' || saved === 'en') return saved;
  } catch (e) {
    // ignore storage errors
  }
  const nav = (navigator.language || 'uk').toLowerCase();
  return nav.startsWith('uk') ? 'uk' : 'en';
}

// State
let currentLang = detectInitialLang();
let selectedSourceIds = new Set();
let missedSourcePolls = new Map();
let lastSourcesData = { apps: [], mics: [] };
let currentConfig = {
  format: 'mp3',
  bitrate: '320k',
  mode: 'single_mix',
  output_dir: '',
  sample_rate: 48000
};
let isRecording = false;
let isWsConnected = true;
let lastSeenReconnections = 0;
let ws = null;
let reconnectTimer = null;
let toastAutoHideTimer = null;

function t(key, params = {}) {
  const dict = TRANSLATIONS[currentLang] || TRANSLATIONS.uk;
  let text = dict[key] !== undefined ? dict[key] : (TRANSLATIONS.uk[key] || key);
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, String(v));
  }
  return text;
}

function applyTranslations() {
  document.documentElement.lang = currentLang;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) el.textContent = t(key);
  });

  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    if (key) el.title = t(key);
  });

  const btnLang = document.getElementById('btnLangToggle');
  if (btnLang) {
    btnLang.textContent = currentLang.toUpperCase();
  }

  const statusTextEl = wsStatusEl ? wsStatusEl.querySelector('.status-text') : null;
  if (statusTextEl) {
    statusTextEl.textContent = isWsConnected ? t('connected') : t('disconnected');
  }

  recordBtnLabel.textContent = isRecording ? t('stopRecord') : t('startRecord');
  updateModeDisplay();
  updateArmedCount();
  if (isRecording) {
    recBadgeEl.textContent = t('statusRecording');
  }
  setControlsLocked(isRecording);

  if (lastSourcesData.apps.length > 0 || lastSourcesData.mics.length > 0) {
    renderSourcesList(appsListEl, lastSourcesData.apps, 'app');
    renderSourcesList(micsListEl, lastSourcesData.mics, 'mic');
  }
}

// DOM Elements
const appsListEl = document.getElementById('appsList');
const micsListEl = document.getElementById('micsList');
const appsCountEl = document.getElementById('appsCount');
const micsCountEl = document.getElementById('micsCount');
const armedCountEl = document.getElementById('armedCount');
const configFormatTagEl = document.getElementById('configFormatTag');
const configModeTagEl = document.getElementById('configModeTag');
const btnRecordToggle = document.getElementById('btnRecordToggle');
const recordBtnLabel = document.getElementById('recordBtnLabel');
const recTimerEl = document.getElementById('recTimer');
const recBadgeEl = document.getElementById('recBadge');
const wsStatusEl = document.getElementById('wsStatus');
const quickModeToggle = document.getElementById('quickModeToggle');
const quickSettingsBox = document.getElementById('quickSettingsBox');

// Health Banner
const healthBanner = document.getElementById('healthBanner');
const healthBannerText = document.getElementById('healthBannerText');
const btnDismissHealthBanner = document.getElementById('btnDismissHealthBanner');

// Settings Modal Elements
const settingsModal = document.getElementById('settingsModal');
const btnOpenSettings = document.getElementById('btnOpenSettings');
const btnCloseSettings = document.getElementById('btnCloseSettings');
const btnCancelSettings = document.getElementById('btnCancelSettings');
const btnSaveSettings = document.getElementById('btnSaveSettings');
const settingBitrate = document.getElementById('settingBitrate');
const settingSampleRate = document.getElementById('settingSampleRate');
const settingOutputDir = document.getElementById('settingOutputDir');
const bitrateGroup = document.getElementById('bitrateGroup');
const btnOpenFolderPicker = document.getElementById('btnOpenFolderPicker');

// History Modal Elements
const historyModal = document.getElementById('historyModal');
const btnHistory = document.getElementById('btnHistory');
const btnCloseHistory = document.getElementById('btnCloseHistory');
const btnHistoryCloseFooter = document.getElementById('btnHistoryCloseFooter');
const btnHistoryOpenDir = document.getElementById('btnHistoryOpenDir');
const historyListEl = document.getElementById('historyList');

// Confirm Modal Elements
const confirmModal = document.getElementById('confirmModal');
const confirmTitleEl = document.getElementById('confirmTitle');
const confirmMessageEl = document.getElementById('confirmMessage');
const btnCloseConfirm = document.getElementById('btnCloseConfirm');
const btnConfirmCancel = document.getElementById('btnConfirmCancel');
const btnConfirmAccept = document.getElementById('btnConfirmAccept');

// Toast
const completionToast = document.getElementById('completionToast');
const toastIcon = document.getElementById('toastIcon');
const toastTitle = document.getElementById('toastTitle');
const toastDetails = document.getElementById('toastDetails');
const btnToastOpenFolder = document.getElementById('btnToastOpenFolder');
const btnToastDismiss = document.getElementById('btnToastDismiss');

// Security & Fetch Helpers
function getApiToken() {
  const meta = document.querySelector('meta[name="api-token"]');
  return meta ? meta.getAttribute('content') : '';
}

function apiFetch(url, options = {}) {
  const headers = new Headers(options.headers || {});
  const token = getApiToken();
  if (token) {
    headers.set('X-API-Token', token);
  }
  return fetch(url, { ...options, headers });
}

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatBytes(bytes) {
  if (!bytes || bytes < 1024) return `${bytes || 0} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Notifications & Confirmations
function showToast({ title, details, variant = 'success', showOpenFolder = false, durationMs = 0 }) {
  if (toastAutoHideTimer) {
    clearTimeout(toastAutoHideTimer);
    toastAutoHideTimer = null;
  }

  completionToast.className = `completion-toast glass toast-${variant}`;
  toastIcon.textContent = variant === 'error' ? '!' : (variant === 'warning' ? '⚠' : (variant === 'info' ? '↻' : '✓'));
  toastTitle.textContent = title;
  toastDetails.textContent = details || '';
  btnToastOpenFolder.style.display = showOpenFolder ? 'inline-flex' : 'none';
  completionToast.style.display = 'flex';

  if (durationMs > 0) {
    toastAutoHideTimer = setTimeout(() => {
      completionToast.style.display = 'none';
    }, durationMs);
  }
}

function showConfirmDialog({ title, message, confirmText, danger = false }) {
  return new Promise((resolve) => {
    confirmTitleEl.textContent = title || t('confirmHeading');
    confirmMessageEl.textContent = message || '';
    btnConfirmAccept.textContent = confirmText || t('confirmBtn');
    btnConfirmAccept.className = danger ? 'btn btn-danger' : 'btn btn-primary';
    confirmModal.style.display = 'flex';

    const cleanup = (accepted) => {
      confirmModal.style.display = 'none';
      btnConfirmAccept.removeEventListener('click', onAccept);
      btnConfirmCancel.removeEventListener('click', onCancel);
      btnCloseConfirm.removeEventListener('click', onCancel);
      resolve(accepted);
    };

    const onAccept = () => cleanup(true);
    const onCancel = () => cleanup(false);

    btnConfirmAccept.addEventListener('click', onAccept);
    btnConfirmCancel.addEventListener('click', onCancel);
    btnCloseConfirm.addEventListener('click', onCancel);
  });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  applyTranslations();
  checkHealth();
  loadConfig();
  fetchSources();
  initWebSocket();
  setupEventListeners();

  setInterval(fetchSources, 2000);
});

function setupEventListeners() {
  btnRecordToggle.addEventListener('click', toggleRecording);

  const btnLang = document.getElementById('btnLangToggle');
  if (btnLang) {
    btnLang.addEventListener('click', () => {
      currentLang = currentLang === 'uk' ? 'en' : 'uk';
      try {
        localStorage.setItem('s_audio_pin_lang', currentLang);
      } catch (e) {
        // ignore storage errors
      }
      applyTranslations();
      checkHealth();
    });
  }

  document.getElementById('btnSelectAllApps').addEventListener('click', () => selectAll('app', true));
  document.getElementById('btnDeselectAllApps').addEventListener('click', () => selectAll('app', false));
  document.getElementById('btnSelectAllMics').addEventListener('click', () => selectAll('mic', true));
  document.getElementById('btnDeselectAllMics').addEventListener('click', () => selectAll('mic', false));

  document.getElementById('btnOpenRecordings').addEventListener('click', () => openFolder());
  btnToastOpenFolder.addEventListener('click', () => openFolder());
  btnToastDismiss.addEventListener('click', () => { completionToast.style.display = 'none'; });

  if (btnDismissHealthBanner) {
    btnDismissHealthBanner.addEventListener('click', () => {
      healthBanner.style.display = 'none';
    });
  }

  // Quick Mode Switch in bottom dock
  quickModeToggle.addEventListener('change', async (e) => {
    if (isRecording) {
      e.target.checked = currentConfig.mode === 'multi_stem';
      return;
    }
    const newMode = e.target.checked ? 'multi_stem' : 'single_mix';
    currentConfig.mode = newMode;
    updateModeDisplay();
    try {
      await apiFetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      });
    } catch (err) {
      console.error('Error updating mode:', err);
    }
  });

  // Settings modal
  btnOpenSettings.addEventListener('click', openSettings);
  btnCloseSettings.addEventListener('click', closeSettings);
  btnCancelSettings.addEventListener('click', closeSettings);
  btnSaveSettings.addEventListener('click', saveSettings);
  btnOpenFolderPicker.addEventListener('click', pickFolder);

  // History modal
  btnHistory.addEventListener('click', openHistoryModal);
  btnCloseHistory.addEventListener('click', closeHistoryModal);
  btnHistoryCloseFooter.addEventListener('click', closeHistoryModal);
  btnHistoryOpenDir.addEventListener('click', () => openFolder());

  // Quit Application
  const btnQuitApp = document.getElementById('btnQuitApp');
  if (btnQuitApp) {
    btnQuitApp.addEventListener('click', async () => {
      const confirmed = await showConfirmDialog({
        title: t('quitTitleModal'),
        message: isRecording ? t('quitMsgRecording') : t('quitMsgIdle'),
        confirmText: isRecording ? t('quitBtnSave') : t('quitBtn'),
        danger: true
      });
      if (!confirmed) return;

      document.body.innerHTML = `
        <div style="height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0c0d12; color: #a1a1aa; font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; gap: 1rem; text-align: center; padding: 2rem;">
          <div style="font-size: 2.8rem;">🎙️</div>
          <h2 style="color: #ffffff; margin: 0; font-size: 1.4rem; font-weight: 600;">${escapeHtml(t('shuttingDownTitle'))}</h2>
          <p style="margin: 0; color: #71717a; font-size: 0.9rem;">${escapeHtml(t('shuttingDownDesc'))}</p>
        </div>
      `;

      try {
        await apiFetch('/api/shutdown', { method: 'POST', keepalive: true });
      } catch (e) {
        // Expected as server terminates
      }
    });
  }

  // Format radio change in settings
  document.querySelectorAll('input[name="audioFormat"]').forEach(radio => {
    radio.addEventListener('change', (e) => {
      updateBitrateVisibility(e.target.value);
    });
  });
}

function updateBitrateVisibility(fmt) {
  bitrateGroup.style.display = (fmt === 'mp3' || fmt === 'ogg') ? 'flex' : 'none';
}

async function checkHealth() {
  try {
    const res = await apiFetch('/api/health');
    if (!res.ok) return;
    const data = await res.json();
    const deps = data.dependencies || {};
    const missing = [];
    if (!deps.parec) missing.push('parec');
    if (!deps.ffmpeg) missing.push('ffmpeg');

    if (missing.length > 0) {
      healthBannerText.textContent = t('missingDeps', { deps: missing.join(', ') });
      healthBanner.style.display = 'flex';
    } else {
      healthBanner.style.display = 'none';
    }
  } catch (err) {
    console.error('Health check failed:', err);
  }
}

async function syncArmedSources() {
  try {
    await apiFetch('/api/monitor/armed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_ids: Array.from(selectedSourceIds) })
    });
  } catch (err) {
    console.debug('Failed to sync armed sources:', err);
  }
}

// Fetch Config
async function loadConfig() {
  try {
    const res = await apiFetch('/api/config');
    if (res.ok) {
      currentConfig = await res.json();
      updateModeDisplay();
    }
  } catch (err) {
    console.error('Error loading config:', err);
  }
}

function updateModeDisplay() {
  const fmt = (currentConfig.format || 'mp3').toUpperCase();
  const hasBitrate = currentConfig.format === 'mp3' || currentConfig.format === 'ogg';
  configFormatTagEl.textContent = hasBitrate
    ? `${fmt} • ${currentConfig.bitrate}`
    : `${fmt} • Lossless`;
  configModeTagEl.textContent = currentConfig.mode === 'multi_stem' ? t('modeStems') : t('modeMix');
  quickModeToggle.checked = currentConfig.mode === 'multi_stem';
}

// Fetch Sources
async function fetchSources() {
  try {
    const res = await apiFetch('/api/sources');
    if (!res.ok) return;

    const data = await res.json();
    const apps = data.apps || [];
    const mics = data.mics || [];
    lastSourcesData = { apps, mics };

    if (appsCountEl) appsCountEl.textContent = apps.length;
    if (micsCountEl) micsCountEl.textContent = mics.length;

    const allActiveIds = new Set([
      ...apps.map(s => s.id),
      ...mics.map(s => s.id)
    ]);

    // Prune disappeared armed sources after 2 consecutive missed polls when idle
    let selectionChanged = false;
    for (const id of allActiveIds) {
      missedSourcePolls.set(id, 0);
    }
    if (!isRecording) {
      for (const sid of Array.from(selectedSourceIds)) {
        if (!allActiveIds.has(sid)) {
          const misses = (missedSourcePolls.get(sid) || 0) + 1;
          missedSourcePolls.set(sid, misses);
          if (misses >= 2) {
            selectedSourceIds.delete(sid);
            missedSourcePolls.delete(sid);
            selectionChanged = true;
          }
        }
      }
    }

    renderSourcesList(appsListEl, apps, 'app');
    renderSourcesList(micsListEl, mics, 'mic');

    if (window.visualizerEngine) {
      window.visualizerEngine.pruneCanvases(allActiveIds);
    }

    updateArmedCount();
    if (selectionChanged) {
      syncArmedSources();
    }
  } catch (err) {
    console.error('Error fetching sources:', err);
  }
}

function buildSourceMetaHtml(src, isArmed) {
  const isApp = src.type === 'app';
  const parts = [];
  if (src.pid) {
    parts.push(`<span class="tag-pid">PID: ${escapeHtml(src.pid)}</span>`);
  }
  if (isApp && src.stream_count > 1) {
    parts.push(`<span class="tag-streams">${escapeHtml(t('streamsTag', { count: src.stream_count }))}</span>`);
  }
  if (!isApp) {
    if (src.is_bluetooth) {
      parts.push(`<span class="tag-bt" title="${escapeHtml(t('btTitle'))}">${escapeHtml(t('btTag'))}</span>`);
    } else if (!isArmed) {
      parts.push(`<span class="tag-mic" title="${escapeHtml(t('micArmedTitle'))}">${escapeHtml(t('micArmedHint'))}</span>`);
    } else {
      parts.push(`<span class="tag-mic">${escapeHtml(t('micActive'))}</span>`);
    }
  }
  const chLabel = src.channels === 1 ? 'Mono' : 'Stereo';
  const khz = Math.round((src.sample_rate || 48000) / 1000);
  parts.push(`<span class="tag-specs">${chLabel} • ${khz}kHz</span>`);
  return parts.join('');
}

// Render Source Cards
function renderSourcesList(container, sources, type) {
  if (sources.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <p>${escapeHtml(type === 'app' ? t('noApps') : t('noMics'))}</p>
      </div>
    `;
    return;
  }

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
    sources.forEach(src => {
      const card = container.querySelector(`[data-source-id="${CSS.escape(src.id)}"]`);
      if (card) {
        const checkbox = card.querySelector('.custom-checkbox');
        const isArmed = selectedSourceIds.has(src.id);
        checkbox.checked = isArmed;
        card.classList.toggle('selected', isArmed);
        const nameEl = card.querySelector('.source-name');
        if (nameEl) {
          nameEl.textContent = src.name;
          nameEl.title = src.name;
        }
        const metaEl = card.querySelector('.source-meta');
        if (metaEl) {
          metaEl.innerHTML = buildSourceMetaHtml(src, isArmed);
        }
        const armBtn = card.querySelector('.arm-btn');
        if (armBtn) {
          armBtn.title = t('armTitle');
        }
      }
    });
  }
}

function createSourceCard(src) {
  const card = document.createElement('div');
  const isArmed = selectedSourceIds.has(src.id);
  card.className = 'source-card' + (isArmed ? ' selected' : '');
  card.dataset.sourceId = src.id;

  const isApp = src.type === 'app';
  const iconEmoji = isApp ? '🎵' : (src.is_bluetooth ? '🎧' : '🎙️');
  const safeName = escapeHtml(src.name);
  const safeCanvasId = `canvas_${escapeHtml(String(src.id).replace(/[^a-zA-Z0-9_-]/g, '_'))}`;

  card.innerHTML = `
    <div class="source-avatar">${iconEmoji}</div>
    <div class="source-info">
      <div class="source-name" title="${safeName}">${safeName}</div>
      <div class="source-meta">${buildSourceMetaHtml(src, isArmed)}</div>
    </div>
    <div class="meter-container">
      <div class="meter-labels">
        <span>-36</span>
        <span>-24</span>
        <span>-12</span>
        <span>-6</span>
        <span>0dB</span>
      </div>
      <canvas class="meter-canvas" id="${safeCanvasId}"></canvas>
    </div>
    <div class="checkbox-wrapper">
      <input type="checkbox" class="custom-checkbox" ${isArmed ? 'checked' : ''}>
      <button type="button" class="arm-btn" title="${escapeHtml(t('armTitle'))}">
        <span class="arm-dot"></span>
        <span class="arm-text">ARM</span>
      </button>
    </div>
  `;

  card.addEventListener('click', () => {
    const checkbox = card.querySelector('.custom-checkbox');
    checkbox.checked = !checkbox.checked;
    const nowArmed = checkbox.checked;

    if (nowArmed) {
      selectedSourceIds.add(src.id);
      card.classList.add('selected');
    } else {
      selectedSourceIds.delete(src.id);
      card.classList.remove('selected');
    }
    const metaEl = card.querySelector('.source-meta');
    if (metaEl) {
      metaEl.innerHTML = buildSourceMetaHtml(src, nowArmed);
    }
    updateArmedCount();
    syncArmedSources();
  });

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
  syncArmedSources();
}

function updateArmedCount() {
  armedCountEl.textContent = selectedSourceIds.size;
  if (!isRecording) {
    recBadgeEl.textContent = selectedSourceIds.size > 0
      ? t('statusArmedCount', { count: selectedSourceIds.size })
      : t('statusWaiting');
  }
}

// WebSocket Connection
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const token = getApiToken();
  const qs = token ? `?token=${encodeURIComponent(token)}` : '';
  const wsUrl = `${protocol}//${window.location.host}/ws${qs}`;

  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    isWsConnected = true;
    wsStatusEl.classList.remove('disconnected');
    wsStatusEl.querySelector('.status-text').textContent = t('connected');
    if (reconnectTimer) {
      clearInterval(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'audio_meters') {
        if (data.peaks && window.visualizerEngine) {
          for (const [sourceId, level] of Object.entries(data.peaks)) {
            window.visualizerEngine.updatePeak(sourceId, level);
          }
        }
        if (data.recording) {
          syncRecordingState(data.recording);
        }
      }
    } catch (e) {
      console.error('WS parse error:', e);
    }
  };

  ws.onclose = () => {
    isWsConnected = false;
    wsStatusEl.classList.add('disconnected');
    wsStatusEl.querySelector('.status-text').textContent = t('disconnected');
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
    lastSeenReconnections = rec.reconnections || 0;
    btnRecordToggle.classList.add('recording');
    recordBtnLabel.textContent = t('stopRecord');
    recBadgeEl.className = 'rec-status-badge active';
    recBadgeEl.textContent = t('statusRecording');
    setControlsLocked(true);
  } else if (!rec.is_recording && isRecording) {
    isRecording = false;
    lastSeenReconnections = 0;
    btnRecordToggle.classList.remove('recording');
    recordBtnLabel.textContent = t('startRecord');
    recBadgeEl.className = 'rec-status-badge idle';
    recBadgeEl.textContent = selectedSourceIds.size > 0
      ? t('statusArmedCount', { count: selectedSourceIds.size })
      : t('statusReady');
    setControlsLocked(false);
  }

  if (rec.is_recording) {
    if (rec.duration_secs !== undefined) {
      recTimerEl.textContent = formatDuration(rec.duration_secs);
    }
    const reconn = rec.reconnections || 0;
    if (reconn > lastSeenReconnections) {
      lastSeenReconnections = reconn;
      const latestWarning =
        (rec.warnings && rec.warnings.length > 0)
          ? rec.warnings[rec.warnings.length - 1]
          : t('streamRestoredDefault');
      showToast({
        title: t('streamRestoredTitle', { count: reconn }),
        details: latestWarning,
        variant: 'info',
        durationMs: 4500
      });
    }
  }
}

function setControlsLocked(locked) {
  if (btnOpenSettings) {
    btnOpenSettings.disabled = locked;
    btnOpenSettings.title = locked ? t('settingsLockedTitle') : t('settingsTitle');
  }
  if (quickModeToggle) {
    quickModeToggle.disabled = locked;
  }
  if (quickSettingsBox) {
    quickSettingsBox.classList.toggle('is-disabled', locked);
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
      showToast({
        title: t('noSourcesTitle'),
        details: t('noSourcesDesc'),
        variant: 'warning',
        durationMs: 4000
      });
      return;
    }

    try {
      const res = await apiFetch('/api/record/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_ids: Array.from(selectedSourceIds),
          format: currentConfig.format,
          bitrate: currentConfig.bitrate,
          sample_rate: currentConfig.sample_rate,
          mode: currentConfig.mode
        })
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast({
          title: t('startFailedTitle'),
          details: err.detail || t('unknownServerErr'),
          variant: 'error'
        });
      }
    } catch (err) {
      showToast({
        title: t('startErrTitle'),
        details: String(err),
        variant: 'error'
      });
    }
  } else {
    recBadgeEl.textContent = t('statusFinalizing');
    btnRecordToggle.disabled = true;
    try {
      const res = await apiFetch('/api/record/stop', { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showCompletionToast(data);
      } else {
        showToast({
          title: t('stopFailedTitle'),
          details: data.detail || t('stopFailedFallback'),
          variant: 'error',
          showOpenFolder: true
        });
      }
    } catch (err) {
      showToast({
        title: t('stopErrTitle'),
        details: String(err),
        variant: 'error'
      });
    } finally {
      btnRecordToggle.disabled = false;
    }
  }
}

function showCompletionToast(data) {
  const sizeLabel = formatBytes(data.total_bytes || 0);
  const warnings = data.warnings || [];
  let details = t('recSavedDetails', {
    dur: formatDuration(data.duration_secs || 0),
    size: sizeLabel,
    files: (data.output_files || []).length
  });
  if (data.reconnections > 0) {
    details += t('recSavedReconn', { count: data.reconnections });
  }
  if (warnings.length > 0) {
    details += ` (${warnings[warnings.length - 1]})`;
  }

  showToast({
    title: warnings.length > 0 ? t('recSavedWarnTitle') : t('recSavedTitle'),
    details,
    variant: warnings.length > 0 ? 'warning' : 'success',
    showOpenFolder: true
  });
}

// Folder Actions
async function openFolder(path = null) {
  try {
    const res = await apiFetch('/api/open-folder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(path ? { path } : {})
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      showToast({
        title: t('openDirErrTitle'),
        details: err.detail || t('openDirErrDesc'),
        variant: 'error',
        durationMs: 4000
      });
    }
  } catch (err) {
    console.error('Error opening folder:', err);
  }
}

async function pickFolder() {
  btnOpenFolderPicker.disabled = true;
  try {
    const res = await apiFetch('/api/pick-folder', { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      if (data.selected && data.path) {
        settingOutputDir.value = data.path;
      }
    }
  } catch (err) {
    showToast({
      title: t('pickerErrTitle'),
      details: String(err),
      variant: 'error',
      durationMs: 4000
    });
  } finally {
    btnOpenFolderPicker.disabled = false;
  }
}

// Settings Modal
function openSettings() {
  if (isRecording) return;
  const fmtRadio = document.querySelector(`input[name="audioFormat"][value="${currentConfig.format}"]`);
  if (fmtRadio) fmtRadio.checked = true;
  const modeRadio = document.querySelector(`input[name="recordMode"][value="${currentConfig.mode}"]`);
  if (modeRadio) modeRadio.checked = true;

  settingBitrate.value = currentConfig.bitrate || '320k';
  settingSampleRate.value = String(currentConfig.sample_rate || 48000);
  settingOutputDir.value = currentConfig.output_dir || '';
  updateBitrateVisibility(currentConfig.format);
  settingsModal.style.display = 'flex';
}

function closeSettings() {
  settingsModal.style.display = 'none';
}

async function saveSettings() {
  const format = document.querySelector('input[name="audioFormat"]:checked').value;
  const mode = document.querySelector('input[name="recordMode"]:checked').value;
  const bitrate = settingBitrate.value;
  const sample_rate = parseInt(settingSampleRate.value, 10) || 48000;
  const output_dir = settingOutputDir.value.trim();

  if (!output_dir) {
    showToast({
      title: t('invalidPathTitle'),
      details: t('invalidPathDesc'),
      variant: 'warning',
      durationMs: 3500
    });
    return;
  }

  try {
    const res = await apiFetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ format, mode, bitrate, sample_rate, output_dir })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showToast({
        title: t('saveSettingsErrTitle'),
        details: data.detail || t('saveSettingsErrDesc'),
        variant: 'error',
        durationMs: 5000
      });
      return;
    }

    currentConfig = data;
    updateModeDisplay();
    closeSettings();
  } catch (err) {
    showToast({
      title: t('saveSettingsErrTitle'),
      details: String(err),
      variant: 'error'
    });
  }
}

// Recordings History Modal
async function openHistoryModal() {
  historyModal.style.display = 'flex';
  await loadHistoryList();
}

function closeHistoryModal() {
  historyModal.style.display = 'none';
}

async function loadHistoryList() {
  historyListEl.innerHTML = `
    <div class="empty-state">
      <div class="spinner"></div>
      <p>${escapeHtml(t('loadingHistory'))}</p>
    </div>
  `;

  try {
    const res = await apiFetch('/api/recordings');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    const items = data.recordings || [];

    if (items.length === 0) {
      historyListEl.innerHTML = `
        <div class="empty-state">
          <p>${escapeHtml(t('noHistory'))}</p>
        </div>
      `;
      return;
    }

    historyListEl.innerHTML = '';
    const dateLocale = currentLang === 'uk' ? 'uk-UA' : 'en-US';
    for (const item of items) {
      const row = document.createElement('div');
      row.className = 'recording-row';
      const dateStr = new Date((item.modified || 0) * 1000).toLocaleString(dateLocale);
      const kindBadge = item.is_dir ? t('kindDir') : t('kindFile');

      row.innerHTML = `
        <div class="recording-info">
          <div class="recording-name" title="${escapeHtml(item.name)}">${item.is_dir ? '📁 ' : '🎵 '}${escapeHtml(item.name)}</div>
          <div class="recording-meta">${escapeHtml(kindBadge)} • ${escapeHtml(formatBytes(item.size_bytes))} • ${escapeHtml(dateStr)}</div>
        </div>
        <div class="recording-actions">
          <button type="button" class="btn btn-xs btn-secondary btn-rec-open">${escapeHtml(t('openBtn'))}</button>
          <button type="button" class="btn btn-xs btn-danger btn-rec-delete">${escapeHtml(t('deleteBtn'))}</button>
        </div>
      `;

      row.querySelector('.btn-rec-open').addEventListener('click', () => {
        openFolder(item.path);
      });

      row.querySelector('.btn-rec-delete').addEventListener('click', async () => {
        const confirmed = await showConfirmDialog({
          title: t('deleteTitle'),
          message: t('deleteMsg', { name: item.name }),
          confirmText: t('deleteBtn'),
          danger: true
        });
        if (!confirmed) return;

        try {
          const delRes = await apiFetch(`/api/recordings/${encodeURIComponent(item.name)}`, {
            method: 'DELETE'
          });
          if (!delRes.ok) {
            const err = await delRes.json().catch(() => ({}));
            showToast({
              title: t('deleteErrTitle'),
              details: err.detail || t('deleteErrDesc'),
              variant: 'error',
              durationMs: 4000
            });
            return;
          }
          await loadHistoryList();
        } catch (err) {
          showToast({
            title: t('deleteErrTitle'),
            details: String(err),
            variant: 'error',
            durationMs: 4000
          });
        }
      });

      historyListEl.appendChild(row);
    }
  } catch (err) {
    historyListEl.innerHTML = `
      <div class="empty-state">
        <p>${escapeHtml(t('historyErr', { err }))}</p>
      </div>
    `;
  }
}
