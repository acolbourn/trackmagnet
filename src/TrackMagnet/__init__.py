"""TrackMagnet — your controls stick to whatever track you select.

A minimal MIDI Remote Script for Ableton Live 12. Live imports this package
and calls ``create_instance`` once at load time.

The ``Live`` module import is deferred into ``create_instance`` so that the
pure-Python parts of this package (``config``, ``midi_utils``) can be imported
outside Live — by the test suite and by CI profile validation.
"""


def create_instance(c_instance):
    from .track_magnet import TrackMagnet

    return TrackMagnet(c_instance)
