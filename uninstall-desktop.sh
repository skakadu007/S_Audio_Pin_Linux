#!/usr/bin/env bash
set -e

APP_ID="io.github.skakadu007.SAudioPin"
APPS_DIR="$HOME/.local/share/applications"
HICOLOR_DIR="$HOME/.local/share/icons/hicolor"

rm -f \
    "$APPS_DIR/${APP_ID}.desktop" \
    "$APPS_DIR/s-audio-pin.desktop" \
    "$APPS_DIR/s_audio_pin.desktop" \
    "$APPS_DIR/127.0.0.1__.desktop"

rm -f \
    "$HICOLOR_DIR/scalable/apps/${APP_ID}.svg" \
    "$HICOLOR_DIR/scalable/apps/s-audio-pin.svg" \
    "$HICOLOR_DIR/scalable/apps/s_audio_pin.svg" \
    "$HICOLOR_DIR/scalable/apps/127.0.0.1.svg" \
    "$HOME/.local/share/icons/s-audio-pin.svg" \
    "$HOME/.local/share/icons/s_audio_pin.svg"

for size in 48 64 128 256 512; do
    DIR="$HICOLOR_DIR/${size}x${size}/apps"
    rm -f \
        "$DIR/${APP_ID}.png" \
        "$DIR/s-audio-pin.png" \
        "$DIR/s_audio_pin.png" \
        "$DIR/127.0.0.1.png" \
        "$DIR/127.0.0.1__.png"
done

rm -f "$HOME/.local/bin/s-audio-pin"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HICOLOR_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "S_Audio_Pin видалено з системного меню."
