# Contributing to trackmagnet

Thanks for helping! The two most valuable contributions are **controller
profiles** (no Python needed) and **bug reports with Log.txt excerpts**.

## Setup

There is no build step. The installable script is the `src/TrackMagnet`
folder — installing means copying it into Live's User Library:

```
C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\TrackMagnet\
```

For development, either copy on each change or make a directory junction so
your checkout is live:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\Documents\Ableton\User Library\Remote Scripts\TrackMagnet" -Target "<repo>\src\TrackMagnet"
```

## Adding a controller profile

1. Copy `profiles/_template/` to `profiles/<your_controller>/` (lowercase,
   underscores).
2. Edit `profile.json` — verify the CC/channel numbers with a MIDI monitor,
   don't trust the manual.
3. Fill in the README and MIDI chart.
4. Run `python tools/validate_profiles.py` (CI runs it too).
5. Open a PR. Done — you never touched Python.

## Code contributions

- **Python 3.11, stdlib only.** Live 12 embeds Python 3.11 and does not
  resolve site-packages; the core must stay dependency-free.
- **Keep `config.py` and `midi_utils.py` free of `import Live`** — they are
  shared with the tests and CI validator, which run outside Live.
- **The listener-hygiene rule:** every `add_*_listener` call must have a
  matching `remove_*_listener` in `disconnect()`. Orphaned listeners are the
  top cause of crashes across script reloads.
- Lint with `ruff check .`; tests with `pytest` (both run in CI on 3.11).
- Wrap LOM writes in try/except with a Log.txt message — a point-release API
  change must degrade gracefully, never crash Live.

## Testing against Live 12 (manual — Live can't run in CI)

1. Install the script (see Setup), restart Live, select **TrackMagnet** as a
   Control Surface and set its Input; enable **Remote** for the port.
2. Reload loop after edits: set the Control Surface to "None" and back
   (sometimes a new set via Ctrl+N helps), or restart Live. There is no hot
   reload.
3. Watch the log while you work:

```powershell
Get-Content "$env:APPDATA\Ableton\Live 12*\Preferences\Log.txt" -Wait -Tail 20
```

Every `log_message` from the script is prefixed `TrackMagnet:`.

Before a release, the full
[acceptance checklist](docs/acceptance-checklist.md) must pass on a real
Windows 11 + Live 12 machine.

## Platform scope

The script itself is OS-agnostic Python — only the documented install paths
and testing workflow are Windows. macOS path documentation is welcome as a
docs PR.

## Releases

Semantic versioning. Bump `src/TrackMagnet/version.py`, update
`CHANGELOG.md`, tag `vX.Y.Z`.
