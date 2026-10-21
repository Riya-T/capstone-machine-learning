"""Hidden tests for the c_peek change (looking at values without removing
them). Never shown to the writer or the editor.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_peek/private/test_peek_new.py
"""

import pytest
from ring_buffer import BufferEmpty, RingBuffer


@pytest.fixture
def buf():
    ring = RingBuffer(3)
    ring.write(1)
    ring.write(2)
    return ring


def test_peek_leaves_the_buffer_unchanged(buf):
    assert buf.peek() == 1
    assert buf.peek() == 1
    assert buf.get_size() == 2
    assert buf.get_contents() == [1, 2]


def test_peek_follows_reads(buf):
    buf.write(3)
    buf.read()
    assert buf.peek() == 2
    buf.read()
    assert buf.peek() == 3


def test_peek_matches_the_next_read(buf):
    buf.write(3)
    buf.read()
    buf.write(4)
    while buf.get_size() > 0:
        assert buf.peek() == buf.read()


def test_newest_is_the_last_value_written(buf):
    assert buf.get_newest() == 2
    buf.write(3)
    assert buf.get_newest() == 3
    buf.read()
    buf.write(4)
    assert buf.get_newest() == 4
    assert buf.get_size() == 3


def test_newest_and_oldest_agree_on_a_single_value():
    buf = RingBuffer(2)
    buf.write(9)
    assert buf.peek() == buf.get_newest() == 9


@pytest.mark.parametrize("method", ["peek", "get_newest"])
def test_looking_at_an_empty_buffer_raises(method):
    buf = RingBuffer(2)
    with pytest.raises(BufferEmpty):
        getattr(buf, method)()
    buf.write(1)
    buf.read()
    with pytest.raises(BufferEmpty):
        getattr(buf, method)()


def test_contents_are_oldest_first_after_a_wrap_around(buf):
    buf.write(3)
    assert buf.read() == 1
    assert buf.read() == 2
    buf.write(4)
    buf.write(5)
    assert buf.get_contents() == [3, 4, 5]
    assert buf.read() == 3
    buf.write(6)
    assert buf.get_contents() == [4, 5, 6]


def test_contents_of_an_empty_or_cleared_buffer_are_empty(buf):
    buf.clear()
    assert buf.get_contents() == []
    assert RingBuffer(1).get_contents() == []


def test_contents_do_not_include_read_values(buf):
    buf.read()
    assert buf.get_contents() == [2]
    buf.read()
    assert buf.get_contents() == []


def test_contents_keep_repeated_values(buf):
    buf.write(1)
    assert buf.get_contents() == [1, 2, 1]


def test_changing_the_returned_list_does_not_change_the_buffer(buf):
    contents = buf.get_contents()
    contents.append(99)
    contents[0] = -1
    assert buf.get_contents() == [1, 2]
    assert buf.get_size() == 2
    assert buf.peek() == 1


def test_contents_match_a_full_drain():
    buf = RingBuffer(4)
    for value in (5, 6, 7, 8):
        buf.write(value)
    buf.read()
    buf.read()
    buf.write(9)
    expected = buf.get_contents()
    drained = [buf.read() for _ in range(buf.get_size())]
    assert drained == expected == [7, 8, 9]
