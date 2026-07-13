"""The TrackMagnet control surface.

A raw Live 12 remote script — no _Framework, no ableton.v2/v3. The whole data
flow is: ``build_midi_map`` asks Live to forward the configured CCs here,
``receive_midi`` parses the bytes and writes the value onto the currently
selected track. Because the target track is resolved on every message, the
controls follow the selection with no remapping and no rebuild.

Listener hygiene rule: every ``add_*_listener`` made in ``__init__`` has a
matching ``remove_*_listener`` in ``disconnect``. Orphaned listeners are the
number-one cause of crashes across script reloads.
"""

import os

import Live

from . import config, midi_utils
from .version import __version__


class TrackMagnet:
    def __init__(self, c_instance):
        self._c_instance = c_instance
        self._song = c_instance.song()

        profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profile.json")
        profile = config.load_profile(profile_path)
        self._controls = profile.controls
        self._debug = profile.debug
        self._dispatch = {control.key(): control for control in self._controls}

        # Soft-takeover state, reset whenever the track selection changes so a
        # "pickup" control must catch up with each newly selected track.
        self._picked_up = set()
        self._last_seen = {}

        self._selection_listener_added = False
        try:
            self._song.view.add_selected_track_listener(self._on_selected_track_changed)
            self._selection_listener_added = True
        except Exception as exc:
            self.log_message(f"could not add selected-track listener: {exc!r}")

        # Live's status-bar messages vanish after a couple of seconds — too
        # fast to read an error. Re-show the first problem a few times from
        # update_display (polled ~10x/second) so it can actually be read.
        self._error_text = None
        self._error_redisplays = 0
        self._display_ticks = 0

        for problem in profile.problems:
            self.log_message(f"profile.json: {problem}")
        if profile.problems:
            self._error_text = f"profile.json problem — {profile.problems[0]} (details in Log.txt)"
            self._error_redisplays = 5
            self.show_message(self._error_text)
        else:
            self.show_message(
                f"v{__version__} loaded — profile \"{profile.name}\", "
                f"{len(self._controls)} control(s)"
            )
        self.log_message(
            f"v{__version__} loaded — profile \"{profile.name}\": "
            + "; ".join(control.describe() for control in self._controls)
        )
        if self._debug:
            self.log_message(
                "debug mode ON — listening to ALL CCs on ALL channels and logging "
                "each one here; set \"debug\": false in profile.json when done"
            )

    # ------------------------------------------------------------------ MIDI

    def build_midi_map(self, midi_map_handle):
        """Called by Live at startup and after request_rebuild_midi_map().

        ``midi_map_handle`` is only valid inside this call. Channel here is
        0-indexed (0-15); profile.json uses 1-16 and Control stores both.
        """
        script_handle = self._c_instance.handle()
        if self._debug:
            # Debug mode: listen to every CC on every channel so receive_midi
            # can log whatever the controller actually sends.
            for channel0 in range(16):
                for cc in range(128):
                    Live.MidiMap.forward_midi_cc(script_handle, midi_map_handle, channel0, cc)
            return
        for control in self._controls:
            Live.MidiMap.forward_midi_cc(
                script_handle, midi_map_handle, control.channel0, control.cc
            )

    def receive_midi(self, midi_bytes):
        """Called by Live with each forwarded message as a tuple of ints."""
        parsed = midi_utils.parse_cc(midi_bytes)
        if parsed is None:
            if self._debug:
                self.log_message(f"debug: non-CC message {tuple(midi_bytes)!r}")
            return
        channel0, cc, value = parsed
        control = self._dispatch.get((channel0, cc))
        if self._debug:
            matched = control.describe() if control else "no matching control"
            self.log_message(
                f"debug: received CC {cc} ch {channel0 + 1} value {value} ({matched})"
            )
        if control is None:
            return
        try:
            self._apply(control, value)
        except Exception as exc:
            # A LOM write failing (e.g. an API change in a point release) must
            # degrade gracefully, never crash Live.
            self.log_message(f"failed to apply {control.describe()}: {exc!r}")

    def _apply(self, control, value):
        track = self._song.view.selected_track
        if track is None:
            return
        parameter = self._resolve_parameter(control, track)
        if parameter is None:
            return

        if control.target == "selected_track_pan":
            new_value = midi_utils.cc_to_pan(value)
            current_cc = midi_utils.pan_to_cc(parameter.value)
        else:
            new_value = midi_utils.cc_to_normalized(value)
            current_cc = midi_utils.normalized_to_cc(parameter.value)

        if control.takeover == "pickup":
            key = control.key()
            last = self._last_seen.get(key)
            self._last_seen[key] = value
            if key not in self._picked_up:
                if midi_utils.pickup_reached(current_cc, value, last):
                    self._picked_up.add(key)
                else:
                    return  # knob hasn't caught up with the parameter yet

        parameter.value = new_value

    def _resolve_parameter(self, control, track):
        mixer = track.mixer_device
        if mixer is None:
            return None
        if control.target == "selected_track_volume":
            return mixer.volume
        if control.target == "selected_track_pan":
            return mixer.panning
        if control.target == "selected_track_send":
            sends = mixer.sends
            if control.index < len(sends):
                return sends[control.index]
            return None  # e.g. Master track has no sends, or index too high
        return None

    # ------------------------------------------------------------- listeners

    def _on_selected_track_changed(self):
        self._picked_up.clear()
        self._last_seen.clear()

    # -------------------------------------------------------------- lifecycle

    def disconnect(self):
        """Called by Live on teardown/reload. Remove every listener we added."""
        if self._selection_listener_added:
            try:
                self._song.view.remove_selected_track_listener(
                    self._on_selected_track_changed
                )
            except Exception as exc:
                self.log_message(f"could not remove selected-track listener: {exc!r}")
            self._selection_listener_added = False
        self.log_message("disconnected")
        self._song = None
        self._c_instance = None

    # ------------------------------------------- optional Live callbacks

    # Live probes scripts for these; harmless no-op/default implementations
    # keep Log.txt free of AttributeError noise.

    def update_display(self):
        # Called by Live roughly every 100 ms. Used only to keep a profile
        # error readable: re-show it every ~3 s, a handful of times.
        if self._error_text is None or self._error_redisplays <= 0:
            return
        self._display_ticks += 1
        if self._display_ticks % 30 == 0:
            self.show_message(self._error_text)
            self._error_redisplays -= 1

    def refresh_state(self):
        pass

    def connect_script_instances(self, instanciated_scripts):
        pass

    def can_lock_to_devices(self):
        return False

    def suggest_input_port(self):
        return ""

    def suggest_output_port(self):
        return ""

    def suggest_map_mode(self, cc_no, channel):
        return Live.MidiMap.MapMode.absolute

    def suggest_needs_takeover(self, cc_no, channel):
        return True

    # ---------------------------------------------------------------- helpers

    def log_message(self, text):
        try:
            self._c_instance.log_message(f"TrackMagnet: {text}")
        except Exception:
            pass

    def show_message(self, text):
        try:
            self._c_instance.show_message(f"TrackMagnet: {text}")
        except Exception:
            pass
