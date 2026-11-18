# Rehearsal setlists

Write a module `setlists.py` that keeps a band's setlists: named lists of
song titles, each in the order the songs will be played.

## Interface

```python
class SetlistError(Exception): ...


class Setlists:
    def __init__(self): ...
    def create_setlist(self, name: str) -> None: ...
    def add_song(self, setlist: str, title: str) -> None: ...
    def remove_song(self, setlist: str, title: str) -> None: ...
    def move_song(self, title: str, from_setlist: str, to_setlist: str) -> None: ...
    def merge_setlists(self, source: str, into: str) -> int: ...
    def drop_song_everywhere(self, title: str) -> int: ...
    def get_songs(self, setlist: str) -> list[str]: ...
    def get_setlists(self) -> list[str]: ...
```

Setlist names and song titles are non-empty strings. Titles are compared
exactly: `"Hey Jude"` and `"hey jude"` are different songs.

## Setlists

- `create_setlist(name)` adds an empty setlist. A name that is already in
  use raises `SetlistError`.
- `get_setlists()` returns the names of the setlists in use, in the order
  they were created.
- Every other method that takes a setlist name raises `KeyError` when that
  setlist is not in use: it was never created, or it was merged into
  another one.

## Songs

- `get_songs(setlist)` returns the titles in the setlist, in order.
- `add_song(setlist, title)` puts the title at the end of the setlist. A
  setlist holds each title at most once: adding a title that is already in
  the setlist raises `SetlistError`. The same title may be in several
  setlists.
- `remove_song(setlist, title)` takes the title out of the setlist; the
  songs after it move up one place. A title that is not in the setlist
  raises `KeyError`.
- `move_song(title, from_setlist, to_setlist)` takes the title out of
  `from_setlist` and puts it at the end of `to_setlist`. It raises
  `KeyError` when the title is not in `from_setlist` and `SetlistError` when
  it is already in `to_setlist`. What happens when both setlists are the
  same is unspecified.

## Merging and dropping

- `merge_setlists(source, into)` appends the songs of `source` to the end
  of `into`, in their order in `source`, skipping the titles that are
  already in `into`. Then it removes `source`: it is no longer listed by
  `get_setlists()`, and every method treats it as not in use. It returns
  how many songs it appended (skipped titles do not count). Merging an
  empty setlist is allowed and returns 0. It raises `ValueError` when both
  names are the same. The other setlists keep their order.
- `drop_song_everywhere(title)` removes the title from every setlist that
  holds it and returns how many setlists it was removed from. A title that
  no setlist holds is not an error: nothing changes and it returns 0.

```python
s = Setlists()
s.create_setlist("friday")
s.create_setlist("encore")
for title in ["Intro", "Blue", "Run"]:
    s.add_song("friday", title)
s.add_song("encore", "Run")
s.add_song("encore", "Home")
s.merge_setlists("encore", "friday")  # returns 1: "Run" is skipped
s.get_songs("friday")                 # ["Intro", "Blue", "Run", "Home"]
s.get_setlists()                      # ["friday"]
s.drop_song_everywhere("Blue")        # returns 1
s.get_songs("friday")                 # ["Intro", "Run", "Home"]
```

## Errors

Which error is raised when a call has more than one problem (for example a
setlist that is not in use and a title that is already there) is
unspecified.

A failed call has no effect: if a method raises, every setlist, its songs
and their order, and the list of setlists are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes names and titles that are not non-empty strings, which error
is raised when a call has more than one problem, creating a setlist under
the name of one that was merged away, what happens if a returned list is
changed, the text of error messages, saving the setlists to a file, and use
from several threads.
