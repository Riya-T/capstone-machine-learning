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

- `RingBuffer(capacity)` creates an empty buffer. The capacity must be an
  `int` of at least 1, or `ValueError` is raised.
- `get_capacity()` returns the capacity given at creation.
- `get_size()` returns how many values the buffer holds right now, from 0
  up to the capacity.

## Writing and reading

- `write(value)` stores a value as the newest. A value that is not an `int`
  raises `ValueError`. Writing when the buffer already holds `capacity`
  values raises `BufferFull`. When both problems apply, `ValueError` is
  raised.
- `read()` removes and returns the oldest value. Reading from an empty
  buffer raises `BufferEmpty`.
- `clear()` removes every value. Clearing an empty buffer is allowed.
- Values come out in the order they went in. After some values are read,
  the space they used can be written again, and `read` still returns the
  remaining values oldest first, followed by the new ones.

A failed call has no effect: if a method raises, the size and the stored
values are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values and capacities, the text of error messages, `len()`
and iteration over a buffer, saving the buffer to a file, and use from
several threads.
