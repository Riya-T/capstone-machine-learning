# Tram lines

Write a module `trams.py` that keeps track of a city's tram lines. Each line
is a list of stops in the order the tram visits them. Lines are planned stop
by stop; a stop can be taken off one line or closed on every line at once;
and two lines can be merged into one.

## Interface

```python
class TramError(Exception): ...


class TramNetwork:
    def __init__(self): ...
    def add_line(self, name: str) -> None: ...
    def add_stop(self, line: str, stop: str) -> None: ...
    def remove_stop(self, line: str, stop: str) -> None: ...
    def close_stop(self, stop: str) -> int: ...
    def merge_lines(self, first: str, second: str) -> None: ...
    def get_stops(self, line: str) -> list[str]: ...
    def get_lines(self) -> list[str]: ...
    def get_lines_through(self, stop: str) -> list[str]: ...
```

Line names and stop names are non-empty strings.

## Lines

- `add_line(name)` adds a line with no stops. A name that is already in use
  raises `TramError`.
- `get_lines()` returns the names of the lines in use, in the order they
  were added.
- Every other method that takes a line name raises `KeyError` when given a
  line name that is not in use: one that was never added, or one that was
  merged into another line.

## Stops

- `add_stop(line, stop)` adds `stop` at the end of the line. A line has each
  stop at most once: adding a stop the line already has raises `TramError`.
  The same stop may be on any number of lines.
- `remove_stop(line, stop)` takes `stop` off the line; the other stops keep
  their order. Removing a stop the line does not have raises `TramError`.
- `close_stop(stop)` takes `stop` off every line that has it and returns how
  many lines that was. The other stops keep their order, and a line left
  with no stops stays in use. Closing a stop that no line has raises
  `TramError`.
- `get_stops(line)` returns the stops of the line, in order.
- `get_lines_through(stop)` returns the names of the lines that have `stop`,
  in the order of `get_lines()`, or `[]` if no line has it.

## Merging lines

- `merge_lines(first, second)` adds the stops of line `second` to the end of
  line `first`, in `second`'s order, skipping the stops that `first` already
  has. Then it removes line `second`: it is no longer in `get_lines()`, and
  every method treats it as not in use.
- `merge_lines` raises `ValueError` when both lines are the same.

## Errors

A failed call has no effect: if a method raises, every line's stops and the
list of lines are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type, such as line or stop names that are not
non-empty strings (`""`, `None` or `1`), wherever they are passed. It also
includes which error is raised when a call has more than one problem (such
as `merge_lines` given the same name twice for a line that is not in use),
whether `add_line` may later add a line under the name of a line that was
merged away, what happens if a returned list is changed, the text of error
messages, saving the network to a file, and use from several threads.
