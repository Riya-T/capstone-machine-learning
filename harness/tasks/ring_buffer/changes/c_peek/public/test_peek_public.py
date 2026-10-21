"""Public checks for the c_peek change (looking at values without removing
them). Shown to the editor, never to the writer.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_peek/public/test_peek_public.py
"""

import pytest
from ring_buffer import BufferEmpty, RingBuffer


def test_peek_shows_the_oldest_value_without_removing_it():
    buf = RingBuffer(3)
    buf.write(4)
    buf.write(5)
    assert buf.peek() == 4
    assert buf.get_newest() == 5
    assert buf.get_size() == 2
    assert buf.read() == 4


def test_contents_are_listed_oldest_first():
    buf = RingBuffer(3)
    buf.write(1)
    buf.write(2)
    buf.write(3)
    buf.read()
    buf.write(4)
    assert buf.get_contents() == [2, 3, 4]


def test_peeking_at_an_empty_buffer_raises():
    buf = RingBuffer(2)
    assert buf.get_contents() == []
    with pytest.raises(BufferEmpty):
        buf.peek()
