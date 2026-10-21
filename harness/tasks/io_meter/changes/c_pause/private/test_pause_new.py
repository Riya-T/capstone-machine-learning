"""Hidden tests for the c_pause change (paused streams). Never shown to the
writer or the editor.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_pause/private/test_pause_new.py
"""

import pytest
from meter import IOMeter, MeterError, QuotaExceeded, StreamPaused


@pytest.fixture
def meter():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    io.record_read("log", 10)
    io.record_write("log", 20)
    return io


def state(io):
    return {
        s: (io.get_bytes_read(s), io.get_bytes_written(s), io.get_op_counts(s))
        for s in io.get_streams()
    }


def test_streams_start_unpaused(meter):
    assert not meter.is_paused("log")
    assert not meter.is_paused("data")


def test_pausing_or_resuming_twice_is_harmless(meter):
    meter.pause("log")
    meter.pause("log")
    assert meter.is_paused("log")
    meter.resume("log")
    meter.resume("log")
    assert not meter.is_paused("log")
    assert not meter.is_paused("data")


@pytest.mark.parametrize("method", ["pause", "resume", "is_paused"])
@pytest.mark.parametrize("stream_id", ["other", None, 1])
def test_pause_methods_on_unknown_streams_raise_key_error(meter, method, stream_id):
    with pytest.raises(KeyError):
        getattr(meter, method)(stream_id)


@pytest.mark.parametrize("size", [0, 1, 10**6])
def test_recording_on_a_paused_stream_changes_nothing(meter, size):
    meter.pause("log")
    before = state(meter)
    with pytest.raises(StreamPaused):
        meter.record_read("log", size)
    with pytest.raises(StreamPaused):
        meter.record_write("log", size)
    assert state(meter) == before


def test_pausing_only_affects_the_named_stream(meter):
    meter.pause("log")
    meter.record_read("data", 5)
    assert meter.get_bytes_read("data") == 5
    assert not meter.is_paused("data")


def test_reading_methods_work_while_paused(meter):
    meter.pause("log")
    assert meter.get_bytes_read("log") == 10
    assert meter.get_bytes_written("log") == 20
    assert meter.get_op_counts("log") == (1, 1)
    assert meter.get_quota("log") is None


def test_pausing_and_resuming_change_no_counts(meter):
    before = state(meter)
    meter.pause("log")
    meter.resume("log")
    assert state(meter) == before


def test_bad_input_is_reported_before_paused(meter):
    meter.pause("log")
    with pytest.raises(ValueError):
        meter.record_read("log", -1)
    with pytest.raises(ValueError):
        meter.record_write("log", "10")
    with pytest.raises(KeyError):
        meter.record_read("other", 1)


def test_paused_is_reported_before_the_quota():
    io = IOMeter()
    io.open_stream("capped", quota=10)
    io.record_read("capped", 10)
    io.pause("capped")
    with pytest.raises(StreamPaused):
        io.record_read("capped", 1)
    io.resume("capped")
    with pytest.raises(QuotaExceeded):
        io.record_read("capped", 1)


def test_stream_paused_is_a_meter_error_but_not_quota_exceeded():
    assert issubclass(StreamPaused, MeterError)
    assert not issubclass(StreamPaused, QuotaExceeded)
