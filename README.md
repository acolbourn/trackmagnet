# trackmagnet

**Your MIDI controls stick to whatever track you select in Ableton Live.** Turn one knob, and it always moves the *selected* track's volume — no per-set mapping, no remapping when you switch tracks.

<!-- TODO: hero demo GIF — knob turns → selected track's fader moves, select another track → same knob moves that fader. -->

![CI](https://github.com/acolbourn/trackmagnet/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)
![Live 12 · Windows](https://img.shields.io/badge/Ableton%20Live-12%20·%20Windows-blue.svg)

## Why this exists

The existing options for "hardware follows the selected track" are heavy (wiffbi's Selected_Track_Control configures via a Python file and targets older Live versions), paid and closed-source (ClyphX Pro), or GUI code generators (Remotify). TrackMagnet is one tiny, readable, MIT-licensed remote script configured by a single JSON file. Players and producers — the flagship example is the [Expressiv MIDI Pro guitar](profiles/expressiv_midi_pro_3/) — get their hardware following the selected track in under a minute.

## Quickstart

1. Download this repo ([ZIP](../../archive/refs/heads/main.zip) or `git clone`).
2. Copy the `src\TrackMagnet` folder into `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\` (create the `Remote Scripts` folder if it doesn't exist). **If Windows syncs your Documents to OneDrive, the path is `C:\Users\<you>\OneDrive\Documents\Ableton\...`** — when in doubt, Live shows the true location under **Preferences → Library → Location of User Library**.
3. Restart Live.
4. In **Options → Preferences → Link, Tempo & MIDI**, pick **TrackMagnet** in a free Control Surface slot and set its **Input** to your controller's MIDI port. Also enable **Remote** for that input port in the MIDI Ports list below.
5. Turn your CC 7 knob — the selected track's volume fader moves. Select another track; the same knob now controls *that* track.

Full walkthrough with exact paths: [docs/install.md](docs/install.md).

## Configuration

Edit `profile.json` inside the installed `TrackMagnet` folder, then reload the script (Control Surface → "None" and back, or restart Live):

```json
{
  "name": "My controller",
  "controls": [
    { "cc": 7,  "channel": 1, "target": "selected_track_volume" },
    { "cc": 10, "channel": 1, "target": "selected_track_pan", "takeover": "pickup" },
    { "cc": 8,  "channel": 1, "target": "selected_track_send", "index": 0 }
  ]
}
```

| Key | Values | Meaning |
|---|---|---|
| `cc` | 0–127 | The CC number your knob/fader sends |
| `channel` | 1–16 | Its MIDI channel (as shown in MIDI monitors) |
| `target` | `selected_track_volume`, `selected_track_pan`, `selected_track_send` | What it controls on the selected track |
| `index` | 0, 1, 2… | Which send (`selected_track_send` only; 0 = Send A) |
| `takeover` | `jump` (default), `pickup` | `pickup` waits until the knob catches up with the parameter before writing — no value jumps |

There is also a top-level `"debug": true` option: TrackMagnet then listens to **every** CC on **every** channel and logs each incoming message to Log.txt (`debug: received CC 7 ch 1 value 64 ...`). It's the fastest way to find out what your controller actually sends — no separate MIDI monitor fighting Live for the port. Turn it off again when done.

If `profile.json` has a mistake, TrackMagnet still loads (falling back to CC 7 / channel 1 / volume) and tells you exactly what's wrong in Live's status bar and Log.txt.

`selected_track_volume` and `selected_track_send` are hardware-tested (Live 12.4, Windows 11, Expressiv MIDI Pro). `selected_track_pan` and `pickup` takeover are implemented and unit-tested but not yet exercised on hardware — reports welcome.

## Requirements

**Ableton Live 12 (any edition), Windows.** That's the tested scope. (The Python itself is OS-agnostic — macOS users only need different install paths; docs contributions welcome.)

## Adding your controller

Copy [`profiles/_template`](profiles/_template/), edit the JSON, document the MIDI chart, open a PR — no Python required. See [docs/adding-a-profile.md](docs/adding-a-profile.md). Shipped profiles:

- [Expressiv MIDI Pro 3](profiles/expressiv_midi_pro_3/) (Rob O'Reilly Guitars) — the guitar's volume knob rides the selected track's volume, and the two knobs below the finger pads drive Sends A and B.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Script not in the Control Surface dropdown | Wrong folder, folder name has a space, or a syntax error | Folder must be `...\User Library\Remote Scripts\TrackMagnet` (no spaces); check Log.txt for a traceback |
| Loads but the knob does nothing | **Remote** not enabled for the input port, or wrong CC/channel | Enable Remote (In) for the device in MIDI prefs; verify the CC number with a MIDI monitor |
| Knob controls the wrong thing | The CC is also manually MIDI-mapped in the set | Remove the manual MIDI mapping of that CC |
| Fader jumps abruptly to the knob position | Takeover is `jump` (the default) | Set `"takeover": "pickup"` on that control |
| Works, then stops after a reload | Shouldn't happen — stale listener | Restart Live; please file an issue with Log.txt |
| Changes have no effect | Multiple Live versions installed — prefs are per-version | Make sure you configured the Live 12 instance |

More detail (including where Log.txt lives and how to tail it): [docs/troubleshooting.md](docs/troubleshooting.md).

## Roadmap

- v1: selected-track **volume** via CC forwarding (done) — plus pan, sends, and pickup takeover implemented ahead of schedule
- Next: device/macro control (`selected_device_param`), note-type controls (transport, Looper triggers), per-control forwarding vs. direct-mapping choice
- Exploring: MIDI feedback *to* the controller — e.g. the Expressiv MIDI Pro can receive CC/PC/Note messages to switch its presets, so selecting a track in Live could recall a matching guitar preset

Each of these is another `target` string in the JSON plus one branch in the dispatcher — the architecture doesn't change.

## Status & support

TrackMagnet is an unofficial third-party script. Ableton [does not provide support for third-party remote scripts](https://help.ableton.com/hc/en-us/articles/206240184); the User Library `Remote Scripts` folder is Ableton's sanctioned install location for them. Issues and Log.txt excerpts are welcome here on GitHub.

## Credits & license

Standing on the shoulders of [wiffbi](https://wiffbi.com/) (Selected_Track_Control, and the "skip the framework" advice), [Structure Void](https://structure-void.com/) (unofficial Live API docs), and Julien Bayle's API references. Expressiv MIDI Pro by [Rob O'Reilly Guitars](https://www.rorguitars.com/).

[MIT](LICENSE).
