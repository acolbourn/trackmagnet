# v1 acceptance checklist (Windows 11 + Live 12)

Live can't run in CI, so this manual checklist gates the `v1.0.0` tag. Run it
on a real machine with a real controller (or a virtual MIDI port + monitor,
e.g. loopMIDI + a CC sender). Check every box before releasing.

Setup: script installed per [install.md](install.md), stock `profile.json`
(CC 7, channel 1, volume), controller input selected, Remote enabled.

- [ ] **1. Discovery** — "TrackMagnet" appears in Preferences → Link, Tempo &
  MIDI → Control Surface dropdown after a restart.
- [ ] **2. Load feedback** — on load, the status bar shows
  `TrackMagnet: v1.0.0 loaded — profile "..."`, and Log.txt contains the
  matching load line listing the configured control(s).
- [ ] **3. Basic control** — with Track 1 selected, turning the CC 7 knob
  moves Track 1's volume fader in real time.
- [ ] **4. Follows selection** — select Track 2 (mouse or arrow keys); the
  same knob now moves Track 2's fader. No remapping, no restart. Track 1's
  fader stays where it was.
- [ ] **5. Full range** — a full 0→127 sweep drives the fader from silence to
  the very top (+6 dB position, i.e. parameter 0.0→1.0).
- [ ] **6. Isolation** — notes, pitch bend, and other CCs the controller
  sends change nothing (no fader moves, no parameter changes, no errors in
  Log.txt).
- [ ] **7. Clean reload** — switching the Control Surface slot to "None" and
  back to TrackMagnet re-loads cleanly: load message reappears, control still
  works, no traceback in Log.txt (proves listener teardown).
- [ ] **8. Reconfiguration** — edit `profile.json` to a different `cc`,
  reload (step 7's method): the new CC controls volume, the old one does
  nothing.
- [ ] **9. Broken config degrades gracefully** — put a deliberate error in
  `profile.json` (e.g. delete a comma), reload: the status bar shows a
  `profile.json problem` message naming the issue, Log.txt has details, and
  CC 7 still controls the selected track's volume (default fallback).

## Extended targets (implemented, marked young until this passes)

- [ ] **10. Pan** — a control with `"target": "selected_track_pan"` sweeps
  the selected track's pan knob fully left (0) to fully right (127), with 64
  exactly centered.
- [ ] **11. Sends** — `"target": "selected_track_send", "index": 0` drives
  Send A on the selected track; with the Master track selected it does
  nothing and logs no errors.
- [ ] **12. Pickup takeover** — with `"takeover": "pickup"` on volume: after
  selecting a track whose fader is far from the knob, turning the knob does
  nothing until it sweeps past the fader's position, then tracks smoothly.
  Selecting another track requires picking up again.

Record the Live point version (Help → About) and date when it passes, then
update CHANGELOG.md and tag `v1.0.0`.
