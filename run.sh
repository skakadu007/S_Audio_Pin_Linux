#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "$SCRIPT_DIR/.venv/bin/python" ]; then
    exec "$SCRIPT_DIR/.venv/bin/python" -m src.main "$@"
elif command -v uv >/dev/null 2>&1; then
    exec uv run python -m src.main "$@"
else
    exec python3 -m src.main "$@"
fi
