"""Loading and validation for profile.json.

Pure stdlib, no ``Live`` import — this module is shared between the running
remote script, the test suite, and CI profile validation, so it must import
cleanly outside Live's embedded interpreter.

Design rule: a broken profile must never prevent the script from loading.
Every problem is collected as a human-readable string (surfaced in Live's
status bar and Log.txt), invalid controls are skipped, and if nothing valid
remains we fall back to the default control (CC 7, channel 1, volume).
"""

import json

VALID_TARGETS = {
    "selected_track_volume",
    "selected_track_pan",
    "selected_track_send",
}
TARGETS_NEEDING_INDEX = {"selected_track_send"}
VALID_TAKEOVER = {"jump", "pickup"}
ALLOWED_CONTROL_KEYS = {"cc", "channel", "target", "index", "takeover"}

DEFAULT_PROFILE_NAME = "Built-in default"


class Control:
    """One validated entry from the profile's ``controls`` array."""

    def __init__(self, cc, channel, target, index=0, takeover="jump"):
        self.cc = cc
        self.channel = channel  # 1-16, as written in profile.json
        self.channel0 = channel - 1  # 0-15, as Live.MidiMap wants it
        self.target = target
        self.index = index
        self.takeover = takeover

    def key(self):
        """Dispatch key: which incoming (channel, cc) this control owns."""
        return (self.channel0, self.cc)

    def describe(self):
        text = f"CC {self.cc} ch {self.channel} -> {self.target}"
        if self.target in TARGETS_NEEDING_INDEX:
            text += f"[{self.index}]"
        return text


class Profile:
    def __init__(self, name, controls, problems, debug=False):
        self.name = name
        self.controls = controls
        self.problems = problems  # list of human-readable strings; empty = clean load
        self.debug = debug  # True: listen to ALL CCs and log each one to Log.txt


def default_controls():
    return [Control(cc=7, channel=1, target="selected_track_volume")]


def _is_int(value):
    # bool is a subclass of int; "channel": true must not validate.
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_control(raw, position):
    """Return (Control or None, problems) for one entry in ``controls``."""
    where = f"controls[{position}]"
    if not isinstance(raw, dict):
        return None, [f"{where}: must be an object like {{\"cc\": 7, ...}}"]

    problems = []
    # Keys beginning with "_" are reserved for comments and ignored.
    unknown = sorted(k for k in raw if k not in ALLOWED_CONTROL_KEYS and not k.startswith("_"))
    for key in unknown:
        problems.append(
            f"{where}: unknown key \"{key}\" (allowed: cc, channel, target, index, takeover)"
        )

    cc = raw.get("cc")
    if not _is_int(cc) or not 0 <= cc <= 127:
        problems.append(f"{where}: \"cc\" must be an integer 0-127, got {cc!r}")

    channel = raw.get("channel")
    if not _is_int(channel) or not 1 <= channel <= 16:
        problems.append(f"{where}: \"channel\" must be an integer 1-16, got {channel!r}")

    target = raw.get("target")
    if target not in VALID_TARGETS:
        problems.append(
            f"{where}: \"target\" must be one of {sorted(VALID_TARGETS)}, got {target!r}"
        )

    index = raw.get("index", 0)
    if target in TARGETS_NEEDING_INDEX:
        if "index" not in raw:
            problems.append(f"{where}: target \"{target}\" requires an \"index\" (0 = Send A)")
        elif not _is_int(index) or index < 0:
            problems.append(f"{where}: \"index\" must be an integer >= 0, got {index!r}")

    takeover = raw.get("takeover", "jump")
    if takeover not in VALID_TAKEOVER:
        problems.append(
            f"{where}: \"takeover\" must be one of {sorted(VALID_TAKEOVER)}, got {takeover!r}"
        )

    if problems:
        return None, problems
    return Control(cc=cc, channel=channel, target=target, index=index, takeover=takeover), []


def parse_profile(data):
    """Validate decoded JSON into a Profile. Never raises."""
    problems = []

    if not isinstance(data, dict):
        return Profile(
            DEFAULT_PROFILE_NAME,
            default_controls(),
            ["top level must be a JSON object; using default (CC 7, channel 1, volume)"],
        )

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        name = "Unnamed profile"
        if "name" in data:
            problems.append("\"name\" must be a non-empty string")

    debug = data.get("debug", False)
    if not isinstance(debug, bool):
        problems.append(f"\"debug\" must be true or false, got {debug!r}")
        debug = False

    raw_controls = data.get("controls")
    controls = []
    if not isinstance(raw_controls, list) or not raw_controls:
        problems.append("\"controls\" must be a non-empty array")
    else:
        seen = {}
        for position, raw in enumerate(raw_controls):
            control, control_problems = _validate_control(raw, position)
            problems.extend(control_problems)
            if control is None:
                continue
            if control.key() in seen:
                problems.append(
                    f"controls[{position}]: duplicate CC {control.cc} on channel "
                    f"{control.channel} (already used by controls[{seen[control.key()]}]); skipped"
                )
                continue
            seen[control.key()] = position
            controls.append(control)

    if not controls:
        problems.append("no valid controls; using default (CC 7, channel 1, volume)")
        controls = default_controls()

    return Profile(name, controls, problems, debug=debug)


def load_profile(path):
    """Read and validate profile.json at ``path``. Never raises."""
    try:
        with open(path, encoding="utf-8-sig") as handle:
            data = json.load(handle)
    except FileNotFoundError:
        return Profile(
            DEFAULT_PROFILE_NAME,
            default_controls(),
            [f"profile.json not found at {path}; using default (CC 7, channel 1, volume)"],
        )
    except json.JSONDecodeError as exc:
        return Profile(
            DEFAULT_PROFILE_NAME,
            default_controls(),
            [
                f"profile.json is not valid JSON (line {exc.lineno}, column {exc.colno}: "
                f"{exc.msg}); using default (CC 7, channel 1, volume)"
            ],
        )
    except OSError as exc:
        return Profile(
            DEFAULT_PROFILE_NAME,
            default_controls(),
            [f"could not read profile.json ({exc}); using default (CC 7, channel 1, volume)"],
        )
    return parse_profile(data)
