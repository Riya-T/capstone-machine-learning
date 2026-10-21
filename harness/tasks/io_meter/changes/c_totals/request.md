Add figures across streams and per-stream extremes to `meter.py`.

- Add `IOMeter.get_total_bytes() -> tuple[int, int]`: `(read, written)`,
  the bytes read and the bytes written added up over every open stream.
  `(0, 0)` when there are no streams.
- Add `IOMeter.get_total_ops() -> int`: the number of operations, reads and
  writes together, recorded over every open stream. 0 when there are none.
- Add `IOMeter.get_largest_op(stream_id) -> int`: the size of the largest
  single operation recorded on the stream, read or write. 0 for a stream
  with no operations yet. Raises `KeyError` for a stream that is not open.
- Add `IOMeter.get_busiest_stream() -> str`: the id of the stream with the
  most operations (reads and writes together). When several streams tie,
  it is the one that was opened first. Raises `MeterError` when no stream
  is open.
- None of these change anything; asking twice gives the same answer.

All existing behavior must keep working.
