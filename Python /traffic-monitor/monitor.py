#!/usr/bin/env python3
"""
Lightweight live top-talkers dashboard powered by tshark (Wireshark CLI).

Designed for low-resource MacBooks: short capture windows, header-only snaplen,
no DNS lookups, and a terminal UI (no Wireshark GUI).
"""

from __future__ import annotations

import argparse
import collections
import os
import random
import shutil
import signal
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple

# ANSI
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
CLEAR = "\033[2J\033[H"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"

RUNNING = True


def _on_signal(_signum: int, _frame: object) -> None:
    global RUNNING
    RUNNING = False


def format_bytes(n: float) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{value:.1f} TB"


def format_rate(bytes_per_sec: float) -> str:
    return f"{format_bytes(bytes_per_sec)}/s"


def heat_color(share: float) -> str:
    """Color by share of total traffic in the window (0..1)."""
    if share >= 0.35:
        return RED
    if share >= 0.15:
        return YELLOW
    if share >= 0.05:
        return GREEN
    return DIM


def bar(share: float, width: int = 28) -> str:
    filled = max(0, min(width, int(round(share * width))))
    return "█" * filled + "░" * (width - filled)


def find_tshark() -> Optional[str]:
    path = shutil.which("tshark")
    if path:
        return path
    # Common Homebrew Wireshark locations on Apple Silicon / Intel Macs
    for candidate in (
        "/opt/homebrew/bin/tshark",
        "/usr/local/bin/tshark",
        "/Applications/Wireshark.app/Contents/MacOS/tshark",
    ):
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None


