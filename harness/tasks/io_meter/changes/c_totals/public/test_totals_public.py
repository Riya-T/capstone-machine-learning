"""Public checks for the c_totals change (totals across streams and the
largest operation). Shown to the editor, never to the writer.

Usage (with meter.py importable, e.g. in the sandbox):
    python -m pytest changes/c_totals/public/test_totals_public.py
"""

from meter import IOMeter


def test_totals_add_up_over_every_stream():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    io.record_read("log", 100)
    io.record_write("log", 10)
    io.record_read("data", 5)
    assert io.get_total_bytes() == (105, 10)
    assert io.get_total_ops() == 3


def test_the_largest_operation_is_tracked_per_stream():
    io = IOMeter()
    io.open_stream("log")
    assert io.get_largest_op("log") == 0
    io.record_read("log", 40)
    io.record_write("log", 90)
    io.record_read("log", 60)
    assert io.get_largest_op("log") == 90


def test_the_busiest_stream_has_the_most_operations():
    io = IOMeter()
    io.open_stream("log")
    io.open_stream("data")
    io.record_write("log", 1000)
    io.record_read("data", 1)
    io.record_read("data", 1)
    assert io.get_busiest_stream() == "data"
