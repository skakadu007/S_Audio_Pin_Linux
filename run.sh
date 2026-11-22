#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python" -m s_audio_pin.main "$@"
elif command -v uv >/dev/null 2>&1; then
    exec uv run s-audio-pin "$@"
else
    exec python3 -m s_audio_pin.main "$@"
fi
