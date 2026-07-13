# Expressiv MIDI Pro 3 — MIDI implementation chart

Everything TrackMagnet-relevant, extracted from Rob O'Reilly Guitars'
official "MIDI PRO User Guide" (18 Jan 2023 edition, software 6-836).

> **Which guitar is this?** The official guide covers several instruments in
> one document (MIDI Pro 2 guitar, MIDI Pro Bass, and newer revisions). This
> project targets the **MIDI Pro 3** — when consulting ROR documentation,
> always use the MIDI Pro 3-specific sections/values, and get the latest
> guide from [rorguitars.com](https://www.rorguitars.com/) rather than
> trusting cached copies. The MIDI facts below are common to the MIDI Pro
> platform; verify anything critical against your own unit with a MIDI
> monitor.

## Connections

| Port | Notes |
|---|---|
| USB (Type-B) | Plug & play with any DAW. **Bi-directional** MIDI (the guitar also receives). Powers the system and charges the battery. Connect directly — no USB hubs. |
| 5-pin MIDI | For hardware synths. Bi-directional on instruments built after 2020 (needs all 5 pins wired). Needs USB/battery power. |
| Wireless | Via MIDIjet Pro (5-pin) or CME WIDI Master (Bluetooth) plugged into the 5-pin port. |

## What the guitar sends

| Source | Message | Channel | Details |
|---|---|---|---|
| **Volume knob** (also the power switch) | **CC 7 by default** ("CC-A") | Global channel (default 1) | Absolute 0–127. Can be reassigned to any CC, or **send up to 3 CCs simultaneously** (CC-A, CC-B, CC-C), each on its own channel. Can be disabled ("Off"). Menu → Volume Knob. |
| Joystick X / Y | Any CC per axis; pitch bend assignable to X | Per-axis (or global) | Spring-return behavior configurable per axis: return to 0, 64, 127, or hold last value ("Return Off"). Menu → Joystick. |
| XY Pad | Any CC per axis (**default CC 1**, modulation) | Per-axis (or global) | First touch jumps to absolute position; release holds the last CC value. Optional pitch bend on X (relative to first touch, recenters on release). "XY Switch" mode: press = 127, release = 0. Also triggers fretted notes (velocity from Y position). |
| Strings / fretboard | Note On/Off, velocity-sensitive, polyphonic | Global, or per-string channels | Pick, Tap, or XY triggering. String bends send pitch bend on the string's channel (one pitch bend per channel — per-string channels give polyphonic bend). String Bend can additionally send a CC. |
| Finger pads (optional) | Notes, or CC / aftertouch / channel pressure | Per-pad (or global) | Pressure output modes: 0→127, 127→0, 64→127, 64→0, momentary switch (0/127), latching switch. |
| Preset toggle | **Program Change** | Global channel | Selecting preset N sends PC N by default (can be disabled per preset). Octave/semitone buttons shift note numbers only. |

## What the guitar receives (MIDI Input)

When enabled (Menu → MIDI Input), the guitar reads **one** command type —
Control Change, Program Change, or Note On — on a configured channel, and
values **0–49 select the corresponding preset**. Works over USB on all units
(5-pin too on post-2020 instruments). This is how a DAW or foot controller
can switch guitar presets remotely.

## The preset system (the big TrackMagnet gotcha)

- There are **30 presets**, and *everything above is stored per preset*:
  volume-knob CCs and channels, joystick/XY assignments, per-string
  channels, tunings, program changes.
- **Changing preset can therefore silently change what every control
  sends.** If TrackMagnet "stops working" after you toggle the preset
  switch, the new preset almost certainly has different CC/channel
  assignments — either configure all your presets consistently or match
  `profile.json` to the preset you actually play with.
- Unsaved menu tweaks revert on power-down or preset change; saving requires
  unlocking memory (Menu → General → Memory Locked).
- A Master Reset restores factory CC assignments (CC 7 volume knob, CC 1 XY
  Pad, global channel).

## Implications for TrackMagnet

- The stock mapping (**CC 7, channel 1 → selected_track_volume**) matches
  the guitar's factory default — zero configuration on either side.
- All continuous controls send **absolute** values, which is exactly what
  TrackMagnet v1 expects. `"takeover": "pickup"` pairs well with the volume
  knob when hopping between tracks with different levels.
- The joystick and XY Pad are natural extra controls: an XY Pad axis
  (holds its value on release) suits `selected_track_send`; a joystick axis
  set to **Return Off** suits `selected_track_pan` — the spring-return
  modes would yank the parameter back on release.
- The CC-B/CC-C feature can make one physical knob send two CCs — e.g.
  CC 7 → volume and CC 8 → a send, moving together from one gesture.
- Preset changes emit Program Change messages; TrackMagnet only listens to
  its configured CCs, so these are harmlessly ignored.
- The guitar's MIDI *input* (preset select via CC/PC/Note) is a possible
  future TrackMagnet feature: selecting a track in Live could recall a
  matching guitar preset.
