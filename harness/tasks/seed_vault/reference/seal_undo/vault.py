"""Seed vault with undo and sealed drawers.

Correct solution for seed_vault after c_undo and c_seal.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vault import SeedVault
    vault = SeedVault()
    vault.add_drawer("A")
    vault.seal("A")
    vault.undo()  # A is open again
"""


class VaultError(Exception):
    pass


class NotEnoughSeeds(VaultError):
    pass


class DrawerSealed(VaultError):
    pass


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_drawer, to_drawer):
    if from_drawer == to_drawer:
        raise ValueError("cannot move packets into the drawer they are in")


class SeedVault:
    def __init__(self):
        # drawer name -> {variety: count}; both dicts keep the order things
        # were added, and only counts above 0 are stored.
        self._drawers = {}
        self._sealed = set()
        self._undo_stack = []  # (drawers, sealed) as they were before each call

    def add_drawer(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("drawer name must be a non-empty str")
        if name in self._drawers:
            raise VaultError(f"drawer name {name!r} is already used")
        self._save()
        self._drawers[name] = {}
        self._sealed.discard(name)

    def deposit(self, drawer, variety, count):
        self._require(drawer)
        check_count(count)
        self._require_open(drawer)
        self._save()
        self._change(drawer, variety, count)

    def transfer(self, variety, from_drawer, to_drawer, count):
        self._require(from_drawer)
        self._require(to_drawer)
        check_count(count)
        check_different(from_drawer, to_drawer)
        self._require_open(from_drawer, to_drawer)
        if self._drawers[from_drawer].get(variety, 0) < count:
            raise NotEnoughSeeds(f"drawer {from_drawer!r} has fewer than {count} {variety}")
        self._save()
        self._change(from_drawer, variety, -count)
        self._change(to_drawer, variety, count)

    def transfer_all(self, from_drawer, to_drawer):
        self._require(from_drawer)
        self._require(to_drawer)
        check_different(from_drawer, to_drawer)
        self._require_open(from_drawer, to_drawer)
        self._save()
        return self._move_everything(from_drawer, to_drawer)

    def retire_drawer(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_open(name, into)
        self._save()
        moved = self._move_everything(name, into)
        del self._drawers[name]
        return moved

    def seal(self, drawer):
        self._require(drawer)
        self._save()
        self._sealed.add(drawer)

    def unseal(self, drawer):
        self._require(drawer)
        self._save()
        self._sealed.discard(drawer)

    def undo(self):
        if not self._undo_stack:
            raise VaultError("nothing to undo")
        self._drawers, self._sealed = self._undo_stack.pop()

    def get_sealed(self):
        return [name for name in self._drawers if name in self._sealed]

    def get_count(self, drawer, variety):
        self._require(drawer)
        return self._drawers[drawer].get(variety, 0)

    def get_drawers(self):
        return list(self._drawers)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        drawers = {name: dict(packets) for name, packets in self._drawers.items()}
        self._undo_stack.append((drawers, set(self._sealed)))

    def _require(self, drawer):
        if not isinstance(drawer, str) or drawer not in self._drawers:
            raise KeyError(drawer)

    def _require_open(self, *drawers):
        for drawer in drawers:
            if drawer in self._sealed:
                raise DrawerSealed(f"drawer {drawer!r} is sealed")

    def _move_everything(self, from_drawer, to_drawer):
        packets = self._drawers[from_drawer]
        moved = sum(packets.values())
        for variety, count in packets.items():
            self._change(to_drawer, variety, count)
        packets.clear()
        return moved

    def _change(self, drawer, variety, delta):
        packets = self._drawers[drawer]
        new_count = packets.get(variety, 0) + delta
        if new_count:
            packets[variety] = new_count
        else:
            del packets[variety]
