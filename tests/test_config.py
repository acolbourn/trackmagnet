"""Unit tests for profile.json loading and validation.

These run in plain CPython 3.11 (no Live) — config.py is deliberately
Live-free so the exact code that runs inside Live is what's tested here.
"""

import json

from TrackMagnet import config


def make_profile(**overrides):
    data = {
        "name": "Test",
        "controls": [{"cc": 7, "channel": 1, "target": "selected_track_volume"}],
    }
    data.update(overrides)
    return data


def test_valid_minimal_profile():
    profile = config.parse_profile(make_profile())
    assert profile.problems == []
    assert profile.name == "Test"
    assert len(profile.controls) == 1
    control = profile.controls[0]
    assert control.cc == 7
    assert control.channel == 1
    assert control.channel0 == 0
    assert control.target == "selected_track_volume"
    assert control.takeover == "jump"


def test_channel_is_converted_to_zero_indexed():
    profile = config.parse_profile(
        make_profile(controls=[{"cc": 1, "channel": 16, "target": "selected_track_pan"}])
    )
    assert profile.controls[0].channel0 == 15


def test_multiple_controls_and_send_index():
    profile = config.parse_profile(
        make_profile(
            controls=[
                {"cc": 7, "channel": 1, "target": "selected_track_volume"},
                {"cc": 10, "channel": 1, "target": "selected_track_pan"},
                {"cc": 8, "channel": 1, "target": "selected_track_send", "index": 0},
            ]
        )
    )
    assert profile.problems == []
    assert [c.target for c in profile.controls] == [
        "selected_track_volume",
        "selected_track_pan",
        "selected_track_send",
    ]
    assert profile.controls[2].index == 0


def test_send_requires_index():
    profile = config.parse_profile(
        make_profile(controls=[{"cc": 8, "channel": 1, "target": "selected_track_send"}])
    )
    assert any("index" in p for p in profile.problems)
    # invalid control skipped -> fallback to default
    assert profile.controls[0].cc == 7


def test_cc_out_of_range_falls_back_to_default():
    profile = config.parse_profile(
        make_profile(controls=[{"cc": 128, "channel": 1, "target": "selected_track_volume"}])
    )
    assert any('"cc"' in p for p in profile.problems)
    assert any("default" in p for p in profile.problems)
    assert profile.controls[0].cc == 7
    assert profile.controls[0].target == "selected_track_volume"


def test_channel_out_of_range_rejected():
    for bad in (0, 17, -1):
        profile = config.parse_profile(
            make_profile(controls=[{"cc": 7, "channel": bad, "target": "selected_track_volume"}])
        )
        assert any('"channel"' in p for p in profile.problems), bad


def test_bool_is_not_a_valid_integer():
    profile = config.parse_profile(
        make_profile(controls=[{"cc": True, "channel": 1, "target": "selected_track_volume"}])
    )
    assert any('"cc"' in p for p in profile.problems)


def test_unknown_target_rejected():
    profile = config.parse_profile(
        make_profile(controls=[{"cc": 7, "channel": 1, "target": "master_volume"}])
    )
    assert any('"target"' in p for p in profile.problems)


def test_unknown_key_reported_but_comment_keys_ignored():
    profile = config.parse_profile(
        make_profile(
            controls=[
                {
                    "cc": 7,
                    "channel": 1,
                    "target": "selected_track_volume",
                    "_comment": "this is fine",
                }
            ]
        )
    )
    assert profile.problems == []

    profile = config.parse_profile(
        make_profile(
            controls=[{"cc": 7, "chanel": 1, "target": "selected_track_volume"}]
        )
    )
    assert any('"chanel"' in p for p in profile.problems)


def test_duplicate_cc_channel_keeps_first():
    profile = config.parse_profile(
        make_profile(
            controls=[
                {"cc": 7, "channel": 1, "target": "selected_track_volume"},
                {"cc": 7, "channel": 1, "target": "selected_track_pan"},
            ]
        )
    )
    assert any("duplicate" in p for p in profile.problems)
    assert len(profile.controls) == 1
    assert profile.controls[0].target == "selected_track_volume"


