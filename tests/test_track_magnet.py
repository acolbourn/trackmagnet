"""Lifecycle tests for the TrackMagnet control surface against a stubbed Live.

``import Live`` only resolves inside Ableton, so these tests inject a minimal
stand-in for the ``Live`` module plus fake LOM objects (song, tracks, mixer)
and drive the script exactly the way Live does: create_instance ->
build_midi_map -> receive_midi -> selection changes -> disconnect.
"""

import sys
import types

import pytest

# ``track_magnet.py`` binds its ``Live`` reference at first import, so the
# stub must be in sys.modules before any TrackMagnet import and must be the
# same module object for the whole session; the fixture resets its state.
_FORWARDED = []


def _forward_midi_cc(script_handle, midi_map_handle, channel, cc):
    _FORWARDED.append((script_handle, midi_map_handle, channel, cc))
    return True


_LIVE = types.ModuleType("Live")
_LIVE.MidiMap = types.SimpleNamespace(
    MapMode=types.SimpleNamespace(absolute="absolute"),
    forward_midi_cc=_forward_midi_cc,
)
_LIVE.forwarded = _FORWARDED
sys.modules["Live"] = _LIVE


# --------------------------------------------------------------- Live stubs


class FakeParameter:
    def __init__(self, value=0.0):
        self.value = value


class FakeMixerDevice:
    def __init__(self, send_count=2):
        self.volume = FakeParameter(0.85)
        self.panning = FakeParameter(0.0)
        self.sends = [FakeParameter(0.0) for _ in range(send_count)]


class FakeTrack:
    def __init__(self, send_count=2):
        self.mixer_device = FakeMixerDevice(send_count)


class FakeSongView:
    def __init__(self):
        self.selected_track = FakeTrack()
        self.listeners = []

    def add_selected_track_listener(self, callback):
        self.listeners.append(callback)

    def remove_selected_track_listener(self, callback):
        self.listeners.remove(callback)

    def select(self, track):
        self.selected_track = track
        for callback in list(self.listeners):
            callback()


class FakeSong:
    def __init__(self):
        self.view = FakeSongView()


class FakeCInstance:
    def __init__(self, song):
        self._song = song
        self.logs = []
        self.shows = []

    def song(self):
        return self._song

    def handle(self):
        return 42

    def log_message(self, text):
        self.logs.append(text)

    def show_message(self, text):
        self.shows.append(text)


@pytest.fixture
def live_stub():
    """The session-wide fake ``Live`` module, with recorded calls reset."""
    _FORWARDED.clear()
    return _LIVE


def make_surface(live_stub, controls=None):
    import TrackMagnet
    from TrackMagnet import config
    from TrackMagnet import track_magnet as tm_module

    if controls is not None:
        profile = config.Profile("Test profile", controls, [])
        original = tm_module.config.load_profile
        tm_module.config.load_profile = lambda path: profile
        try:
            c_instance = FakeCInstance(FakeSong())
            surface = TrackMagnet.create_instance(c_instance)
        finally:
            tm_module.config.load_profile = original
    else:
        c_instance = FakeCInstance(FakeSong())
        surface = TrackMagnet.create_instance(c_instance)
    return surface, c_instance


def cc(channel, number, value):
    """Build the (status, data1, data2) tuple Live hands to receive_midi."""
    return (0xB0 | (channel - 1), number, value)


# --------------------------------------------------------------------- tests


def test_loads_bundled_profile_and_reports(live_stub):
    _surface, c_instance = make_surface(live_stub)
    assert any("loaded" in text for text in c_instance.shows)
    assert any("loaded" in text for text in c_instance.logs)
    assert len(c_instance.song().view.listeners) == 1


def test_build_midi_map_forwards_configured_cc(live_stub):
    surface, _c_instance = make_surface(live_stub)
    surface.build_midi_map(midi_map_handle=object())
    # bundled default profile: CC 7 on channel 1 -> 0-indexed channel 0
    assert [(call[2], call[3]) for call in live_stub.forwarded] == [(0, 7)]
    assert live_stub.forwarded[0][0] == 42  # script handle from c_instance


def test_cc_moves_selected_track_volume(live_stub):
    surface, c_instance = make_surface(live_stub)
    track = c_instance.song().view.selected_track
    surface.receive_midi(cc(1, 7, 127))
    assert track.mixer_device.volume.value == 1.0
    surface.receive_midi(cc(1, 7, 0))
    assert track.mixer_device.volume.value == 0.0


def test_volume_follows_selection_change(live_stub):
    surface, c_instance = make_surface(live_stub)
    view = c_instance.song().view
    first, second = view.selected_track, FakeTrack()

    surface.receive_midi(cc(1, 7, 127))
    assert first.mixer_device.volume.value == 1.0

    view.select(second)
    surface.receive_midi(cc(1, 7, 0))
    assert second.mixer_device.volume.value == 0.0
    assert first.mixer_device.volume.value == 1.0  # untouched after deselect


def test_unrelated_messages_ignored(live_stub):
    surface, c_instance = make_surface(live_stub)
    track = c_instance.song().view.selected_track
    before = track.mixer_device.volume.value
    surface.receive_midi((0x90, 60, 100))  # note on
    surface.receive_midi(cc(1, 8, 100))  # unconfigured CC
    surface.receive_midi(cc(2, 7, 100))  # right CC, wrong channel
    surface.receive_midi((0xF8,))  # clock tick, 1 byte
    assert track.mixer_device.volume.value == before


