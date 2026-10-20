#!/bin/bash
# Double-click in Finder on your MacBook, or run from Terminal.
cd "$(dirname "$0")"

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

if ! command -v python3 >/dev/null 2>&1; then
  osascript -e 'display alert "Python 3 is required" message "Install Python 3 from python.org or: brew install python"' >/dev/null 2>&1 || true
  echo "Python 3 not found. Install with: brew install python"
  read -r -p "Press Enter to close…"
  exit 1
fi

# Prefer Wi-Fi; fall back to auto-detect inside monitor.py
IFACE="${TRAFFIC_IFACE:-en0}"
DURATION="${TRAFFIC_DURATION:-5}"

echo "Starting Traffic Monitor on $IFACE (window=${DURATION}s). Ctrl+C to stop."
echo "Tip: TRAFFIC_DURATION=8 ./Run\\ Traffic\\ Monitor.command  # quieter on CPU"
echo

exec python3 monitor.py -i "$IFACE" -d "$DURATION"
