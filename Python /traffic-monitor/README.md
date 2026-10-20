# Traffic Monitor (MacBook-compatible, low CPU)

Live **top-talkers** dashboard built for a MacBook Pro (including **8 GB RAM**). It uses **tshark** (Wireshark’s CLI) with short sample windows and header-only captures — not the Wireshark GUI — so the machine stays usable.

Heavy endpoints are colored and marked so the busiest traffic stands out.

**Runs on:** macOS (Apple Silicon or Intel) with Python 3 + Wireshark/`tshark`.  
**Also works on:** Linux if `tshark` is installed (same `monitor.py`).

## Quick start on your MacBook

```bash
cd "Python /traffic-monitor"
chmod +x setup-mac.sh "Run Traffic Monitor.command" monitor.py
./setup-mac.sh
./Run\ Traffic\ Monitor.command
```

Or from Terminal only:

```bash
./setup-mac.sh
python3 monitor.py -i en0
```

Finder option: after `chmod +x`, double-click **`Run Traffic Monitor.command`**.

### Keep CPU low on 8 GB RAM

```bash
python3 monitor.py -i en0 -d 8
# or:
TRAFFIC_DURATION=8 ./Run\ Traffic\ Monitor.command
```

- Prefer 5–10 second windows (longer = less CPU).
- Keep default 96-byte snaplen (headers only).
- Don’t leave the Wireshark GUI open while monitoring.

## Why this instead of leaving Wireshark open

| Approach | Resource impact |
| --- | --- |
| Wireshark GUI, continuous capture | High RAM/CPU, stores full packets |
| **This script + tshark** | Short windows, 96-byte snaplen, no DNS, terminal only |
| Wireshark GUI on a saved pcap | Use only when you need deep packet inspection |

## One-time macOS setup (manual)

1. Install Homebrew if needed: https://brew.sh  
2. Install Wireshark (includes `tshark`): `brew install wireshark`  
3. If capture says permission denied: log out/in after BPF setup, or try `sudo tshark -D` once to confirm.  
4. Wi-Fi is usually `en0` — check with `tshark -D`.

## Useful options

```bash
python3 monitor.py -i en0          # Wi-Fi (typical on Mac)
python3 monitor.py -d 8            # longer window = less CPU
python3 monitor.py -n 15           # show top 15 talkers
python3 monitor.py --mock          # preview UI without capturing
python3 monitor.py --once          # one sample, then exit
```

Stop with `Ctrl+C`.

## When you need full packet detail

```bash
tshark -i en0 -a duration:30 -s 256 -w /tmp/sample.pcapng
open -a Wireshark /tmp/sample.pcapng
```

## Preview without Wireshark

```bash
python3 monitor.py --mock --once
```
