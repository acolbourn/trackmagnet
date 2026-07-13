"""Pure MIDI/value math, kept free of ``Live`` imports so it is unit-testable.

Live's mixer volume is a normalized 0.0-1.0 DeviceParameter (unity/0 dB sits
near 0.85 — it is NOT dB and NOT 0-127). Pan is -1.0..1.0 with 0.0 center.
"""

CC_STATUS = 0xB0


def parse_cc(midi_bytes):
    """Return (channel0, cc, value) for a Control Change message, else None.

    ``midi_bytes`` is the tuple Live passes to ``receive_midi``; anything that
    is not a 3-byte CC message (notes, pitch bend, sysex) returns None.
    """
    if len(midi_bytes) < 3:
        return None
    status, data1, data2 = midi_bytes[0], midi_bytes[1], midi_bytes[2]
    if status & 0xF0 != CC_STATUS:
        return None
    if not (0 <= data1 <= 127 and 0 <= data2 <= 127):
        return None  # malformed data bytes; never write out-of-range values
    return (status & 0x0F, data1, data2)


def cc_to_normalized(value):
    """0-127 -> 0.0-1.0 (volume, sends)."""
    return value / 127.0


def normalized_to_cc(value):
    """0.0-1.0 -> 0-127, clamped (used to compare a parameter to knob units)."""
    return round(min(max(value, 0.0), 1.0) * 127)


def cc_to_pan(value):
    """0-127 -> -1.0..1.0: 0 -> -1, 64 -> 0 (exact center), 127 -> 1."""
    if value < 64:
        return (value - 64) / 64.0
    return (value - 64) / 63.0


def pan_to_cc(value):
    """-1.0..1.0 -> 0-127, inverse of cc_to_pan, clamped."""
    value = min(max(value, -1.0), 1.0)
    if value < 0:
        return round(64 + value * 64)
    return round(64 + value * 63)


def pickup_reached(current_cc, incoming, last_incoming, threshold=1):
    """Soft-takeover (pickup): has the knob caught up with the parameter?

    True when the incoming value lands within ``threshold`` of the parameter's
    current position (in 0-127 units), or when the knob swept across it since
    the previous message (so a fast turn can't tunnel past the pickup point).
    """
    if abs(incoming - current_cc) <= threshold:
        return True
    if last_incoming is None:
        return False
    low, high = sorted((last_incoming, incoming))
    return low <= current_cc <= high
