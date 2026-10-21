"""Hidden tests for the initial io_meter spec. They decide whether a program
is correct to begin with. Never shown to the writer or the editor.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest private/test_meter_initial.py
"""

import pytest
from meter import IOMeter, MeterError

BAD_SIZES = [-1, -100, 2.5, "10", None]


@pytest.fixture
def meter():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    return io


def state(io):
    """Every count on every stream, to check that a failed call changed nothing."""
    return {
        s: (io.get_bytes_read(s), io.get_bytes_written(s), io.get_op_counts(s))
        for s in io.get_streams()
    }


# --- streams ----------------------------------------------------------------


def test_a_new_stream_has_no_traffic(meter):
    assert meter.get_bytes_read("log") == 0
    assert meter.get_bytes_written("log") == 0
    assert meter.get_op_counts("log") == (0, 0)


def test_streams_are_listed_in_opening_order():
    io = IOMeter()
    for name in ["zeta", "alpha", "mid"]:
        io.open_stream(name)
    assert io.get_streams() == ["zeta", "alpha", "mid"]


@pytest.mark.parametrize("bad_id", [""])
def test_invalid_stream_ids_are_rejected(bad_id):
    io = IOMeter()
    with pytest.raises(ValueError):
        io.open_stream(bad_id)
    assert io.get_streams() == []


def test_opening_an_open_stream_is_rejected(meter):
    meter.record_read("log", 40)
    before = state(meter)
    with pytest.raises(MeterError):
        meter.open_stream("log")
    assert state(meter) == before
    assert meter.get_streams() == ["log", "data"]


@pytest.mark.parametrize(
    "call",
    [
        lambda io: io.record_read("other", 1),
        lambda io: io.record_write("other", 1),
        lambda io: io.get_bytes_read("other"),
        lambda io: io.get_bytes_written("other"),
        lambda io: io.get_op_counts("other"),
        lambda io: io.get_bytes_read(None),
        lambda io: io.get_bytes_read(1),
        lambda io: io.record_write(None, 1),
    ],
)
def test_streams_that_are_not_open_raise_key_error(meter, call):
    meter.record_read("log", 40)
    before = state(meter)
    with pytest.raises(KeyError):
        call(meter)
    assert state(meter) == before


# --- recording --------------------------------------------------------------


def test_bytes_read_add_up(meter):
    meter.record_read("log", 100)
    meter.record_read("log", 250)
    meter.record_read("log", 1)
    assert meter.get_bytes_read("log") == 351
    assert meter.get_op_counts("log") == (3, 0)


def test_bytes_written_add_up(meter):
    meter.record_write("log", 7)
    meter.record_write("log", 8)
    assert meter.get_bytes_written("log") == 15
    assert meter.get_op_counts("log") == (0, 2)


def test_reads_and_writes_are_kept_apart(meter):
    meter.record_read("log", 100)
    meter.record_write("log", 1)
    meter.record_write("log", 2)
    assert meter.get_bytes_read("log") == 100
    assert meter.get_bytes_written("log") == 3
    assert meter.get_op_counts("log") == (1, 2)


def test_zero_byte_operations_count_as_operations(meter):
    meter.record_read("log", 0)
    meter.record_write("log", 0)
    meter.record_read("log", 0)
    assert meter.get_bytes_read("log") == 0
    assert meter.get_bytes_written("log") == 0
    assert meter.get_op_counts("log") == (2, 1)


def test_streams_do_not_share_counts(meter):
    meter.record_read("log", 10)
    meter.record_write("data", 20)
    assert meter.get_bytes_read("data") == 0
    assert meter.get_bytes_written("log") == 0
    assert meter.get_op_counts("log") == (1, 0)
    assert meter.get_op_counts("data") == (0, 1)


def test_large_sizes_are_fine(meter):
    meter.record_write("data", 10**12)
    meter.record_write("data", 10**12)
    assert meter.get_bytes_written("data") == 2 * 10**12


@pytest.mark.parametrize("size", BAD_SIZES)
@pytest.mark.parametrize(
    "call",
    [lambda io, s: io.record_read("log", s), lambda io, s: io.record_write("log", s)],
    ids=["read", "write"],
)
def test_invalid_sizes_are_rejected(meter, call, size):
    meter.record_read("log", 5)
    before = state(meter)
    with pytest.raises(ValueError):
        call(meter, size)
    assert state(meter) == before


def test_a_stream_that_is_not_open_is_reported_before_a_bad_size(meter):
    with pytest.raises(KeyError):
        meter.record_read("other", -1)
    with pytest.raises(KeyError):
        meter.record_write("other", "10")


def test_failed_calls_leave_the_counts_alone(meter):
    meter.record_read("log", 5)
    for call in (
        lambda: meter.record_read("log", -5),
        lambda: meter.record_write("log", None),
        lambda: meter.record_write("other", 5),
        lambda: meter.open_stream("log"),
    ):
        with pytest.raises((ValueError, KeyError, MeterError)):
            call()
    assert meter.get_bytes_read("log") == 5
    assert meter.get_op_counts("log") == (1, 0)
    assert meter.get_streams() == ["log", "data"]


def test_op_counts_is_a_tuple_of_two_ints(meter):
    meter.record_read("log", 3)
    counts = meter.get_op_counts("log")
    assert isinstance(counts, tuple)
    assert counts == (1, 0)


def test_meters_do_not_share_streams():
    first, second = IOMeter(), IOMeter()
    first.open_stream("log")
    first.record_read("log", 9)
    assert second.get_streams() == []
    second.open_stream("log")
    assert second.get_bytes_read("log") == 0
