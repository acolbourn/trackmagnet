# Adding a controller profile

A profile is a folder under `profiles/` containing a `profile.json` (same
schema the script itself uses) plus a README documenting the controller's
MIDI implementation. Adding one requires **zero Python**.

## Steps

1. **Copy the template:** duplicate `profiles/_template/` as
   `profiles/<maker_model>/` (lowercase, underscores — e.g.
   `profiles/akai_mpk_mini_3/`).
2. **Find out what the controller really sends.** Easiest way: add
   `"debug": true` to the top level of your installed `profile.json`,
   reload the script, move every control you care about, and read Log.txt —
   each incoming CC is logged with its number, channel (1–16), and value.
   (An external MIDI monitor like MIDI-OX works too, but it fights Live for
   the port on Windows.) Note whether each control is an absolute pot
   (sweeps 0–127) or an endless/relative encoder. **TrackMagnet v1 expects
   absolute values** — if the encoder has an absolute mode, use it and note
   how to enable it. Turn `debug` off when done.
3. **Edit `profile.json`.** One entry per control:

   ```json
   {
     "name": "Akai MPK mini mk3",
     "controls": [
       { "cc": 70, "channel": 1, "target": "selected_track_volume" },
       { "cc": 71, "channel": 1, "target": "selected_track_pan", "takeover": "pickup" },
       { "cc": 72, "channel": 1, "target": "selected_track_send", "index": 0 }
     ]
   }
   ```

   Keys starting with `_` (like `"_comment"`) are ignored — use them freely.
4. **Validate:** `python tools/validate_profiles.py` from the repo root
   (needs any Python 3.11+; no Live required). CI runs the same check on
   your PR.
5. **Fill in the README and MIDI chart** in your profile folder — what the
   controller is, the table of messages used, and any quirks (channels that
   change with presets, controls that only send on release, etc.).
6. **Test it in Live** if you can: copy your `profile.json` over the
   installed `...\Remote Scripts\TrackMagnet\profile.json`, reload the
   script, and run through: volume follows selection; each extra control
   does what the chart says; a full 0→127 sweep covers the whole range.
7. **Open a PR.**

## Schema reference

| Key | Required | Values | Meaning |
|---|---|---|---|
| `cc` | yes | 0–127 | CC number |
| `channel` | yes | 1–16 | MIDI channel (human convention, as MIDI monitors show) |
| `target` | yes | `selected_track_volume` · `selected_track_pan` · `selected_track_send` | What it drives on the selected track |
| `index` | for sends | 0, 1, 2… | 0 = Send A, 1 = Send B… |
| `takeover` | no | `jump` (default) · `pickup` | `pickup` = soft takeover, no value jumps |

Two controls may not share the same `cc` + `channel` pair. The profile's
`name` is shown in Live's status bar at load.