def default_interface() -> str:
    """Prefer Wi-Fi-ish names; fall back to first non-loopback listing."""
    tshark = find_tshark()
    if not tshark:
        return "en0"
    try:
        out = subprocess.check_output(
            [tshark, "-D"],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return "en0"

    names: List[str] = []
    for line in out.splitlines():
        # e.g. "1. en0 (Wi-Fi)" or "1. eth0"
        parts = line.split(maxsplit=1)
        if len(parts) < 2:
            continue
        name = parts[1].split()[0]
        names.append(name)

    preferred = ("en0", "en1", "wlan0", "eth0")
    for name in preferred:
        if name in names:
            return name
    for name in names:
        if name not in ("lo", "lo0", "any"):
            return name
    return names[0] if names else "en0"


def capture_window(
    tshark: str,
    interface: str,
    duration: float,
    snaplen: int,
) -> Dict[str, int]:
    """
    Capture for `duration` seconds and return bytes per endpoint IP.
    Uses header-only snaplen and field export — not full packet dissection.
    """
    cmd = [
        tshark,
        "-i",
        interface,
        "-a",
        f"duration:{max(1, int(round(duration)))}",
        "-n",  # no name resolution (saves CPU / DNS)
        "-l",
        "-s",
        str(snaplen),
        "-T",
        "fields",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "frame.len",
        "-E",
        "separator=\t",
    ]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=duration + 8,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {}
    except OSError as exc:
        print(f"{RED}Failed to run tshark: {exc}{RESET}", file=sys.stderr)
        return {}

    if proc.returncode not in (0,):
        # tshark sometimes exits non-zero on empty captures; still parse stdout
        err = (proc.stderr or "").strip()
        if err and "permission" in err.lower():
            print(
                f"{RED}Permission denied capturing on {interface}.{RESET}\n"
                f"{DIM}On macOS: install Wireshark, then log out/in after BPF "
                f"group setup, or run once with sudo.{RESET}",
                file=sys.stderr,
            )
            raise SystemExit(2)

    totals: Dict[str, int] = collections.defaultdict(int)
    for line in (proc.stdout or "").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        src, dst, length_s = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not length_s:
            continue
        try:
            length = int(length_s)
        except ValueError:
            continue
        if src:
            totals[src] += length
        if dst and dst != src:
            totals[dst] += length
    return dict(totals)


def mock_window() -> Dict[str, int]:
    """Synthetic traffic so the UI can be tested without capture privileges."""
    hosts = [
        "142.250.72.14",  # google-ish
        "104.16.132.229",  # cloudflare
        "13.107.42.14",  # microsoft
        "1.1.1.1",
        "192.168.1.1",
        "192.168.1.42",
        "17.253.144.10",  # apple
        "52.94.236.248",  # aws
    ]
    totals: Dict[str, int] = {}
    # One host dominates so heat coloring is visible
    heavy = random.choice(hosts[:4])
    for host in hosts:
        base = random.randint(2_000, 80_000)
        totals[host] = base
    totals[heavy] += random.randint(400_000, 1_200_000)
    return totals


def render(
    totals: Dict[str, int],
    duration: float,
    interface: str,
    top_n: int,
    mock: bool,
    history: collections.deque,
) -> str:
    ranked: List[Tuple[str, int]] = sorted(
        totals.items(), key=lambda item: item[1], reverse=True
    )[:top_n]
    total_bytes = sum(totals.values()) or 1
    rate = total_bytes / max(duration, 0.001)

    lines: List[str] = []
    mode = "MOCK" if mock else "LIVE"
    lines.append(
        f"{BOLD}{CYAN}Traffic Monitor{RESET}  "
        f"{DIM}[{mode}]{RESET}  iface={BOLD}{interface}{RESET}  "
        f"window={duration:.0f}s  total={BOLD}{format_rate(rate)}{RESET}"
    )
    lines.append(
        f"{DIM}Heavy talkers highlighted · header-only capture · Ctrl+C to quit{RESET}"
    )
    lines.append("")
    lines.append(
        f"{DIM}{'#':>3}  {'ENDPOINT':<18}  {'BYTES':>10}  {'RATE':>12}  "
        f"{'SHARE':>6}  LOAD{RESET}"
    )

    for idx, (host, nbytes) in enumerate(ranked, start=1):
        share = nbytes / total_bytes
        color = heat_color(share)
        host_rate = nbytes / max(duration, 0.001)
        marker = " ◀ HEAVY" if share >= 0.35 else (" ◀ busy" if share >= 0.15 else "")
        lines.append(
            f"{color}{idx:>3}  {host:<18}  {format_bytes(nbytes):>10}  "
            f"{format_rate(host_rate):>12}  {share * 100:5.1f}%  "
            f"{bar(share)}{marker}{RESET}"
        )

    if not ranked:
        lines.append(f"{DIM}  (no IPv4 traffic in this window){RESET}")

    # Tiny sparkline of recent window totals
    if history:
        peak = max(history) or 1
        spark = "".join("▁▂▃▄▅▆▇█"[min(7, int(v / peak * 7))] for v in history)
        lines.append("")
        lines.append(f"{DIM}recent windows: {RESET}{CYAN}{spark}{RESET}")

    lines.append("")
    lines.append(
        f"{DIM}tip: open a pcap in Wireshark GUI only when you need deep packet detail{RESET}"
    )
    return "\n".join(lines)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Low-CPU live top-talkers dashboard using tshark."
    )
    parser.add_argument(
        "-i",
        "--interface",
        default=None,
        help="Capture interface (default: auto, usually en0 on Mac Wi-Fi)",
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=5.0,
        help="Seconds per sample window (default: 5). Higher = less CPU.",
    )
    parser.add_argument(
        "-n",
        "--top",
        type=int,
        default=12,
        help="How many talkers to show (default: 12)",
    )
    parser.add_argument(
        "-s",
        "--snaplen",
        type=int,
        default=96,
        help="Bytes per packet to capture (default: 96 headers-only)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Synthetic data (no capture) — useful for UI testing",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single window and exit",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    tshark = find_tshark()
    if not args.mock and not tshark:
        print(
            f"{RED}tshark not found.{RESET}\n"
            "Install Wireshark CLI on macOS:\n"
            "  brew install wireshark\n"
            "Then re-run this script (or use --mock to preview the UI).",
            file=sys.stderr,
        )
        return 1

    interface = args.interface or (default_interface() if not args.mock else "en0")
    history: collections.deque = collections.deque(maxlen=24)

    sys.stdout.write(HIDE_CURSOR)
    sys.stdout.flush()
    try:
        while RUNNING:
            started = time.monotonic()
            if args.mock:
                time.sleep(min(args.duration, 1.5) if not args.once else 0)
                totals = mock_window()
            else:
                assert tshark is not None
                totals = capture_window(
                    tshark, interface, args.duration, args.snaplen
                )

            history.append(sum(totals.values()))
            frame = render(
                totals,
                args.duration,
                interface,
                args.top,
                args.mock,
                history,
            )
            sys.stdout.write(CLEAR + frame + "\n")
            sys.stdout.flush()

            if args.once:
                break

            # If capture returned early, avoid a tight spin
            elapsed = time.monotonic() - started
            if elapsed < 0.4:
                time.sleep(0.4 - elapsed)
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
        sys.stdout.flush()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
