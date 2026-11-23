<div align="center">
  <h1>🎙️ S_Audio_Pin_Linux</h1>
  <p><strong>Lightweight Linux Desktop Audio Process Monitor & Multi-Source Pinpoint Audio Recorder</strong></p>
  <p><em>Легкий додаток для Linux: моніторинг процесів з індикаторами звуку та вибірковий запис окремих програм і мікрофонів.</em></p>
</div>

---

## 🌟 Основні можливості (Key Features)

- 🔍 **Моніторинг процесів у реальному часі**: Автоматично виявляє всі запущені програми на Linux, які відтворюють аудіо (через PipeWire / PulseAudio).
- 📊 **Живі логарифмічні VU-метри (60 FPS)**: Плавна індикація у шкалі дБ (`-36`..`0 dB`) з Peak-Hold.
- 🎧 **Захист Bluetooth A2DP та стійкий запис**:
  - Мікрофони (особливо Bluetooth `bluez_input.*`) не відкривають фонового стріму до вибору `ARM`, тому Bluetooth-навушники не перемикаються примусово у режим гарнітури HFP.
  - Під час запису при зміні пристрою виводу або перепідключенні аудіопотоку запис автоматично відновлюється без обриву файлу.
- 🎯 **Точковий вибірковий запис (Pinpoint Audio Capture)**:
  - Обирайте будь-яку кількість конкретних програм та мікрофонів.
  - Жодних зайвих системних сповіщень у записі.
- ⚙️ **Гнучкі налаштування формату**:
  - **Формати**: `MP3`, `WAV` (PCM), `FLAC` (Lossless), `OGG` (Opus).
  - **Частота**: `48000 Hz` та `44100 Hz`, бітрейт `128k`–`320k`.
  - **Режими збереження**: **Single Mix** (зведення з лімітером) або **Multitrack Stems** (синхронізовані окремі файли).
- 🖥️ **Нативне вікно GTK4 + WebKitGTK 6.0**: Працює на Wayland та X11 без залежності від зовнішнього Chrome, з нативним вибором папки через XDG Portal та історією записів.

---

## 🛠️ Встановлення та запуск (Quickstart)

### 1. Встановлення готового Flatpak-пакета з GitHub Releases (рекомендовано)
Завантажте `S_Audio_Pin_Linux-x86_64.flatpak` зі сторінки [GitHub Releases](https://github.com/skakadu007/S_Audio_Pin_Linux/releases/latest) та виконайте:
```bash
flatpak remote-add --if-not-exists --user flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user S_Audio_Pin_Linux-x86_64.flatpak
flatpak run io.github.skakadu007.S_Audio_Pin_Linux
```

### 2. Запуск з системного меню Linux (Desktop App)
```bash
./install-desktop.sh
```
Після цього знайдіть **`S_Audio_Pin`** у меню програм або запустіть із терміналу `s-audio-pin`.
Для видалення з меню: `./uninstall-desktop.sh`.

### 3. Запуск із репозиторію
```bash
uv sync
uv run s-audio-pin
```
Також доступні прапорці:
- `uv run s-audio-pin --no-window` — лише локальний сервер;
- `uv run s-audio-pin --browser` — відкрити в браузері;
- `uv run s-audio-pin --port 8765` — фіксований локальний порт.

---

## 🏗️ Архітектура проекту

```text
S_Audio_Pin_Linux/
├── src/s_audio_pin/
│   ├── models/audio.py         # Моделі даних (AudioSource, RecordingConfig, RecordingSession)
│   ├── config/settings.py      # XDG-конфігурація ($XDG_CONFIG_HOME/s-audio-pin/config.json)
│   ├── audio/
│   │   ├── monitor.py          # Моніторинг потоків PipeWire/PulseAudio без ламання Bluetooth A2DP
│   │   ├── recorder.py         # Стійкий рушій захоплення (parec -> PCM -> ffmpeg) з відновленням потоків
│   │   ├── encoder.py          # Конфігурація кодеків MP3/WAV/FLAC/OGG та зведення з alimiter
│   │   └── process_info.py     # Розпізнавання програм, групування та Bluetooth-джерел
│   ├── server/
│   │   ├── app.py              # Захищений локальний FastAPI REST API
│   │   └── ws.py               # WebSocket сервер для трансляції VU-метрів
│   ├── ui/                     # HTML/CSS/JS інтерфейс + Canvas 60fps VU-метри
│   ├── window.py               # Нативна оболонка GTK4 + WebKitGTK 6.0 та Gtk.FileDialog
│   └── main.py                 # Точка входу, вибір вільного порту та життєвий цикл
├── data/                       # .desktop та AppStream .metainfo.xml для Linux/Flathub
├── flatpak/                    # Стартовий маніфест Flatpak
└── tests/                      # Юніт- та інтеграційні тести
```

---

## 🧪 Запуск тестів

```bash
uv run pytest -v
```

---

## 📄 Ліцензія
[MIT License](LICENSE)
