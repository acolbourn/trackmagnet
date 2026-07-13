# Installing TrackMagnet (Windows, Live 12)

## 1. Get the files

Download the repo as a ZIP (green **Code** button → Download ZIP) or clone it.
The only folder Live needs is `src\TrackMagnet`.

## 2. Copy the script into Live's User Library

Copy the whole `TrackMagnet` folder (the one directly containing
`__init__.py` and `profile.json`) to:

```
C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\TrackMagnet\
```

Notes:

- **OneDrive users:** if Windows syncs your Documents folder to OneDrive
  (very common on Windows 11), there is no `C:\Users\<you>\Documents\Ableton`
  — the real path is `C:\Users\<you>\OneDrive\Documents\Ableton\...`. The
  authoritative answer is always Live's
  **Preferences → Library → Location of User Library**.
- If the `Remote Scripts` folder doesn't exist inside `User Library`, create
  it — exact spelling, with the space.
- The folder name `TrackMagnet` is what appears in Live's dropdown. It must
  contain **no spaces**.
- If your User Library lives elsewhere, check Live's
  **Preferences → Library → Location of User Library**.
- This is Ableton's sanctioned location for third-party scripts and survives
  Live updates (unlike the folder inside the Live installation).

You should end up with:

```
...\Remote Scripts\TrackMagnet\__init__.py
...\Remote Scripts\TrackMagnet\track_magnet.py
...\Remote Scripts\TrackMagnet\config.py
...\Remote Scripts\TrackMagnet\midi_utils.py
...\Remote Scripts\TrackMagnet\profile.json
...\Remote Scripts\TrackMagnet\version.py
```

## 3. Enable it in Live

1. Restart Live (it scans for scripts at startup).
2. Open **Options → Preferences → Link, Tempo & MIDI**.
3. In a free **Control Surface** slot, choose **TrackMagnet**.
4. Set that slot's **Input** to your controller's MIDI input port.
   (**Output** can stay "None" — v1 sends nothing back.)
5. In the **MIDI Ports** list below, make sure **Remote** is **On** for your
   controller's input port.
6. Live's status bar (bottom of the window) should show
   `TrackMagnet: v1.0.0 loaded — ...`.

## 4. Try it

With any track selected, turn the knob that sends **CC 7 on channel 1** (the
default profile). The selected track's volume fader moves. Click a different
track — the same knob now moves that track's fader.

Different knob? Edit `profile.json` in the installed folder (see the
[README](../README.md#configuration)), then set the Control Surface slot to
"None" and back to **TrackMagnet** to reload.

## Where things live (for debugging)

| What | Path |
|---|---|
| Installed script | `C:\Users\<you>\Documents\Ableton\User Library\Remote Scripts\TrackMagnet\` |
| Live's log | `C:\Users\<you>\AppData\Roaming\Ableton\Live 12.x\Preferences\Log.txt` |

Tail the log in PowerShell while testing:

```powershell
Get-Content "$env:APPDATA\Ableton\Live 12*\Preferences\Log.txt" -Wait -Tail 20
```

If anything misbehaves, see [troubleshooting.md](troubleshooting.md).
