#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_ID="io.github.skakadu007.S_Audio_Pin_Linux"
ICON_SRC="$SCRIPT_DIR/assets/icon.svg"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

APPS_DIR="$HOME/.local/share/applications"
HICOLOR_DIR="$HOME/.local/share/icons/hicolor"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$APPS_DIR" "$BIN_DIR"
chmod +x "$RUN_SCRIPT"

# Clean legacy desktop entries & icon aliases
rm -f \
    "$APPS_DIR/s-audio-pin.desktop" \
    "$APPS_DIR/s_audio_pin.desktop" \
    "$APPS_DIR/127.0.0.1__.desktop" \
    "$APPS_DIR/io.github.skakadu007.SAudioPin.desktop" \
    "$APPS_DIR/${APP_ID}.desktop"

rm -f \
    "$HICOLOR_DIR/scalable/apps/s_audio_pin.svg" \
    "$HICOLOR_DIR/scalable/apps/127.0.0.1.svg" \
    "$HICOLOR_DIR/scalable/apps/io.github.skakadu007.SAudioPin.svg" \
    "$HOME/.local/share/icons/s_audio_pin.svg"

for size in 48 64 128 256 512; do
    DIR="$HICOLOR_DIR/${size}x${size}/apps"
    rm -f \
        "$DIR/s_audio_pin.png" \
        "$DIR/127.0.0.1.png" \
        "$DIR/127.0.0.1__.png" \
        "$DIR/io.github.skakadu007.SAudioPin.png"
done

# 1. Install SVG scalable icon
mkdir -p "$HICOLOR_DIR/scalable/apps"
cp "$ICON_SRC" "$HICOLOR_DIR/scalable/apps/${APP_ID}.svg"

# 2. Install multi-resolution PNG icons
for size in 48 64 128 256 512; do
    DIR="$HICOLOR_DIR/${size}x${size}/apps"
    mkdir -p "$DIR"
    if [ -f "$SCRIPT_DIR/assets/icon_${size}.png" ]; then
        cp "$SCRIPT_DIR/assets/icon_${size}.png" "$DIR/${APP_ID}.png"
    fi
done

# 3. Install CLI symlink
ln -sf "$RUN_SCRIPT" "$BIN_DIR/s-audio-pin"

# 4. Install single clean .desktop file matching GTK application_id
cat > "$APPS_DIR/${APP_ID}.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=S_Audio_Pin
GenericName=Audio Process Monitor & Recorder
GenericName[uk]=Моніторинг процесів та запис аудіо
Comment=Monitor audio-playing processes and selectively record applications and microphones
Comment[uk]=Моніторинг процесів зі звуком та вибірковий запис програм і мікрофонів
Exec=$RUN_SCRIPT
Icon=${APP_ID}
Terminal=false
Categories=AudioVideo;Audio;Recorder;
Keywords=audio;sound;record;process;microphone;vu;pipewire;pulseaudio;
StartupNotify=true
StartupWMClass=${APP_ID}
EOF

chmod +x "$APPS_DIR/${APP_ID}.desktop"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HICOLOR_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "============================================================"
echo "  S_Audio_Pin успішно встановлено!"
echo "============================================================"
echo "• Desktop entry: $APPS_DIR/${APP_ID}.desktop"
echo "• CLI команда:   $BIN_DIR/s-audio-pin"
echo "============================================================"
