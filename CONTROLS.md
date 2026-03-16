# WhisPlay Button Controls Reference

## Hardware

One physical button (GPIO 11). All interactions are tap (< 400ms) or hold (≥ 400ms).
RGB LED provides visual feedback for mode changes.

## Button Map by State

| Current State | Tap | Double-tap | Hold (≥ 400ms) |
|---|---|---|---|
| **Screen sleeping** | Wake display | Wake display | Wake display |
| **Idle (claudia)** | *(no action)* | *(no action)* | Start recording (push-to-talk) |
| **Listening** | *(holding button)* | *(holding button)* | Release to stop & process |
| **Transcribing** | Cancel → idle | Cancel → idle | Cancel → idle |
| **Thinking** | Cancel → idle | Cancel → idle | Cancel → idle |
| **Streaming/TTS** | Show transcript | Show transcript | Show transcript |
| **Response** | Scroll pages | Dismiss + cancel TTS → idle | Dismiss + cancel TTS → idle |
| **Error** | *(no action)* | *(no action)* | Start recording |

Note: Cancel during transcribing/thinking requires 2s lockout to prevent accidental cancels.

## Mode Switches (work from any state)

| Combo | Action | LED Flash | Screen Label |
|---|---|---|---|
| **3 taps** (within 1s) | Toggle Silent Mode | 🔵 Blue ×3 | "helen" |
| **4 taps** (within 1.2s) | Toggle Guest Mode | 🔴 Red ×3 | "claudi-ugh" |
| **Either off** | Back to normal | 🟢 Green ×3 | "claudia" |

Modes are mutually exclusive. Switching to one clears the other.

## Modes

### claudia (normal)
- Full voice responses via TTS
- Standard personality

### helen (silent)
- Text-only responses on screen, no TTS playback
- Same personality, just quiet

### claudi-ugh (guest)
- Roasts Eric in front of friends
- Valley girl TTS voice (fast, exasperated, vocal fry)
- Conversation history saved on entry, restored on exit (roast context doesn't leak)
- Can also be triggered by voice: "Claudia, meet my friends" (but only button exits)

## Screen Layout (Idle)

```
┌──────────────────────────────┐
│ WiFi bars    Vol%    Batt%   │  ← top bar
│                              │
│           HH:MM              │  ← clock
│      Day, Mon DD             │  ← date
│         SSID                 │  ← WiFi network
│       192.168.x.x            │  ← IP address
│                              │
│         claudia              │  ← mode label
└──────────────────────────────┘
```

## Timeouts

| Timeout | Duration | Action |
|---|---|---|
| Response hold | 30s | Auto-dismiss response → idle |
| Sleep | 60s idle | Display turns off |
| Cancel lockout | 2s | Prevents accidental cancel of fresh operations |
| Tap settle | 450ms | Waits after last tap to determine single/double/triple/quad |