def test_pan_and_send_targets(live_stub):
    from TrackMagnet.config import Control

    surface, c_instance = make_surface(
        live_stub,
        controls=[
            Control(cc=10, channel=1, target="selected_track_pan"),
            Control(cc=8, channel=1, target="selected_track_send", index=1),
        ],
    )
    mixer = c_instance.song().view.selected_track.mixer_device
    surface.receive_midi(cc(1, 10, 0))
    assert mixer.panning.value == -1.0
    surface.receive_midi(cc(1, 10, 64))
    assert mixer.panning.value == 0.0
    surface.receive_midi(cc(1, 8, 127))
    assert mixer.sends[1].value == 1.0
    assert mixer.sends[0].value == 0.0


def test_send_index_out_of_range_is_harmless(live_stub):
    from TrackMagnet.config import Control

    surface, c_instance = make_surface(
        live_stub,
        controls=[Control(cc=8, channel=1, target="selected_track_send", index=5)],
    )
    surface.receive_midi(cc(1, 8, 127))  # only 2 sends exist; must not raise
    assert not any("failed to apply" in text for text in c_instance.logs)


def test_pickup_waits_then_engages_and_resets_on_selection(live_stub):
    from TrackMagnet.config import Control

    surface, c_instance = make_surface(
        live_stub,
        controls=[
            Control(cc=7, channel=1, target="selected_track_volume", takeover="pickup")
        ],
    )
    view = c_instance.song().view
    track = view.selected_track
    track.mixer_device.volume.value = 0.5  # parameter sits at CC ~64

    surface.receive_midi(cc(1, 7, 10))  # far away: no write
    assert track.mixer_device.volume.value == 0.5
    surface.receive_midi(cc(1, 7, 100))  # swept across 64: picked up, writes
    assert track.mixer_device.volume.value == pytest.approx(100 / 127)
    surface.receive_midi(cc(1, 7, 20))  # now engaged: follows freely
    assert track.mixer_device.volume.value == pytest.approx(20 / 127)

    # new selection -> must pick up again
    second = FakeTrack()
    second.mixer_device.volume.value = 0.9
    view.select(second)
    surface.receive_midi(cc(1, 7, 30))  # far from CC ~114: no write
    assert second.mixer_device.volume.value == 0.9


def test_debug_mode_forwards_everything_and_logs(live_stub):
    from TrackMagnet import config

    controls = config.default_controls()
    import TrackMagnet
    from TrackMagnet import track_magnet as tm_module

    profile = config.Profile("Debug profile", controls, [], debug=True)
    original = tm_module.config.load_profile
    tm_module.config.load_profile = lambda path: profile
    try:
        c_instance = FakeCInstance(FakeSong())
        surface = TrackMagnet.create_instance(c_instance)
    finally:
        tm_module.config.load_profile = original

    surface.build_midi_map(midi_map_handle=object())
    assert len(live_stub.forwarded) == 16 * 128  # every CC on every channel

    surface.receive_midi(cc(5, 42, 99))  # unmatched CC still gets logged
    assert any("received CC 42 ch 5 value 99" in text for text in c_instance.logs)

    track = c_instance.song().view.selected_track
    surface.receive_midi(cc(1, 7, 127))  # matched control still works in debug
    assert track.mixer_device.volume.value == 1.0
    assert any("received CC 7 ch 1 value 127" in text for text in c_instance.logs)


def test_lom_write_failure_is_logged_not_raised(live_stub):
    surface, c_instance = make_surface(live_stub)

    class ExplodingParameter:
        @property
        def value(self):
            return 0.5

        @value.setter
        def value(self, _):
            raise RuntimeError("boom")

    c_instance.song().view.selected_track.mixer_device.volume = ExplodingParameter()
    surface.receive_midi(cc(1, 7, 127))  # must not raise
    assert any("failed to apply" in text for text in c_instance.logs)


def test_disconnect_removes_listener_and_reload_is_clean(live_stub):
    surface, c_instance = make_surface(live_stub)
    view = c_instance.song().view
    assert len(view.listeners) == 1
    surface.disconnect()
    assert view.listeners == []

    # simulate Live re-instantiating the script against the same song
    import TrackMagnet

    second_instance = FakeCInstance(c_instance._song)
    second_surface = TrackMagnet.create_instance(second_instance)
    assert len(view.listeners) == 1
    second_surface.disconnect()
    assert view.listeners == []


def test_profile_error_is_redisplayed_so_it_can_be_read(live_stub):
    import TrackMagnet
    from TrackMagnet import config
    from TrackMagnet import track_magnet as tm_module

    profile = config.Profile(
        "Broken", config.default_controls(), ["controls[0]: bad thing"]
    )
    original = tm_module.config.load_profile
    tm_module.config.load_profile = lambda path: profile
    try:
        c_instance = FakeCInstance(FakeSong())
        surface = TrackMagnet.create_instance(c_instance)
    finally:
        tm_module.config.load_profile = original

    error_shows = [t for t in c_instance.shows if "bad thing" in t]
    assert len(error_shows) == 1  # shown once at load

    # Live polls update_display ~10x/second; the error re-shows every ~30
    # ticks, 5 times total, then stops nagging.
    for _ in range(1000):
        surface.update_display()
    error_shows = [t for t in c_instance.shows if "bad thing" in t]
    assert len(error_shows) == 1 + 5


def test_update_display_is_quiet_on_clean_load(live_stub):
    surface, c_instance = make_surface(live_stub)
    before = len(c_instance.shows)
    for _ in range(1000):
        surface.update_display()
    assert len(c_instance.shows) == before


def test_optional_live_callbacks_are_safe(live_stub):
    surface, _c_instance = make_surface(live_stub)
    surface.update_display()
    surface.refresh_state()
    surface.connect_script_instances([])
    assert surface.can_lock_to_devices() is False
    assert surface.suggest_input_port() == ""
    assert surface.suggest_output_port() == ""
    assert surface.suggest_map_mode(7, 0) == "absolute"
    assert surface.suggest_needs_takeover(7, 0) is True
