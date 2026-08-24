#!/usr/bin/env bash
set -e

APPS_DIR="$HOME/.local/share/applications"
HICOLOR_DIR="$HOME/.local/share/icons/hicolor"

rm -f "$APPS_DIR/s-audio-pin.desktop"
rm -f "$APPS_DIR/s_audio_pin.desktop"
rm -f "$APPS_DIR/127.0.0.1__.desktop"

rm -f "$HICOLOR_DIR/scalable/apps/s-audio-pin.svg"
rm -f "$HICOLOR_DIR/scalable/apps/s_audio_pin.svg"
rm -f "$HICOLOR_DIR/scalable/apps/127.0.0.1.svg"
rm -f "$HOME/.local/share/icons/s-audio-pin.svg"
rm -f "$HOME/.local/share/icons/s_audio_pin.svg"

for size in 48 64 128 256 512; do
    rm -f "$HICOLOR_DIR/${size}x${size}/apps/s-audio-pin.png"
    rm -f "$HICOLOR_DIR/${size}x${size}/apps/s_audio_pin.png"
    rm -f "$HICOLOR_DIR/${size}x${size}/apps/127.0.0.1.png"
    rm -f "$HICOLOR_DIR/${size}x${size}/apps/127.0.0.1__.png"
done

rm -f "$HOME/.local/bin/s-audio-pin"

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HICOLOR_DIR" 2>/dev/null || true
fi

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPS_DIR" 2>/dev/null || true
fi

echo "S_Audio_Pin видалено з системного меню."
