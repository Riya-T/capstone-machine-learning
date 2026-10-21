"""Hidden tests for the initial ring_buffer spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest private/test_ring_initial.py
"""

import pytest
from ring_buffer import BufferEmpty, BufferFull, RingBuffer, RingError

BAD_CAPACITIES = [0, -1, 2.5, "3", None]
BAD_VALUES = [1.5, "7", None, [1]]


@pytest.fixture
def buf():
    return RingBuffer(3)


def drain(ring):
    """Read everything out, oldest first. Empties the buffer."""
    values = []
    while ring.get_size() > 0:
        values.append(ring.read())
    return values


# --- capacity ---------------------------------------------------------------


def test_a_new_buffer_is_empty(buf):
    assert buf.get_size() == 0
    assert buf.get_capacity() == 3
    assert drain(buf) == []


@pytest.mark.parametrize("capacity", BAD_CAPACITIES)
def test_invalid_capacities_are_rejected(capacity):
    with pytest.raises(ValueError):
        RingBuffer(capacity)


def test_a_capacity_of_one_works():
    buf = RingBuffer(1)
    buf.write(9)
    assert buf.get_size() == 1
    with pytest.raises(BufferFull):
        buf.write(10)
    assert buf.read() == 9
    buf.write(11)
    assert buf.read() == 11


def test_size_follows_writes_and_reads(buf):
    sizes = [buf.get_size()]
    for value in (1, 2, 3):
        buf.write(value)
        sizes.append(buf.get_size())
    buf.read()
    sizes.append(buf.get_size())
    buf.read()
    buf.read()
    sizes.append(buf.get_size())
    assert sizes == [0, 1, 2, 3, 2, 0]


def test_size_never_passes_the_capacity(buf):
    for value in (1, 2, 3):
        buf.write(value)
    with pytest.raises(BufferFull):
        buf.write(4)
    assert buf.get_size() == 3


# --- writing and reading ----------------------------------------------------


def test_read_returns_the_oldest_value(buf):
    buf.write(7)
    buf.write(8)
    assert buf.read() == 7
    assert buf.read() == 8


def test_read_removes_exactly_one_value(buf):
    buf.write(1)
    buf.write(2)
    buf.read()
    assert buf.get_size() == 1
    assert buf.read() == 2
    assert buf.get_size() == 0


def test_a_full_buffer_rejects_a_write_and_keeps_its_values(buf):
    for value in (1, 2, 3):
        buf.write(value)
    with pytest.raises(BufferFull):
        buf.write(4)
    assert buf.get_size() == 3
    assert drain(buf) == [1, 2, 3]


def test_reading_past_the_last_value_raises(buf):
    buf.write(1)
    buf.read()
    with pytest.raises(BufferEmpty):
        buf.read()
    assert buf.get_size() == 0


@pytest.mark.parametrize("value", BAD_VALUES)
def test_invalid_values_are_rejected(buf, value):
    buf.write(1)
    with pytest.raises(ValueError):
        buf.write(value)
    assert buf.get_size() == 1
    assert drain(buf) == [1]


def test_a_bad_value_is_reported_before_a_full_buffer(buf):
    for value in (1, 2, 3):
        buf.write(value)
    with pytest.raises(ValueError):
        buf.write("4")
    assert drain(buf) == [1, 2, 3]


def test_zero_negative_and_repeated_values_are_stored(buf):
    buf.write(0)
    buf.write(-5)
    buf.write(0)
    assert drain(buf) == [0, -5, 0]


def test_values_wrap_around_many_times(buf):
    buf.write(1)
    buf.write(2)
    buf.write(3)
    assert buf.read() == 1
    assert buf.read() == 2
    buf.write(4)
    buf.write(5)
    assert buf.get_size() == 3
    assert buf.read() == 3
    buf.write(6)
    assert drain(buf) == [4, 5, 6]
    buf.write(7)
    buf.write(8)
    assert drain(buf) == [7, 8]


def test_the_buffer_is_full_again_after_a_wrap_around(buf):
    for value in (1, 2, 3):
        buf.write(value)
    buf.read()
    buf.write(4)
    with pytest.raises(BufferFull):
        buf.write(5)
    assert drain(buf) == [2, 3, 4]


# --- clearing ---------------------------------------------------------------


def test_clearing_an_empty_buffer_is_allowed(buf):
    buf.clear()
    assert buf.get_size() == 0
    buf.write(1)
    assert buf.read() == 1


def test_reading_after_clear_raises(buf):
    buf.write(1)
    buf.write(2)
    buf.clear()
    with pytest.raises(BufferEmpty):
        buf.read()


def test_a_cleared_buffer_holds_a_full_set_of_new_values(buf):
    buf.write(1)
    buf.write(2)
    buf.read()
    buf.clear()
    for value in (4, 5, 6):
        buf.write(value)
    assert buf.get_size() == 3
    assert drain(buf) == [4, 5, 6]
    assert buf.get_capacity() == 3


# --- errors and independence -----------------------------------------------


def test_errors_share_the_ring_error_base():
    assert issubclass(BufferFull, RingError)
    assert issubclass(BufferEmpty, RingError)
    assert not issubclass(BufferFull, BufferEmpty)
    assert not issubclass(BufferEmpty, BufferFull)


def test_buffers_do_not_share_values():
    first, second = RingBuffer(2), RingBuffer(2)
    first.write(1)
    assert second.get_size() == 0
    with pytest.raises(BufferEmpty):
        second.read()
    assert first.read() == 1
