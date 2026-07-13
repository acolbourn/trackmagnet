# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), versions follow
[Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-07-12

Core acceptance checklist (checks 1–9) passed on Windows 11 + Live 12.4.2
with an Expressiv MIDI Pro over a CME WIDI uHost: load feedback, volume
follows selection, full sweep, isolation, clean reload, and graceful
fallback on broken JSON all verified on hardware. Extended targets
(pan, sends, pickup takeover) are unit-tested but not yet hardware-tested.

### Added
- Initial release target: raw Live 12 remote script (no `_Framework`, no
  `ableton.v2/v3`) that forwards configured CCs and writes them to the
  currently selected track.
- `profile.json` configuration: `cc`, `channel`, `target`, `index`,
  `takeover` — validated on load with visible status-bar errors and a safe
  fallback (CC 7 / channel 1 / volume), so the script always loads.
- Targets: `selected_track_volume` (core), `selected_track_pan`,
  `selected_track_send`.
- Optional per-control soft-takeover: `"takeover": "pickup"` (threshold +
  crossing detection, reset on track selection change).
- Controller profiles: Expressiv MIDI Pro 3 (flagship) and `_template`.
- Debug mode (`"debug": true` in profile.json): listens to every CC on
  every channel and logs each incoming message to Log.txt — finds what a
  controller really sends without an external MIDI monitor fighting Live
  for the port.
- Profile errors re-display in the status bar for ~15 seconds (Live's
  status-bar messages otherwise vanish too fast to read).
- CI: byte-compile on Python 3.11 (Live 12's version), ruff, profile
  validation via the script's own validator, unit tests for all Live-free
  logic (41 tests, including a stubbed-Live lifecycle suite).
