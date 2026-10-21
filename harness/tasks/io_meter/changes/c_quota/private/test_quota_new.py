"""Hidden tests for the c_quota change (per-stream quotas). Never shown to the
writer or the editor.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_quota/private/test_quota_new.py
"""

import pytest
from meter import IOMeter, MeterError, QuotaExceeded

BAD_QUOTAS = [-1, 2.5, "100", True]


@pytest.fixture
def meter():
    io = IOMeter()
    io.open_stream("log", quota=100)
    io.open_stream("free")
    return io


def state(io):
    return {
        s: (io.get_bytes_read(s), io.get_bytes_written(s), io.get_op_counts(s))
        for s in io.get_streams()
    }


def test_the_quota_and_what_is_left_are_reported(meter):
    assert meter.get_quota("log") == 100
    assert meter.get_quota_left("log") == 100
    meter.record_read("log", 30)
    meter.record_write("log", 25)
    assert meter.get_quota("log") == 100
    assert meter.get_quota_left("log") == 45


def test_the_quota_can_be_reached_exactly(meter):
    meter.record_read("log", 100)
    assert meter.get_quota_left("log") == 0
    before = state(meter)
    with pytest.raises(QuotaExceeded):
        meter.record_write("log", 1)
    with pytest.raises(QuotaExceeded):
        meter.record_read("log", 1)
    assert state(meter) == before


def test_zero_byte_operations_are_allowed_at_the_quota(meter):
    meter.record_write("log", 100)
    meter.record_read("log", 0)
    meter.record_write("log", 0)
    assert meter.get_op_counts("log") == (1, 2)
    assert meter.get_quota_left("log") == 0


def test_a_quota_of_zero_allows_only_empty_operations():
    io = IOMeter()
    io.open_stream("empty", quota=0)
    io.record_read("empty", 0)
    with pytest.raises(QuotaExceeded):
        io.record_write("empty", 1)
    assert io.get_op_counts("empty") == (1, 0)


def test_streams_without_a_quota_report_none(meter):
    assert meter.get_quota("free") is None
    assert meter.get_quota_left("free") is None
    meter.record_write("free", 10**9)
    assert meter.get_quota_left("free") is None


@pytest.mark.parametrize("quota", BAD_QUOTAS)
def test_invalid_quotas_are_rejected_when_opening(meter, quota):
    before = state(meter)
    with pytest.raises(ValueError):
        meter.open_stream("other", quota=quota)
    assert meter.get_streams() == ["log", "free"]
    assert state(meter) == before


def test_a_bad_quota_is_reported_before_a_duplicate_id(meter):
    with pytest.raises(ValueError):
        meter.open_stream("log", quota=-1)


@pytest.mark.parametrize("method", ["get_quota", "get_quota_left"])
@pytest.mark.parametrize("stream_id", ["other", None, 1])
def test_quota_queries_on_unknown_streams_raise_key_error(meter, method, stream_id):
    with pytest.raises(KeyError):
        getattr(meter, method)(stream_id)


def test_set_quota_replaces_the_quota(meter):
    meter.record_read("log", 80)
    meter.set_quota("log", 90)
    assert meter.get_quota("log") == 90
    assert meter.get_quota_left("log") == 10
    with pytest.raises(QuotaExceeded):
        meter.record_read("log", 11)
    meter.record_read("log", 10)
    meter.set_quota("free", 5)
    with pytest.raises(QuotaExceeded):
        meter.record_write("free", 6)


def test_set_quota_to_none_removes_the_cap(meter):
    meter.record_read("log", 100)
    meter.set_quota("log", None)
    assert meter.get_quota("log") is None
    meter.record_read("log", 1000)
    assert meter.get_bytes_read("log") == 1100


def test_a_quota_below_the_bytes_already_moved_is_rejected(meter):
    meter.record_write("log", 60)
    before = state(meter)
    with pytest.raises(MeterError):
        meter.set_quota("log", 59)
    assert meter.get_quota("log") == 100
    assert state(meter) == before
    meter.set_quota("log", 60)  # exactly what was moved is fine
    assert meter.get_quota_left("log") == 0


@pytest.mark.parametrize("quota", BAD_QUOTAS)
def test_invalid_quotas_are_rejected_when_setting(meter, quota):
    with pytest.raises(ValueError):
        meter.set_quota("log", quota)
    assert meter.get_quota("log") == 100


def test_set_quota_error_order(meter):
    meter.record_write("log", 60)
    with pytest.raises(KeyError):
        meter.set_quota("other", -1)
    with pytest.raises(ValueError):
        meter.set_quota("log", -1)


def test_a_bad_size_is_reported_before_the_quota(meter):
    meter.record_read("log", 100)
    with pytest.raises(ValueError):
        meter.record_read("log", -1)
    with pytest.raises(KeyError):
        meter.record_read("other", 10**6)
    assert meter.get_op_counts("log") == (1, 0)


def test_quota_exceeded_is_a_meter_error():
    assert issubclass(QuotaExceeded, MeterError)
