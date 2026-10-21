Let callers look at what `ring_buffer.py` holds without taking anything out.

- Add `RingBuffer.peek() -> int`, which returns the oldest value and leaves
  the buffer as it is. On an empty buffer it raises `BufferEmpty`.
- Add `RingBuffer.get_newest() -> int`, which returns the most recently
  written value that is still in the buffer, also without removing it. On
  an empty buffer it raises `BufferEmpty`.
- Add `RingBuffer.get_contents() -> list[int]`, which returns every stored
  value, oldest first, so that `get_contents()[0]` is what `read()` would
  return next. An empty buffer gives `[]`. Changing the returned list must
  not change the buffer.

The three methods work the same after reads, clears and wrap-arounds: they
describe the values a sequence of `read()` calls would return, in that
order. All existing behavior must keep working.
