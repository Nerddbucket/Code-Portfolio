#!/bin/bash
# One-time setup for MacBook (Apple Silicon or Intel).
set -euo pipefail

echo "== Traffic Monitor · macOS setup =="

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "This setup script is for macOS. On Linux, install tshark via your package manager."
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  echo "Homebrew not found. Install it from https://brew.sh then re-run this script."
  exit 1
fi

if ! command -v tshark >/dev/null 2>&1 \
  && [[ ! -x /opt/homebrew/bin/tshark ]] \
  && [[ ! -x /usr/local/bin/tshark ]] \
  && [[ ! -x /Applications/Wireshark.app/Contents/MacOS/tshark ]]; then
  echo "Installing Wireshark (includes tshark)…"
  brew install wireshark
else
  echo "tshark already available."
fi

echo
echo "Listing capture interfaces (may prompt for permissions):"
if command -v tshark >/dev/null 2>&1; then
  TSHARK=tshark
elif [[ -x /opt/homebrew/bin/tshark ]]; then
  TSHARK=/opt/homebrew/bin/tshark
elif [[ -x /usr/local/bin/tshark ]]; then
  TSHARK=/usr/local/bin/tshark
else
  TSHARK=/Applications/Wireshark.app/Contents/MacOS/tshark
fi

if ! "$TSHARK" -D; then
  echo
  echo "Could not list interfaces. After Wireshark install, macOS often needs a logout/login"
  echo "so your account can use BPF capture devices. Then run:"
  echo "  $TSHARK -D"
  echo "Or try once with: sudo $TSHARK -D"
  exit 1
fi

echo
echo "Setup looks good."
echo "Run the dashboard with:"
echo "  ./Run\\ Traffic\\ Monitor.command"
echo "or:"
echo "  python3 monitor.py -i en0"
echo
echo "For lower CPU on 8GB RAM: python3 monitor.py -i en0 -d 8"
