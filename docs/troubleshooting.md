# Troubleshooting

Work top to bottom — each check narrows down where the chain breaks:
**folder → dropdown → load message → MIDI in → fader moves**.

## TrackMagnet doesn't appear in the Control Surface dropdown

- The folder must be at
  `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\TrackMagnet`
  — the `TrackMagnet` folder itself, not a `src` folder containing it, and
  the name must have **no spaces**.
- Confirm the User Library location in **Preferences → Library** — if you
  moved it, `Remote Scripts` goes inside the moved location. On OneDrive-
  synced machines the real path is usually
  `C:\Users\<you>\OneDrive\Documents\Ableton\User Library`.
- Restart Live after copying; the dropdown is populated at startup.
- A Python syntax error prevents the script from being listed. Check
  Log.txt (path below) for a traceback mentioning `TrackMagnet`.

## It loads, but turning the knob does nothing

1. Status bar said `TrackMagnet: ... loaded`? If it showed a
   `profile.json problem` instead, fix the reported issue first (the script
   is running on the CC 7 default meanwhile).
2. In **Preferences → Link, Tempo & MIDI**:
   - The TrackMagnet slot's **Input** must be your controller's port.
   - **Remote** must be **On** for that input port in the MIDI Ports list.
3. Find out what the knob actually sends — manuals lie and presets change
   channels. Add `"debug": true` to the top level of `profile.json`, reload
   the script, turn the knob, and read Log.txt: every incoming CC is logged
   as `debug: received CC <n> ch <n> value <n>`. If CCs appear but say
   "no matching control", fix `cc`/`channel` in the profile to match. If
   **nothing** appears, the messages aren't reaching the script — check the
   port (step 2) or a conflicting manual mapping (next section). Set
   `"debug": false` when done.
4. An external MIDI monitor (MIDI-OX, Pocket MIDI) works too, but Windows
   MIDI ports are exclusive: while the monitor holds the port, Live can't
   read it — close the monitor, then restart Live.

## The knob controls the wrong thing / one specific track / two things at once

- The CC is probably also mapped in the set's manual MIDI map. Press
  **Ctrl+M** and check the MIDI Mappings browser (left panel) for your CC
  number; delete the entry. Manual mappings intercept the CC before scripts
  see it, they live inside the saved set/template (so they can be years
  old), and they're easy to create by accident — turning a knob while MIDI
  map mode is open silently maps it to whatever was clicked last. A
  telltale: a manual mapping physically moves a fader/knob on screen,
  while a plugin merely obeying CC 7 ("MIDI Volume") gets quieter without
  anything moving.
- Another Control Surface slot may claim the same port/CC. Set duplicates to
  "None".

## The fader jumps abruptly when I first touch the knob

That's the default `jump` takeover. Set `"takeover": "pickup"` on the control
in `profile.json`: the knob then only takes effect once it sweeps past the
parameter's current position.

## Edits to profile.json have no effect

- Reload the script: set the Control Surface slot to "None" and back, or
  restart Live. There is no hot reload.
- Make sure you edited the **installed** copy
  (`...\Remote Scripts\TrackMagnet\profile.json`), not the one in your repo
  checkout.
- Multiple Live versions? Preferences (and Log.txt) are per-version — confirm
  you configured the Live 12 instance you're running.

## It worked, then stopped after switching Control Surface to None and back

This shouldn't happen (listeners are torn down in `disconnect`). Restart Live
to recover, then please
[file a bug](../.github/ISSUE_TEMPLATE/bug_report.md) with the Log.txt
excerpt around the reload.

## Reading Log.txt

```
C:\Users\<you>\AppData\Roaming\Ableton\Live 12.x\Preferences\Log.txt
```

Tail it live while testing:

```powershell
Get-Content "$env:APPDATA\Ableton\Live 12*\Preferences\Log.txt" -Wait -Tail 20
```

Everything TrackMagnet logs is prefixed `TrackMagnet:` — load confirmation,
each configured control, every profile.json problem, and any failed write
with the reason.
