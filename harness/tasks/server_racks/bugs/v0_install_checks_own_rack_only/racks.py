"""Server racks: named servers in ordered racks.

Planted bug: install only rejects a name already installed in the same rack.
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

    def add_rack(self, name):
        check_name(name, "rack")
        if name in self._racks:
            raise RackError(f"rack name {name!r} is already used")
        self._racks[name] = []

    def install(self, rack, server):
        self._require(rack)
        check_name(server, "server")
        if server in self._racks[rack]:
            raise RackError(f"server {server!r} is already installed")
        self._racks[rack].append(server)

    def remove(self, server):
        rack = self._require_server(server)
        self._racks[rack].remove(server)

    def move(self, server, to_rack):
        self._require(to_rack)
        rack = self._require_server(server)
        if rack == to_rack:
            raise ValueError(f"server {server!r} is already in rack {to_rack!r}")
        self._racks[rack].remove(server)
        self._racks[to_rack].append(server)

    def migrate_all(self, from_rack, to_rack):
        self._require(from_rack)
        self._require(to_rack)
        check_different(from_rack, to_rack)
        return self._move_everything(from_rack, to_rack)

    def decommission_rack(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        moved = self._move_everything(name, into)
        del self._racks[name]
        return moved

    def get_servers(self, rack):
        self._require(rack)
        return list(self._racks[rack])

    def get_racks(self):
        return list(self._racks)

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
