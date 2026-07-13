"""Unit tests for the pure MIDI/value math used inside receive_midi."""

from TrackMagnet import midi_utils


def test_parse_cc_happy_path():
    # CC 7 = 64 on channel 1 (status 0xB0)
    assert midi_utils.parse_cc((0xB0, 7, 64)) == (0, 7, 64)
    # channel 16 (status 0xBF)
    assert midi_utils.parse_cc((0xBF, 10, 127)) == (15, 10, 127)


def test_parse_cc_rejects_non_cc_messages():
    assert midi_utils.parse_cc((0x90, 60, 100)) is None  # note on
    assert midi_utils.parse_cc((0x80, 60, 0)) is None  # note off
    assert midi_utils.parse_cc((0xE0, 0, 64)) is None  # pitch bend
    assert midi_utils.parse_cc((0xF0, 1)) is None  # sysex fragment
    assert midi_utils.parse_cc((0xB0,)) is None  # too short


def test_parse_cc_rejects_malformed_data_bytes():
    # Data bytes are 7-bit; anything larger must never reach a parameter write.
    assert midi_utils.parse_cc((0xB0, 7, 200)) is None
    assert midi_utils.parse_cc((0xB0, 200, 64)) is None
    assert midi_utils.parse_cc((0xB0, 7, -1)) is None


def test_cc_to_normalized_range():
    assert midi_utils.cc_to_normalized(0) == 0.0
    assert midi_utils.cc_to_normalized(127) == 1.0
    assert 0.49 < midi_utils.cc_to_normalized(64) < 0.51


def test_normalized_to_cc_clamps_and_inverts():
    assert midi_utils.normalized_to_cc(0.0) == 0
    assert midi_utils.normalized_to_cc(1.0) == 127
    assert midi_utils.normalized_to_cc(-0.5) == 0
    assert midi_utils.normalized_to_cc(1.5) == 127
    for value in range(128):
        assert midi_utils.normalized_to_cc(midi_utils.cc_to_normalized(value)) == value


def test_pan_mapping_endpoints_and_center():
    assert midi_utils.cc_to_pan(0) == -1.0
    assert midi_utils.cc_to_pan(64) == 0.0
    assert midi_utils.cc_to_pan(127) == 1.0


def test_pan_round_trip():
    for value in range(128):
        assert midi_utils.pan_to_cc(midi_utils.cc_to_pan(value)) == value


def test_pan_to_cc_clamps():
    assert midi_utils.pan_to_cc(-2.0) == 0
    assert midi_utils.pan_to_cc(2.0) == 127


def test_pickup_within_threshold():
    assert midi_utils.pickup_reached(current_cc=60, incoming=60, last_incoming=None)
    assert midi_utils.pickup_reached(current_cc=60, incoming=61, last_incoming=None)
    assert not midi_utils.pickup_reached(current_cc=60, incoming=90, last_incoming=None)


def test_pickup_by_crossing():
    # knob swept 40 -> 80 while parameter sits at 60: crossed, picked up
    assert midi_utils.pickup_reached(current_cc=60, incoming=80, last_incoming=40)
    # swept downward across it too
    assert midi_utils.pickup_reached(current_cc=60, incoming=40, last_incoming=80)
    # moved but never crossed
    assert not midi_utils.pickup_reached(current_cc=60, incoming=30, last_incoming=10)
