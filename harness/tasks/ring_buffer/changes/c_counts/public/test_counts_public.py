"""Public checks for the c_counts change (lifetime totals). Shown to the
editor, never to the writer.

Usage (with ring_buffer.py importable, e.g. in the sandbox):
    python -m pytest changes/c_counts/public/test_counts_public.py
"""

from ring_buffer import RingBuffer


def totals(buf):
    return (buf.get_total_written(), buf.get_total_read(), buf.get_total_discarded())


def test_writes_and_reads_are_counted():
    buf = RingBuffer(3)
    assert totals(buf) == (0, 0, 0)
    buf.write(1)
    buf.write(2)
    buf.read()
    assert totals(buf) == (2, 1, 0)


def test_clear_counts_the_removed_values_as_discarded():
    buf = RingBuffer(3)
    buf.write(1)
    buf.write(2)
    buf.clear()
    assert totals(buf) == (2, 0, 2)
    assert buf.get_size() == 0
