# PiZero OpenClaw Device

## Hardware
- **Raspberry Pi Zero 2 WH** (pre-soldered headers) at `pizero.local` / `192.168.1.15`
- **PiSugar WhisPlay HAT** — 1.69" LCD (240x280), speaker, mic, 1 button (push-to-talk)
- **PiSugar 3 battery** (1200mAh)
- **32GB SanDisk microSD**

## Access
- SSH: `ssh pi@pizero.local` (key-based auth from MacBook, password: `raspberry`)
- Diane (OpenClaw AI on Mac mini) also has SSH access to the Pi
- Service: `sudo systemctl restart pizero-openclaw`
- Logs: `sudo journalctl -u pizero-openclaw -f` or `/tmp/openclaw.log`

## Software Stack
- Raspberry Pi OS Bookworm Desktop 64-bit
- Project code at `/home/pi/pizero-openclaw/`
- WhisPlay drivers at `/home/pi/Whisplay/Driver/`
- systemd service `pizero-openclaw` — auto-starts on boot

## OpenClaw Gateway
- Runs on Mac mini at `192.168.1.5:18789` (user: `petercrouch`)
- Bind mode: `lan` (listening on all interfaces)
- Diane manages this — reachable via Discord or email (yuncunstest@gmail.com)

## Key Modifications from Upstream
- `openclaw_client.py` — patched to use `/v1/chat/completions` instead of `/v1/responses` (gateway uses Chat Completions API, not the newer Responses API)
- `button_ptt.py` — added `RESPONSE` state with tap-to-scroll, wake-without-record, hold-to-talk (400ms threshold)
- `display.py` — added page scrolling with wrap-around + page indicator, improved idle screen (WiFi signal, SSID, IP, color-coded battery)
- `main.py` — wired up tap-to-scroll, wake detection, RESPONSE state

## Button Behavior
- **Screen sleeping** → tap to wake (does NOT start recording)
- **Idle screen** → hold to talk (push-to-talk)
- **Response showing** → tap to scroll pages (wraps around), hold to start new recording
- **Kirby talking** → tap to cancel TTS

## Config (.env on the Pi)
- TTS voice: `coral` (changeable: alloy, echo, fable, onyx, nova, shimmer)
- TTS speed: 1.1, gain: 9dB
- Speaker volume: 60% via `amixer -c 1 sset 'Speaker' 60%`
- LCD backlight: 70%
- Conversation history: 5 exchanges

## WiFi Networks Configured
- `NETGEARC3D3B3` (home)
- `Pixel_8102` (phone hotspot)

## Deploy Workflow
1. Edit files locally or via SSH
2. `scp` changed files to `pi@pizero.local:/home/pi/pizero-openclaw/`
3. `ssh pi@pizero.local "sudo systemctl restart pizero-openclaw"`
4. Push to this repo to keep changes tracked

## Troubleshooting
- **405 error** — gateway endpoint mismatch, we patched to use `/v1/chat/completions`
- **WAV file too small** — button press was too short, or wake-without-record isn't working
- **No display on boot** — normal until service starts; display only works when main.py runs
- **Charge via PiSugar USB port**, not the Pi's USB port
- **Speaker JST connector** comes loose — check if audio stops
- **Pi not on network** — mDNS can be flaky, try `ssh pi@192.168.1.15` directly
