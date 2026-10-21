"""Hidden tests for the c_overwrite change (overwrite mode). Never shown to
the writer or the editor.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_overwrite/private/test_overwrite_new.py
"""

import pytest
from ring_buffer import BufferFull, RingBuffer


@pytest.fixture
def full():
    """A full buffer of capacity 3 with overwrite mode enabled."""
    ring = RingBuffer(3)
    ring.enable_overwrite()
    for value in (1, 2, 3):
        ring.write(value)
    return ring


def drain(ring):
    values = []
    while ring.get_size() > 0:
        values.append(ring.read())
    return values


def test_overwrite_mode_starts_disabled():
    assert not RingBuffer(2).is_overwrite_enabled()


def test_switching_twice_is_harmless():
    buf = RingBuffer(2)
    buf.enable_overwrite()
    buf.enable_overwrite()
    assert buf.is_overwrite_enabled()
    buf.disable_overwrite()
    buf.disable_overwrite()
    assert not buf.is_overwrite_enabled()


def test_the_oldest_value_is_dropped_and_the_new_one_comes_last(full):
    full.write(4)
    assert full.get_size() == 3
    assert drain(full) == [2, 3, 4]


def test_several_overwrites_in_a_row(full):
    full.write(4)
    full.write(5)
    full.write(6)
    full.write(7)
    assert full.get_size() == 3
    assert drain(full) == [5, 6, 7]


def test_overwriting_after_reads_and_writes_keeps_the_order(full):
    assert full.read() == 1
    full.write(4)  # full again: 2, 3, 4
    full.write(5)  # drops 2
    assert full.read() == 3
    full.write(6)
    full.write(7)  # drops 4
    assert drain(full) == [5, 6, 7]


def test_overwrite_with_a_capacity_of_one():
    buf = RingBuffer(1)
    buf.enable_overwrite()
    buf.write(1)
    buf.write(2)
    assert buf.get_size() == 1
    assert buf.read() == 2


def test_disabling_overwrite_makes_a_full_buffer_raise_again(full):
    full.disable_overwrite()
    with pytest.raises(BufferFull):
        full.write(4)
    assert drain(full) == [1, 2, 3]


def test_enabling_overwrite_on_a_full_buffer_allows_the_next_write():
    buf = RingBuffer(2)
    buf.write(1)
    buf.write(2)
    with pytest.raises(BufferFull):
        buf.write(3)
    buf.enable_overwrite()
    buf.write(3)
    assert drain(buf) == [2, 3]


def test_a_bad_value_is_rejected_before_anything_is_dropped(full):
    with pytest.raises(ValueError):
        full.write("4")
    with pytest.raises(ValueError):
        full.write(None)
    assert full.get_size() == 3
    assert drain(full) == [1, 2, 3]


def test_switching_modes_does_not_change_the_values(full):
    full.disable_overwrite()
    full.enable_overwrite()
    full.disable_overwrite()
    assert full.get_size() == 3
    assert drain(full) == [1, 2, 3]


def test_overwrite_mode_does_not_affect_a_buffer_with_room():
    buf = RingBuffer(3)
    buf.enable_overwrite()
    buf.write(1)
    buf.write(2)
    assert buf.get_size() == 2
    assert drain(buf) == [1, 2]


def test_clear_works_in_overwrite_mode(full):
    full.write(4)
    full.clear()
    assert full.get_size() == 0
    full.write(5)
    full.write(6)
    full.write(7)
    full.write(8)
    assert drain(full) == [6, 7, 8]
