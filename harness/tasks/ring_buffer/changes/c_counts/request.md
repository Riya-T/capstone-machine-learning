Keep running totals in `ring_buffer.py` of what has passed through a buffer
over its whole lifetime.

- Add `RingBuffer.get_total_written() -> int`: the number of values ever
  stored by a successful `write`, including writes that overwrote an older
  value.
- Add `RingBuffer.get_total_read() -> int`: the number of values ever
  returned by a successful `read`.
- Add `RingBuffer.get_total_discarded() -> int`: the number of values that
  left the buffer without being read, either because `clear` removed them
  or because a write in overwrite mode replaced them.
- A new buffer reports 0 for all three. A call that raises changes none of
  them, and `clear` resets none of them (it only adds to the discarded
  total). At every moment `get_size()` equals the written total minus the
  read total minus the discarded total.

All existing behavior must keep working.
