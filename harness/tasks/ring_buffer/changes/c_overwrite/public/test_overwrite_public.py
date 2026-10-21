"""Public checks for the c_overwrite change (overwrite mode). Shown to the
editor, never to the writer.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overwrite/public/test_overwrite_public.py
"""

import pytest
from ring_buffer import BufferFull, RingBuffer


def test_overwrite_mode_replaces_the_oldest_value():
    buf = RingBuffer(3)
    buf.enable_overwrite()
    assert buf.is_overwrite_enabled()
    for value in (1, 2, 3, 4):
        buf.write(value)
    assert buf.get_size() == 3
    assert buf.read() == 2
    assert buf.read() == 3
    assert buf.read() == 4


def test_a_full_buffer_still_raises_when_overwrite_is_disabled():
    buf = RingBuffer(2)
    assert not buf.is_overwrite_enabled()
    buf.write(1)
    buf.write(2)
    with pytest.raises(BufferFull):
        buf.write(3)
    buf.enable_overwrite()
    buf.disable_overwrite()
    with pytest.raises(BufferFull):
        buf.write(3)
    assert buf.read() == 1
