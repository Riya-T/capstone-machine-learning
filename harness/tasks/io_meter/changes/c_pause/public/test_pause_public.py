"""Public checks for the c_pause change (paused streams). Shown to the
editor, never to the writer.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/public/test_pause_public.py
"""

import pytest
from meter import IOMeter, StreamPaused


def test_a_paused_stream_records_nothing():
    io = IOMeter()
    io.open_stream("log")
    io.record_read("log", 10)
    io.pause("log")
    assert io.is_paused("log")
    with pytest.raises(StreamPaused):
        io.record_read("log", 5)
    with pytest.raises(StreamPaused):
        io.record_write("log", 0)
    assert io.get_bytes_read("log") == 10
    assert io.get_op_counts("log") == (1, 0)


def test_a_resumed_stream_records_again():
    io = IOMeter()
    io.open_stream("log")
    io.pause("log")
    io.resume("log")
    assert not io.is_paused("log")
    io.record_write("log", 7)
    assert io.get_bytes_written("log") == 7
