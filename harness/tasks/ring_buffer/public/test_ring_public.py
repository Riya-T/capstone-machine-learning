"""Public checks for ring_buffer.py.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest public/test_ring_public.py
"""

import pytest
from ring_buffer import BufferEmpty, BufferFull, RingBuffer


def test_values_come_out_in_the_order_written():
    buf = RingBuffer(3)
    buf.write(10)
    buf.write(20)
    buf.write(30)
    assert buf.read() == 10
    assert buf.read() == 20
    assert buf.read() == 30


def test_size_and_capacity():
    buf = RingBuffer(4)
    assert (buf.get_size(), buf.get_capacity()) == (0, 4)
    buf.write(1)
    buf.write(2)
    assert buf.get_size() == 2
    buf.read()
    assert buf.get_size() == 1


def test_writing_to_a_full_buffer_raises():
    buf = RingBuffer(2)
    buf.write(1)
    buf.write(2)
    with pytest.raises(BufferFull):
        buf.write(3)
    assert buf.get_size() == 2
    assert buf.read() == 1


def test_reading_an_empty_buffer_raises():
    buf = RingBuffer(2)
    with pytest.raises(BufferEmpty):
        buf.read()


def test_space_freed_by_reads_is_written_again():
    buf = RingBuffer(3)
    buf.write(1)
    buf.write(2)
    buf.write(3)
    assert buf.read() == 1
    buf.write(4)
    assert buf.read() == 2
    assert buf.read() == 3
    assert buf.read() == 4


def test_clear_empties_the_buffer():
    buf = RingBuffer(2)
    buf.write(5)
    buf.write(6)
    buf.clear()
    assert buf.get_size() == 0
    buf.write(7)
    assert buf.read() == 7
