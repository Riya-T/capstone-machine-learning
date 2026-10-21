"""Public checks for meter.py.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest public/test_meter_public.py
"""

import pytest
from meter import IOMeter


@pytest.fixture
def meter():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    return io


def test_reads_add_up(meter):
    meter.record_read("log", 100)
    meter.record_read("log", 50)
    assert meter.get_bytes_read("log") == 150
    assert meter.get_bytes_written("log") == 0
    assert meter.get_op_counts("log") == (2, 0)


def test_writes_are_counted_separately_from_reads(meter):
    meter.record_read("data", 10)
    meter.record_write("data", 300)
    meter.record_write("data", 20)
    assert meter.get_bytes_read("data") == 10
    assert meter.get_bytes_written("data") == 320
    assert meter.get_op_counts("data") == (1, 2)


def test_a_zero_byte_operation_still_counts(meter):
    meter.record_read("log", 0)
    assert meter.get_bytes_read("log") == 0
    assert meter.get_op_counts("log") == (1, 0)


def test_streams_are_listed_in_opening_order(meter):
    assert meter.get_streams() == ["log", "data"]
    assert meter.get_op_counts("data") == (0, 0)


def test_negative_sizes_are_rejected(meter):
    with pytest.raises(ValueError):
        meter.record_write("log", -1)
    assert meter.get_op_counts("log") == (0, 0)


def test_unknown_stream_raises_key_error(meter):
    with pytest.raises(KeyError):
        meter.record_read("other", 5)
