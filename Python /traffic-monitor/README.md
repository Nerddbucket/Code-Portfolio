# Traffic Monitor (Mac-friendly, low CPU)

Live **top-talkers** dashboard for your MacBook. It uses **tshark** (Wireshark’s CLI) with short sample windows and header-only captures — not the Wireshark GUI — so an 8 GB MacBook stays usable.

Heavy endpoints are colored and marked so the busiest traffic stands out.

## Why this instead of leaving Wireshark open

| Approach | Resource impact |
| --- | --- |
| Wireshark GUI, continuous capture | High RAM/CPU, stores full packets |
| **This script + tshark** | Short windows, 96-byte snaplen, no DNS, terminal only |
| Wireshark GUI on a saved pcap | Use only when you need deep packet inspection |

## One-time macOS setup

1. Install Homebrew if you don’t have it: https://brew.sh  
2. Install Wireshark (includes `tshark`):

```bash
brew install wireshark
```

3. Allow packet capture (BPF). Homebrew usually prompts you; if capture fails with “permission denied”:

```bash
# After install, ensure your user can use BPF devices, then log out and back in.
# Or run the monitor once with sudo to confirm capture works:
sudo tshark -D
```

4. Confirm `tshark` is on your PATH:

```bash
tshark -v | head -1
tshark -D   # list interfaces — Wi-Fi is usually en0
```

## Run the dashboard

```bash
cd "Python /traffic-monitor"
python3 monitor.py
```

Useful options:

```bash
python3 monitor.py -i en0          # Wi-Fi (typical on Mac)
python3 monitor.py -d 8            # longer window = less CPU
python3 monitor.py -n 15           # show top 15 talkers
python3 monitor.py --mock          # preview UI without capturing
python3 monitor.py --once          # one sample, then exit
```

Stop with `Ctrl+C`.

### Keep CPU low on 8 GB RAM

- Prefer `-d 5`–`-d 10` (default is 5). Larger windows mean fewer tshark restarts.
- Keep default `-s 96` (headers only). Do not raise snaplen unless you need payloads.
- Don’t run the Wireshark GUI at the same time.
- Close other heavy apps while monitoring if the fan spins up.

## When you need full packet detail

Capture a short pcap, then open it in Wireshark:

```bash
# 30-second header-ish capture (raise -s only if you need more)
tshark -i en0 -a duration:30 -s 256 -w /tmp/sample.pcapng
open -a Wireshark /tmp/sample.pcapng
```

## Preview without Wireshark

```bash
python3 monitor.py --mock --once
```
