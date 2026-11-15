# Sample freezers

Write a module `freezers.py` that keeps track of which lab freezer holds
each sample. Every sample has its own id, and each freezer keeps its
samples in the order they arrived in it.

## Interface

```python
class FreezerError(Exception): ...


class Freezers:
    def __init__(self): ...
    def add_freezer(self, freezer_id: str) -> None: ...
    def store(self, freezer_id: str, sample_id: str) -> None: ...
    def discard(self, sample_id: str) -> None: ...
    def move(self, sample_id: str, to_freezer: str) -> None: ...
    def move_all(self, from_freezer: str, to_freezer: str) -> int: ...
    def remove_freezer(self, freezer_id: str, to_freezer: str) -> int: ...
    def find(self, sample_id: str) -> str: ...
    def get_samples(self, freezer_id: str) -> list[str]: ...
    def get_freezers(self) -> list[str]: ...
```

## Freezers

- `add_freezer(freezer_id)` adds an empty freezer. An id that is in use
  raises `FreezerError`. The id of a removed freezer may be added again: it
  becomes a new, empty freezer.
- `get_freezers()` returns the ids of the freezers in use, in the order they
  were added.
- Every other method that takes a freezer id raises `KeyError` when that
  freezer is not in use: it was never added, or it was removed.

## Samples

- `store(freezer_id, sample_id)` puts a new sample in the freezer. A
  freezer that is not in use raises `KeyError`, and a sample id that is
  stored already, in any freezer, raises `FreezerError`. The id of a
  discarded sample may be stored again.
- `discard(sample_id)` takes the sample out of its freezer for good.
- `move(sample_id, to_freezer)` moves the sample from its freezer to
  `to_freezer`. Moving it to the freezer it is already in raises
  `ValueError`.
- `find(sample_id)` returns the id of the freezer that holds the sample.
- `discard`, `move` and `find` raise `KeyError` for a sample id that is not
  stored: it was never stored, or it was discarded.

## Moving every sample

- `move_all(from_freezer, to_freezer)` moves every sample in `from_freezer`
  to `to_freezer` and returns the number of samples moved. When
  `from_freezer` is empty it returns 0 and nothing changes; `from_freezer`
  stays in use either way.
- `remove_freezer(freezer_id, to_freezer)` moves every sample in the freezer
  to `to_freezer` the same way, then removes the freezer, even when it was
  empty: `get_freezers` no longer lists it. It returns the number of
  samples moved.
- Both raise `ValueError` when the two freezer ids are the same.

## Order of samples

`get_samples(freezer_id)` returns the ids of the samples in the freezer, in
the order they arrived in it. A sample arrives in a freezer when it is
stored there or moved there by `move`, `move_all` or `remove_freezer`.

`move_all` and `remove_freezer` keep the moved samples in the same order
they had in the freezer they came from (the first stays first; the order
is not reversed), and put them after the samples already in `to_freezer`:

```python
lab = Freezers()
lab.add_freezer("A")
lab.add_freezer("B")
lab.store("A", "s1")
lab.store("A", "s2")
lab.store("A", "s3")
lab.store("B", "s4")
lab.move_all("A", "B")    # returns 3
lab.get_samples("B")      # ["s4", "s1", "s2", "s3"]: s1, s2, s3 as they were in A
lab.get_samples("A")      # []
lab.move("s4", "A")
lab.get_samples("B")      # ["s1", "s2", "s3"]
lab.remove_freezer("A", "B")  # returns 1
lab.get_samples("B")      # ["s1", "s2", "s3", "s4"]
lab.get_freezers()        # ["B"]
```

## Errors

Which error is raised when a call has more than one problem (such as a
`KeyError` and a `ValueError` problem, or a `store` into a freezer that is
not in use with a sample id that is stored already) is unspecified.

A failed call has no effect: if a method raises, every freezer and every
sample is where it was, in the same order.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings or are empty, which error is raised when
a call has more than one problem, what happens if a returned
list is changed, the text of error messages, saving to a file, and use from
several threads.
