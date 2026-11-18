# Server racks

Write a module `racks.py` that keeps track of which servers are installed in
which rack of a data center. Every server has its own name, and each rack
keeps its servers in the order they arrived in it.

## Interface

```python
class RackError(Exception): ...


class Racks:
    def __init__(self): ...
    def add_rack(self, name: str) -> None: ...
    def install(self, rack: str, server: str) -> None: ...
    def remove(self, server: str) -> None: ...
    def move(self, server: str, to_rack: str) -> None: ...
    def migrate_all(self, from_rack: str, to_rack: str) -> int: ...
    def decommission_rack(self, name: str, into: str) -> int: ...
    def get_servers(self, rack: str) -> list[str]: ...
    def get_racks(self) -> list[str]: ...
```

Rack names and server names are non-empty strings.

## Racks

- `add_rack(name)` adds an empty rack. A name that is already in use
  raises `RackError`.
- `get_racks()` returns the names of the racks in use, in the order they
  were added.
- Every other method that takes a rack name raises `KeyError` when that
  rack is not in use: it was never added, or it was decommissioned.

## Servers

- `install(rack, server)` puts a new server at the end of the rack. A
  server name that is already installed, in any rack, raises `RackError`.
- `remove(server)` takes the server out of its rack for good; the servers
  after it move up one place.
- `move(server, to_rack)` takes the server out of its rack and puts it at
  the end of `to_rack`.
- `remove` and `move` raise `KeyError` for a server name that is not
  installed.
- `get_servers(rack)` returns the names of the servers in the rack, in the
  order they arrived in it. A server arrives in a rack when it is installed
  there, or moved there by `move`, `migrate_all` or `decommission_rack`.

## Moving every server

- `migrate_all(from_rack, to_rack)` moves every server in `from_rack` to
  the end of `to_rack` and returns how many servers it moved. The moved
  servers keep the order they had in `from_rack` (the first stays first),
  after the servers already in `to_rack`. Afterwards `from_rack` is empty
  but still in use. Migrating an empty rack is not an error: nothing
  changes and it returns 0.
- `decommission_rack(name, into)` moves every server in rack `name` to
  `into` exactly as `migrate_all(name, into)` does, and then also removes
  rack `name`, even when it was empty. A removed rack is no longer listed
  by `get_racks()`, and every method treats it as not in use (unlike after
  `migrate_all`, where the rack stays). It returns how many servers it
  moved. The other racks keep their order.
- Both raise `ValueError` when the two rack names are the same.

```python
dc = Racks()
dc.add_rack("A")
dc.add_rack("B")
dc.install("A", "web1")
dc.install("A", "web2")
dc.install("A", "db1")
dc.install("B", "cache1")
dc.migrate_all("A", "B")         # returns 3
dc.get_servers("B")              # ["cache1", "web1", "web2", "db1"]
dc.get_servers("A")              # []
dc.move("cache1", "A")
dc.get_servers("B")              # ["web1", "web2", "db1"]
dc.decommission_rack("A", "B")   # returns 1
dc.get_servers("B")              # ["web1", "web2", "db1", "cache1"]
dc.get_racks()                   # ["B"]
```

Python note: moving a server changes the list of the rack it leaves. If you
loop over that very list and call `move` (or anything else that takes
servers out of it) inside the loop, Python skips every other server. Loop
over a copy instead (`for server in list(servers):`), from the first server
to the last (looping backwards would reverse their order), and count how
many there are before you move anything.

## Errors

Which error is raised when a call has more than one problem (for example a
rack that is not in use and a server name that is already installed) is
unspecified.

A failed call has no effect: if a method raises, every rack and every
server is where it was, in the same order.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it.
This includes names that are not non-empty strings, which error is raised
when a call has more than one problem, moving a server to the rack it is
already in, installing a server under the name
of a removed server, adding a rack under the name of a decommissioned rack,
what happens if a returned list is changed, the text of error messages,
saving the racks to a file, and use from several threads.
