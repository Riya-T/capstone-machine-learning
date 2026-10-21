"""Public checks for the c_quota change (per-stream quotas). Shown to the
editor, never to the writer.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_quota/public/test_quota_public.py
"""

import pytest
from meter import IOMeter, QuotaExceeded


def test_reads_and_writes_share_the_quota():
    io = IOMeter()
    io.open_stream("log", quota=100)
    io.record_read("log", 60)
    io.record_write("log", 40)
    assert io.get_quota("log") == 100
    assert io.get_quota_left("log") == 0
    with pytest.raises(QuotaExceeded):
        io.record_read("log", 1)
    assert io.get_op_counts("log") == (1, 1)


def test_going_over_the_quota_changes_nothing():
    io = IOMeter()
    io.open_stream("log", quota=50)
    io.record_write("log", 30)
    with pytest.raises(QuotaExceeded):
        io.record_write("log", 21)
    assert io.get_bytes_written("log") == 30
    assert io.get_quota_left("log") == 20


def test_without_a_quota_nothing_is_capped():
    io = IOMeter()
    io.open_stream("log")
    assert io.get_quota("log") is None
    assert io.get_quota_left("log") is None
    io.record_read("log", 10**9)
    assert io.get_bytes_read("log") == 10**9
