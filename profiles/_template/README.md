# <Controller make + model> profile

> Template — copy this folder to `profiles/<your_controller_name>/`, edit
> `profile.json`, fill in the sections below, delete these blockquotes, and
> open a PR. You never have to touch Python to add a controller.

One or two sentences: what the controller is and what this profile makes it do
("the big knob rides the selected track's volume", etc.).

## Install

1. Install TrackMagnet itself (see the repo [README](../../README.md)).
2. Copy this folder's `profile.json` over
   `...\Remote Scripts\TrackMagnet\profile.json`.
3. Reload the script (Control Surface → "None" and back, or restart Live).

## MIDI implementation used by this profile

| Control on device | Message | Channel | Used as |
|---|---|---|---|
| e.g. Knob 1 | CC 7 | 1 | `selected_track_volume` |

> Verify what the device actually sends with a MIDI monitor
> (MIDI-OX, Pocket MIDI) rather than trusting the manual.

## Quirks / notes

> Anything surprising: endless encoders vs. absolute pots, channels that
> change with presets, controls that send on release, etc. If the device has
> endless/relative encoders, note that TrackMagnet v1 expects **absolute** CC
> values (0-127).
