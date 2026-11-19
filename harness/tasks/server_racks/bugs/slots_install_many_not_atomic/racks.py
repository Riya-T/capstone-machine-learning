"""Server racks: named servers in ordered racks.

Planted bug: slots work, but install_many checks each name while installing, so the
servers before a bad name stay installed.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from racks import Racks
    racks = Racks()
    racks.add_rack("r1")
    racks.install("r1", "web-1")
    racks.install("r1", "db-1")
    racks.get_servers("r1")  # ["web-1", "db-1"]
"""


class RackError(Exception):
    pass


class RackFull(RackError):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} name must be a non-empty str")


def check_different(from_rack, to_rack):
    if from_rack == to_rack:
        raise ValueError("the two racks must be different")


class Racks:
    def __init__(self):
        # rack name -> list of server names in the order they arrived, in
        # the order the racks were added
        self._racks = {}
        self._slots = {}  # rack name -> int or None
        self._undo_stack = []  # copies of the state as it was before each recorded call

    def add_rack(self, name, slots=None):
        check_name(name, "rack")
        if name in self._racks:
            raise RackError(f"rack name {name!r} is already used")
        if slots is not None and (isinstance(slots, bool) or not isinstance(slots, int) or slots <= 0):
            raise ValueError("slots must be None or a positive int")
        self._record()
        self._racks[name] = []
        self._slots[name] = slots

    def install(self, rack, server):
        self._require(rack)
        check_name(server, "server")
        if self._rack_of(server) is not None:
            raise RackError(f"server {server!r} is already installed")
        self._require_room(rack, 1)
        self._record()
        self._racks[rack].append(server)

    def remove(self, server):
        rack = self._require_server(server)
        self._record()
        self._racks[rack].remove(server)

    def move(self, server, to_rack):
        self._require(to_rack)
        rack = self._require_server(server)
        if rack == to_rack:
            raise ValueError(f"server {server!r} is already in rack {to_rack!r}")
        self._require_room(to_rack, 1)
        self._record()
        self._racks[rack].remove(server)
        self._racks[to_rack].append(server)

    def migrate_all(self, from_rack, to_rack):
        self._require(from_rack)
        self._require(to_rack)
        check_different(from_rack, to_rack)
        self._require_room(to_rack, len(self._racks[from_rack]))
        self._record()
        return self._move_everything(from_rack, to_rack)

    def decommission_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(into, len(self._racks[name]))
        self._record()
        moved = self._move_everything(name, into)
        del self._racks[name]
        del self._slots[name]
        return moved

    def install_many(self, rack, servers):
        self._require(rack)
        for server in servers:
            check_name(server, "server")
        self._require_room(rack, len(servers))
        self._record()
        for server in servers:
            if self._rack_of(server) is not None:
                raise RackError(f"server {server!r} is already installed")
            self._racks[rack].append(server)
        return len(servers)

    def undo(self):
        if not self._undo_stack:
            raise RackError("nothing to undo")
        self._racks, self._slots = self._undo_stack.pop()

    def get_slots(self, rack):
        self._require(rack)
        return self._slots[rack]

    def get_servers(self, rack):
        self._require(rack)
        return list(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

    def _record(self):
        # Called by each call that changes the racks, once all its checks
        # have passed.
        racks = {name: list(servers) for name, servers in self._racks.items()}
        self._undo_stack.append((racks, dict(self._slots)))

    def _move_everything(self, from_rack, to_rack):
        servers = self._racks[from_rack]
        self._racks[to_rack].extend(servers)
        self._racks[from_rack] = []
        return len(servers)

    def _rack_of(self, server):
        for name, servers in self._racks.items():
            if server in servers:
                return name
        return None

    def _require(self, rack):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(rack, str) or rack not in self._racks:
            raise KeyError(rack)

    def _require_server(self, server):
        rack = self._rack_of(server)
        if rack is None:
            raise KeyError(server)
        return rack

    def _require_room(self, rack, count):
        slots = self._slots[rack]
        if slots is not None and len(self._racks[rack]) + count > slots:
            raise RackFull(f"rack {rack!r} has no room for {count} more servers")
