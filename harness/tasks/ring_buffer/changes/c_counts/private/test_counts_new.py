"""Hidden tests for the c_counts change (lifetime totals). Never shown to
the writer or the editor.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/private/test_counts_new.py
"""

import pytest
from ring_buffer import BufferEmpty, BufferFull, RingBuffer


@pytest.fixture
def buf():
    return RingBuffer(3)


def totals(ring):
    return (ring.get_total_written(), ring.get_total_read(), ring.get_total_discarded())


def check_invariant(ring):
    written, read, discarded = totals(ring)
    assert ring.get_size() == written - read - discarded


def test_a_new_buffer_has_zero_totals(buf):
    assert totals(buf) == (0, 0, 0)
    check_invariant(buf)


def test_every_successful_write_is_counted(buf):
    for value in (1, 2, 3):
        buf.write(value)
    assert buf.get_total_written() == 3
    check_invariant(buf)


def test_every_successful_read_is_counted(buf):
    buf.write(1)
    buf.write(2)
    buf.read()
    assert totals(buf) == (2, 1, 0)
    buf.read()
    assert totals(buf) == (2, 2, 0)
    check_invariant(buf)


def test_totals_keep_growing_across_wrap_arounds(buf):
    for value in (1, 2, 3):
        buf.write(value)
    buf.read()
    buf.read()
    buf.write(4)
    buf.write(5)
    buf.read()
    assert totals(buf) == (5, 3, 0)
    check_invariant(buf)


def test_clear_discards_what_the_buffer_held(buf):
    buf.write(1)
    buf.write(2)
    buf.write(3)
    buf.read()
    buf.clear()
    assert totals(buf) == (3, 1, 2)
    assert buf.get_size() == 0
    check_invariant(buf)


def test_clearing_an_empty_buffer_discards_nothing(buf):
    buf.clear()
    buf.write(1)
    buf.read()
    buf.clear()
    assert totals(buf) == (1, 1, 0)


def test_clear_does_not_reset_the_totals(buf):
    buf.write(1)
    buf.read()
    buf.write(2)
    buf.clear()
    buf.write(3)
    assert totals(buf) == (3, 1, 1)
    check_invariant(buf)


def test_overwrites_count_as_written_and_discarded(buf):
    buf.enable_overwrite()
    for value in (1, 2, 3):
        buf.write(value)
    buf.write(4)
    assert totals(buf) == (4, 0, 1)
    buf.write(5)
    buf.write(6)
    assert totals(buf) == (6, 0, 3)
    assert buf.get_size() == 3
    check_invariant(buf)


def test_overwrite_mode_with_room_discards_nothing(buf):
    buf.enable_overwrite()
    buf.write(1)
    buf.write(2)
    assert totals(buf) == (2, 0, 0)


def test_a_full_write_without_overwrite_counts_nothing(buf):
    for value in (1, 2, 3):
        buf.write(value)
    with pytest.raises(BufferFull):
        buf.write(4)
    assert totals(buf) == (3, 0, 0)


@pytest.mark.parametrize("value", [1.5, "2", None])
def test_a_rejected_value_counts_nothing(buf, value):
    buf.write(1)
    with pytest.raises(ValueError):
        buf.write(value)
    assert totals(buf) == (1, 0, 0)
    buf.enable_overwrite()
    buf.write(2)
    buf.write(3)
    with pytest.raises(ValueError):
        buf.write(value)
    assert totals(buf) == (3, 0, 0)


def test_a_failed_read_counts_nothing(buf):
    with pytest.raises(BufferEmpty):
        buf.read()
    buf.write(1)
    buf.read()
    with pytest.raises(BufferEmpty):
        buf.read()
    assert totals(buf) == (1, 1, 0)


def test_totals_belong_to_one_buffer():
    first, second = RingBuffer(2), RingBuffer(2)
    first.write(1)
    first.read()
    assert totals(second) == (0, 0, 0)
    assert totals(first) == (1, 1, 0)
