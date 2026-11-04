# Ring buffer

Write a module `ring_buffer.py` with a bounded first-in, first-out buffer:
values go in at one end and come out at the other in the same order, and
the buffer never holds more than its capacity.

## Interface

```python
class RingError(Exception): ...


class BufferFull(RingError): ...


class BufferEmpty(RingError): ...


class RingBuffer:
    def __init__(self, capacity: int): ...
    def write(self, value: int) -> None: ...
    def read(self) -> int: ...
    def clear(self) -> None: ...
    def get_size(self) -> int: ...
    def get_capacity(self) -> int: ...
```

Values are plain `int`s. They may be 0 or negative, and the same value may
be written more than once.

## Capacity

- `RingBuffer(capacity)` creates a buffer with room for exactly `capacity`
  values. All of that room is free at first. The capacity must be at least
  1, or `ValueError` is raised.
- `get_capacity()` returns the capacity given at creation.
- `get_size()` returns how many values the buffer holds right now, from 0
  up to the capacity.

## Writing and reading

- `write(value)` stores a value as the newest. A value that is not an `int`
  raises `ValueError`. Writing when the buffer already holds `capacity`
  values raises `BufferFull`.
- `read()` removes and returns the oldest value. Reading from an empty
  buffer raises `BufferEmpty`.
- `clear()` removes every value. Clearing an empty buffer is allowed.
- Values come out in the order they went in, however writes and reads are
  mixed, and each read makes room for one more write. For example, with a
  capacity of 2: write 1, write 2, read gives 1, write 3, read gives 2,
  write 4, and the next two reads give 3 and then 4.

A failed call has no effect: if a method raises, the size and the stored
values are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes capacities that are not `int`s, such as `2.5`, `"3"` or `None`,
`bool` values and capacities, which error is raised when a value that is
not an `int` is written to a full buffer, the text of error messages,
`len()` and iteration over a buffer, saving the buffer to a file, and use
from several threads.
