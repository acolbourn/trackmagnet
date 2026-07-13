# Expressiv MIDI Pro 3 profile

The [Expressiv MIDI Pro](https://www.rorguitars.com/) is Rob O'Reilly Guitars'
MIDI guitar. With this profile, the guitar's onboard volume knob rides the
volume fader of whatever track you have selected in Live — select a track,
turn the knob, done. No per-set MIDI mapping.

> **Model note:** ROR's official user guide covers several instruments
> (MIDI Pro 2, MIDI Pro Bass, and newer revisions) in one document. This
> profile targets the **MIDI Pro 3** — when checking anything against ROR
> documentation, use the MIDI Pro 3-specific sections and the latest guide
> from rorguitars.com.

## Install

1. Install TrackMagnet itself (see the repo [README](../../README.md)).
2. Copy this folder's `profile.json` over
   `...\Remote Scripts\TrackMagnet\profile.json`.
3. Reload the script (set the Control Surface to "None" and back, or restart
   Live).

## What this profile maps

| Guitar control | Sends | Drives on the selected track |
|---|---|---|
| Volume knob | CC 7 ch 1 | Volume |
| Lower knob (below finger pads) | CC 74 ch 1 | Send A |
| Upper knob (below finger pads) | CC 71 ch 1 | Send B |

Full MIDI implementation chart (from the official user guide plus
hardware-measured values): [midi-chart.md](midi-chart.md).

Connect the guitar over USB or a WIDI wireless adapter (directly, not
through a hub), set the TrackMagnet Control Surface's **Input** to the
guitar's port, and enable **Remote** for that port in Live's MIDI
preferences. Sends only do something if the set has Return tracks.

## Quirks / notes

- **Presets can remap everything.** The guitar stores CC and channel
  assignments *per preset* (30 of them). If the knob stops moving the fader
  after you toggle the preset switch, the new preset likely sends a
  different CC or channel. Configure your presets consistently, or update
  `profile.json` to match the preset you play with. Verify with a MIDI
  monitor (e.g. [MIDI-OX](http://www.midiox.com/) or
  [Pocket MIDI](https://www.morson.jp/pocketmidi-webpage/)) —
  remember Windows MIDI ports are exclusive, so close the monitor before
  giving the port back to Live.
- **Preset changes send Program Change messages** (preset N → PC N by
  default). TrackMagnet ignores them; they're harmless.
- **The volume knob is also the power switch** — the first click of the
  turn powers the guitar on, so expect no CC output until the display shows
  "Ready".
- **The knob can send up to 3 CCs at once** (CC-A/B/C, each on its own
  channel). With extra `profile.json` entries, one knob gesture can drive
  volume *and* a send simultaneously.
- **Good extra controls:** an XY Pad axis holds its value on release —
  well-suited to `selected_track_send`. A joystick axis works for
  `selected_track_pan` only if its Return is set to **Off**; the
  spring-return modes (0/64/127) snap the CC back when released.
- **Notes are unaffected.** TrackMagnet consumes only the configured CC(s);
  the guitar's Note On/Off and pitch bend pass through to the track input
  for playing instruments as usual.
