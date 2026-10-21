# I/O meter

Write a module `meter.py` that keeps track of the data moving through a set
of named streams: how many bytes were read and written on each stream, and
how many read and write operations took place.

## Interface

```python
class MeterError(Exception): ...


class IOMeter:
    def __init__(self): ...
    def open_stream(self, stream_id: str) -> None: ...
    def record_read(self, stream_id: str, size: int) -> None: ...
    def record_write(self, stream_id: str, size: int) -> None: ...
    def get_bytes_read(self, stream_id: str) -> int: ...
    def get_bytes_written(self, stream_id: str) -> int: ...
    def get_op_counts(self, stream_id: str) -> tuple[int, int]: ...
    def get_streams(self) -> list[str]: ...
```

All sizes are whole bytes, as `int`.

## Streams

- `open_stream(stream_id)` opens a stream with nothing read or written yet.
  An empty id raises `ValueError`, and opening an id that is already open
  raises `MeterError`.
- `get_streams()` returns the ids of all open streams, in the order they
  were opened.
- Every other method raises `KeyError` when given a stream id that is not
  open, including values that are not strings at all, such as `None` or `1`.

## Recording operations

- `record_read(stream_id, size)` records one read operation that moved
  `size` bytes. `record_write(stream_id, size)` records one write operation
  the same way.
- A size must be an `int` of 0 or more, or `ValueError` is raised. A size of
  0 is a real operation (a read at the end of a file, for example): it moves
  no bytes but still counts as an operation.
- When a call has several problems, `KeyError` for a stream that is not open
  is raised before `ValueError` for a bad size.

## Reading the meter

- `get_bytes_read(stream_id)` returns the total bytes read on the stream so
  far, and `get_bytes_written(stream_id)` the total bytes written. Both are
  0 for a stream that was just opened.
- `get_op_counts(stream_id)` returns a `(reads, writes)` tuple: how many
  read operations and how many write operations were recorded on the
  stream. It is `(0, 0)` for a stream that was just opened.

A failed call has no effect: if a method raises, every stream is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `open_stream`, `bool` sizes,
what happens if a returned list is changed, the text of error messages,
saving the meter to a file, and use from several threads.
