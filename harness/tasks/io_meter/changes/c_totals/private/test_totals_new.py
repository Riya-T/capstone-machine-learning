"""Hidden tests for the c_totals change (totals across streams and the
largest operation). Never shown to the writer or the editor.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/private/test_totals_new.py
"""

import pytest
from meter import IOMeter, MeterError


@pytest.fixture
def meter():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    return io


def state(io):
    return {
        s: (io.get_bytes_read(s), io.get_bytes_written(s), io.get_op_counts(s))
        for s in io.get_streams()
    }


def test_an_empty_meter_has_zero_totals():
    io = IOMeter()
    assert io.get_total_bytes() == (0, 0)
    assert io.get_total_ops() == 0


def test_total_bytes_keeps_reads_and_writes_apart(meter):
    meter.record_read("log", 100)
    meter.record_write("log", 1)
    meter.record_read("data", 20)
    meter.record_write("data", 2)
    assert meter.get_total_bytes() == (120, 3)


def test_total_ops_counts_zero_byte_operations(meter):
    meter.record_read("log", 0)
    meter.record_write("data", 0)
    meter.record_write("data", 5)
    assert meter.get_total_ops() == 3
    assert meter.get_total_bytes() == (0, 5)


def test_failed_calls_do_not_reach_the_totals(meter):
    meter.record_read("log", 10)
    for call in (
        lambda: meter.record_read("log", -1),
        lambda: meter.record_write("other", 5),
    ):
        with pytest.raises((ValueError, KeyError)):
            call()
    assert meter.get_total_bytes() == (10, 0)
    assert meter.get_total_ops() == 1


def test_largest_op_takes_reads_and_writes_together(meter):
    meter.record_write("log", 30)
    meter.record_read("log", 70)
    meter.record_write("log", 50)
    assert meter.get_largest_op("log") == 70
    meter.record_write("log", 71)
    assert meter.get_largest_op("log") == 71


def test_largest_op_is_per_stream(meter):
    meter.record_read("log", 500)
    meter.record_read("data", 5)
    assert meter.get_largest_op("log") == 500
    assert meter.get_largest_op("data") == 5


def test_largest_op_is_zero_without_operations(meter):
    assert meter.get_largest_op("log") == 0
    meter.record_read("log", 0)
    assert meter.get_largest_op("log") == 0


@pytest.mark.parametrize("stream_id", ["other", None, 1])
def test_largest_op_on_an_unknown_stream_raises_key_error(meter, stream_id):
    with pytest.raises(KeyError):
        meter.get_largest_op(stream_id)


def test_busiest_stream_counts_operations_not_bytes(meter):
    meter.record_write("log", 10**6)
    meter.record_read("data", 1)
    meter.record_write("data", 1)
    assert meter.get_busiest_stream() == "data"
    meter.record_read("log", 1)
    meter.record_read("log", 1)
    assert meter.get_busiest_stream() == "log"


def test_busiest_stream_ties_go_to_the_stream_opened_first(meter):
    assert meter.get_busiest_stream() == "log"
    meter.record_read("data", 1)
    meter.record_read("log", 1)
    assert meter.get_busiest_stream() == "log"
    meter.open_stream("late")
    meter.record_read("late", 1)
    assert meter.get_busiest_stream() == "log"


def test_busiest_stream_without_streams_raises():
    io = IOMeter()
    with pytest.raises(MeterError):
        io.get_busiest_stream()


def test_total_queries_change_nothing(meter):
    meter.record_read("log", 3)
    before = state(meter)
    for _ in range(2):
        assert meter.get_total_bytes() == (3, 0)
        assert meter.get_total_ops() == 1
        assert meter.get_largest_op("log") == 3
        assert meter.get_busiest_stream() == "log"
    assert state(meter) == before
