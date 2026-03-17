# Storymode Character Integration with WhisPlay Device

*Written 2026-03-16 from the WhisPlay/device side. Intended to be read by a Claude session working in the storymode-cli or pixterm-engine repos.*

## What This Device Is

A Raspberry Pi Zero 2 WH with a PiSugar WhisPlay HAT — a tiny handheld voice assistant. It has:
- **240x280 pixel LCD** (SPI, driven by PIL images in Python)
- **Speaker + microphone** (push-to-talk voice assistant)
- **1 button** (tap to scroll, hold to talk)
- **RGB LED** (state indicator)
- **512MB RAM** (tight — Node.js is heavy, Python is the native runtime)

The device talks to an OpenClaw gateway for AI responses and uses OpenAI for speech-to-text and TTS.

## Current Animation System

All rendering is in `display.py` (Python, PIL/Pillow). The current character is a **Kirby-style pixel art sprite** hardcoded as grid coordinates.

### How frames work

`_generate_sprite_frames()` produces a dict of named `PIL.Image` objects (240x240 pixels, RGB):

```
idle, idle_blink
listen, listen_blink
think1, think1_blink, think2, think2_blink
talk0, talk0_blink, talk1, talk1_blink, talk2, talk2_blink, talk3, talk3_blink
happy, happy_blink
```

### How animation works

`_character_loop()` runs at ~10fps and selects a frame based on the current state:

| State | Frame selection |
|---|---|
| `"idle"` | `idle` frame, gentle bob animation (±4px vertical offset) |
| `"listening"` | `listen` frame (wide eyes, attentive) |
| `"thinking"` | alternates `think1`/`think2` every 15 ticks (eyes dart side to side) |
| `"talking"` | `talk0`-`talk3` selected by TTS mouth RMS level (0=closed, 3=wide open) |
| `"done"` | `happy` frame with bob |

Blink is applied every ~40 ticks (~4 seconds) by swapping to the `_blink` variant.

The loop also draws:
- Accent color bar at top (color per state)
- Status label ("Listening…", "Thinking…")
- TTS subtitle text (current sentence being spoken)
- Battery indicator

### Frame format

Each frame is a `PIL.Image.Image`, mode `"RGB"`, size `(240, 240)`. The remaining 40px of the 240x280 screen is used for text/UI below the character.

Frames are converted to RGB565 via `_image_to_rgb565()` and pushed to the LCD via SPI.

## What We Want

Replace the hardcoded Kirby with **storymode characters** that can be swapped dynamically. The animation states (idle, listening, thinking, talking, done) stay the same — just the visuals change.

## Proposed Approach

### Pre-rendered sprite sheets

Generate character frames as **PNG files** (240x240, RGB) on a more powerful machine, then sync them to the Pi. The device loads them into memory at startup.

Suggested file structure on the Pi:
```
/home/pi/pizero-openclaw/characters/
  default/
    idle_0.png, idle_1.png, ...
    listen_0.png, ...
    think_0.png, think_1.png, ...
    talk_0.png, talk_1.png, talk_2.png, talk_3.png
    happy_0.png, ...
    blink.png  (or per-state blinks)
  another_character/
    ...
```

Config in `.env`:
```
CHARACTER_DIR="characters/default"
```

### What the storymode/pixterm-engine side needs to produce

For each character, generate these frame sets at **240x240 pixels, RGB, PNG**:

1. **idle** — 1+ frames for idle animation (breathing, bobbing, etc.)
2. **listen** — 1+ frames for attentive/listening pose
3. **think** — 2+ frames for thinking animation (head tilt, looking around)
4. **talk** — 4 frames mapped to mouth openness: 0=closed, 1=slightly open, 2=open, 3=wide open
5. **happy** — 1+ frames for completion/satisfaction
6. **blink** variants of each (or a single blink overlay)

Background should be **black (0, 0, 0)** — the LCD is black when off, so black backgrounds look seamless.

### Constraints

- **240x240 pixels** for the character area (the bottom 40px is reserved for UI text)
- **RGB, no alpha** (the LCD doesn't support transparency)
- **Keep file sizes small** — the Pi has 512MB RAM and loads all frames at startup. Aim for <50KB per PNG.
- **No animation framework on the device** — the Python loop just cycles through pre-loaded PIL images. All animation logic (which frame to show when) is already handled.
- **No Node.js on the device** — the Pi Zero 2 W struggles with Node.js memory. Pre-render everything externally.

## Device Repo

- Fork: https://github.com/Yuncun/pizero-openclaw
- Key file: `display.py` — all rendering code
- The `_generate_sprite_frames()` function and `_character_loop()` method are the integration points
- SSH access: `ssh pi@pizero.local` from Eric's MacBook

## Questions for the Storymode Side

1. What format are character assets currently in? Can they be rendered to 240x240 PNG?
2. Does pixterm-engine have a "render to image file" mode, or only ANSI terminal output?
3. Could the generation pipeline (ComfyUI/AI) produce character poses at this resolution?
4. What characters are available and which would look best at 240x240 pixel art scale?
5. Should we build a CLI command like `storymode-cli render-device-sprites --character X --output ./sprites/` ?
