Let streams in `meter.py` be paused, for example while a device is being
swapped out.

- Add `IOMeter.pause(stream_id)`, `IOMeter.resume(stream_id)` and
  `IOMeter.is_paused(stream_id) -> bool`. All three raise `KeyError` for a
  stream that is not open. New streams are not paused. Pausing a paused
  stream, or resuming one that is not paused, does nothing.
- Add `class StreamPaused(MeterError)` to `meter.py`.
- While a stream is paused, `record_read` and `record_write` on it raise
  `StreamPaused` and change nothing, whatever the size, including 0. The
  reading methods (`get_bytes_read`, `get_bytes_written`, `get_op_counts`
  and any others) keep working on a paused stream.
- `StreamPaused` is checked after every `KeyError` and `ValueError` check
  and before any other `MeterError`.
- Pausing and resuming change no byte total and no operation count.

All existing behavior must keep working.
