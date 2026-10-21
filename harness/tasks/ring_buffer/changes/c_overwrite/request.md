Add an overwrite mode to `ring_buffer.py`, for callers who would rather lose
the oldest value than fail when the buffer is full.

- Add `RingBuffer.enable_overwrite()`, `RingBuffer.disable_overwrite()` and
  `RingBuffer.is_overwrite_enabled() -> bool`. A new buffer has overwrite
  mode disabled. Enabling it when it is already enabled, or disabling it
  when it is already disabled, does nothing.
- While overwrite mode is enabled, `write` on a full buffer removes the
  oldest value and stores the new one as the newest, instead of raising
  `BufferFull`. The size stays at the capacity, and `read` then returns the
  remaining values oldest first, ending with the new one.
- While overwrite mode is disabled, `write` on a full buffer raises
  `BufferFull` as before.
- A value that is not an `int` still raises `ValueError`, before anything
  is removed, whether or not overwrite mode is enabled.
- Switching overwrite mode on or off never changes the stored values or the
  size.

All existing behavior must keep working.
