#!/usr/bin/env bash
# One setup for every project in this repo: Java labs, Python labs, and the job applier.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root"

export DEBIAN_FRONTEND=noninteractive

if ! command -v javac >/dev/null 2>&1 || ! command -v java >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends openjdk-21-jdk-headless
fi

if ! command -v python3 >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y --no-install-recommends python3 python3-pip python3-venv
fi

python3 -m pip install --user -r "$root/job-applier/requirements.txt"
python3 -m playwright install chromium
python3 -m playwright install-deps chromium

echo "Ready: Java ($(javac -version 2>&1)), Python ($(python3 --version)), job applier (playwright)."