def test_same_cc_on_different_channels_is_fine():
    profile = config.parse_profile(
        make_profile(
            controls=[
                {"cc": 7, "channel": 1, "target": "selected_track_volume"},
                {"cc": 7, "channel": 2, "target": "selected_track_pan"},
            ]
        )
    )
    assert profile.problems == []
    assert len(profile.controls) == 2


def test_takeover_pickup_accepted_and_bad_value_rejected():
    profile = config.parse_profile(
        make_profile(
            controls=[
                {"cc": 7, "channel": 1, "target": "selected_track_volume", "takeover": "pickup"}
            ]
        )
    )
    assert profile.problems == []
    assert profile.controls[0].takeover == "pickup"

    profile = config.parse_profile(
        make_profile(
            controls=[
                {"cc": 7, "channel": 1, "target": "selected_track_volume", "takeover": "soft"}
            ]
        )
    )
    assert any('"takeover"' in p for p in profile.problems)


def test_empty_or_missing_controls_falls_back():
    for data in (make_profile(controls=[]), {"name": "x"}, [], "nope", 42):
        profile = config.parse_profile(data)
        assert profile.problems, data
        assert len(profile.controls) == 1
        assert profile.controls[0].cc == 7


def test_debug_flag_parsed_and_defaults_off():
    profile = config.parse_profile(make_profile())
    assert profile.debug is False

    profile = config.parse_profile(make_profile(debug=True))
    assert profile.problems == []
    assert profile.debug is True

    profile = config.parse_profile(make_profile(debug="yes"))
    assert any('"debug"' in p for p in profile.problems)
    assert profile.debug is False


def test_load_profile_missing_file(tmp_path):
    profile = config.load_profile(str(tmp_path / "nope.json"))
    assert any("not found" in p for p in profile.problems)
    assert profile.controls[0].cc == 7


def test_load_profile_invalid_json(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text("{ not json", encoding="utf-8")
    profile = config.load_profile(str(path))
    assert any("not valid JSON" in p for p in profile.problems)
    assert profile.controls[0].cc == 7


def test_load_profile_survives_utf16_file(tmp_path):
    # Windows Notepad's "Unicode" encoding and PowerShell's `>` redirect both
    # write UTF-16; the script must fall back, not die.
    path = tmp_path / "profile.json"
    path.write_bytes(json.dumps(make_profile()).encode("utf-16"))
    profile = config.load_profile(str(path))
    assert any("UTF-8" in p for p in profile.problems)
    assert profile.controls[0].cc == 7


def test_index_on_non_send_target_is_flagged():
    profile = config.parse_profile(
        make_profile(
            controls=[{"cc": 7, "channel": 1, "target": "selected_track_volume", "index": 1}]
        )
    )
    assert any("only valid for" in p for p in profile.problems)


def test_top_level_unknown_key_flagged_but_comments_ignored():
    profile = config.parse_profile(make_profile(debgu=True))  # typo'd "debug"
    assert any('"debgu"' in p for p in profile.problems)
    assert profile.debug is False

    profile = config.parse_profile(make_profile(_comment="top-level comments are fine"))
    assert profile.problems == []


def test_load_profile_tolerates_utf8_bom(tmp_path):
    # Windows Notepad historically saves UTF-8 with a BOM.
    path = tmp_path / "profile.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps(make_profile()).encode("utf-8"))
    profile = config.load_profile(str(path))
    assert profile.problems == []


def test_bundled_default_profile_is_valid():
    import pathlib

    bundled = pathlib.Path(__file__).resolve().parents[1] / "src" / "TrackMagnet" / "profile.json"
    profile = config.load_profile(str(bundled))
    assert profile.problems == []
