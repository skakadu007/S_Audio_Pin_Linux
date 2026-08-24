#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON_SRC="$SCRIPT_DIR/assets/icon.svg"
RUN_SCRIPT="$SCRIPT_DIR/run.sh"

APPS_DIR="$HOME/.local/share/applications"
HICOLOR_DIR="$HOME/.local/share/icons/hicolor"
BIN_DIR="$HOME/.local/bin"

mkdir -p "$APPS_DIR" "$BIN_DIR"

# Clean old entries first
rm -f "$APPS_DIR/s-audio-pin.desktop" "$APPS_DIR/s_audio_pin.desktop" "$APPS_DIR/127.0.0.1__.desktop"

# 1. Install SVG scalable icon
mkdir -p "$HICOLOR_DIR/scalable/apps"
cp "$ICON_SRC" "$HICOLOR_DIR/scalable/apps/s-audio-pin.svg"
cp "$ICON_SRC" "$HICOLOR_DIR/scalable/apps/s_audio_pin.svg"
cp "$ICON_SRC" "$HICOLOR_DIR/scalable/apps/127.0.0.1.svg" 2>/dev/null || true
cp "$ICON_SRC" "$HOME/.local/share/icons/s-audio-pin.svg" 2>/dev/null || true
cp "$ICON_SRC" "$HOME/.local/share/icons/s_audio_pin.svg" 2>/dev/null || true

# 2. Install multi-resolution PNG icons for Dock, Panel, and Alt-Tab switcher
for size in 48 64 128 256 512; do
    DIR="$HICOLOR_DIR/${size}x${size}/apps"
    mkdir -p "$DIR"
    if [ -f "$SCRIPT_DIR/assets/icon_${size}.png" ]; then
        cp "$SCRIPT_DIR/assets/icon_${size}.png" "$DIR/s-audio-pin.png"
        cp "$SCRIPT_DIR/assets/icon_${size}.png" "$DIR/s_audio_pin.png"
        cp "$SCRIPT_DIR/assets/icon_${size}.png" "$DIR/127.0.0.1.png"
        cp "$SCRIPT_DIR/assets/icon_${size}.png" "$DIR/127.0.0.1__.png"
    fi
done

# 3. Install CLI symlink
ln -sf "$RUN_SCRIPT" "$BIN_DIR/s-audio-pin"

# 4. Create primary .desktop file (The ONLY one visible in App Menu)
cat > "$APPS_DIR/s-audio-pin.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=S_Audio_Pin
GenericName=Audio Process Monitor & Recorder
GenericName[uk]=Моніторинг процесів та запис аудіо
Comment=Monitor audio-playing processes and selectively record applications and microphones
Comment[uk]=Моніторинг процесів зі звуком та вибірковий запис програм і мікрофонів
Exec=$RUN_SCRIPT
Icon=s-audio-pin
Terminal=false
Categories=AudioVideo;Audio;Recorder;
Keywords=audio;sound;record;process;microphone;vu;pipewire;pulseaudio;
StartupNotify=true
StartupWMClass=s_audio_pin
EOF

chmod +x "$APPS_DIR/s-audio-pin.desktop"

# 5. Hidden alias desktop files for Wayland/GNOME WM_CLASS window matching (NoDisplay=true)
cat > "$APPS_DIR/s_audio_pin.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=S_Audio_Pin
Exec=$RUN_SCRIPT
Icon=s-audio-pin
Terminal=false
NoDisplay=true
StartupWMClass=s_audio_pin
EOF

cat > "$APPS_DIR/127.0.0.1__.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=S_Audio_Pin
Exec=$RUN_SCRIPT
Icon=s-audio-pin
Terminal=false
NoDisplay=true
StartupWMClass=127.0.0.1__
EOF

# 6. Update icon cache and desktop database
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HICOLOR_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "============================================================"
echo "  🎉 S_Audio_Pin успішно налаштовано!"
echo "============================================================"
echo "• У меню програм тепер РІВНО ОДНА іконка S_Audio_Pin."
echo "• Налаштовано приховані мапінги WM_CLASS для панелі та Alt+Tab."
echo "============================================================"
