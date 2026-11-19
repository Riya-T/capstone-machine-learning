"""Coin vaults: coins counted per denomination per vault.

Planted bug: the capacity works, but transfer works on the live vaults, so the moves
before a failing one stay made.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vaults import Vaults
    vaults = Vaults()
    vaults.add_vault("main")
    vaults.deposit("main", 20, 4)
    vaults.withdraw("main", 20, 1)
    vaults.get_count("main", 20)  # 3
"""


class VaultError(Exception):
    pass


class NotEnoughCoins(VaultError):
    pass


class VaultFull(VaultError):
    pass


STANDARD_DENOMINATIONS = [1, 2, 5, 10, 20, 50, 100, 200]


def check_name(name):
    if not isinstance(name, str) or not name:
        raise ValueError("vault name must be a non-empty str")


def check_count(count):
    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError(f"count must be a positive int, got {count!r}")


def check_different(from_vault, to_vault):
    if from_vault == to_vault:
        raise ValueError("the two vaults must be different")


def change(coins, denomination, delta):
    """Add delta coins to one vault's {denomination: count}; only counts
    above 0 are stored."""
    new_count = coins.get(denomination, 0) + delta
    if new_count:
        coins[denomination] = new_count
    else:
        del coins[denomination]


class Vaults:
    def __init__(self):
        self._accepted = list(STANDARD_DENOMINATIONS)
        # vault name -> {denomination: count}, in the order the vaults were added
        self._vaults = {}
        self._capacity = {}  # vault name -> int or None
        self._undo_stack = []  # copies of the state as it was before each recorded call

    def add_vault(self, name, capacity=None):
        check_name(name)
        if name in self._vaults:
            raise VaultError(f"vault name {name!r} is already used")
        if capacity is not None and (
            isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0
        ):
            raise ValueError("capacity must be None or a positive int")
        self._save()
        self._vaults[name] = {}
        self._capacity[name] = capacity

    def deposit(self, vault, denomination, count):
        self._require(vault)
        if denomination not in self._accepted:
            raise ValueError(f"denomination {denomination!r} is not accepted")
        check_count(count)
        self._require_room(self._vaults, vault, count)
        self._save()
        change(self._vaults[vault], denomination, count)

    def withdraw(self, vault, denomination, count):
        self._require(vault)
        check_count(count)
        self._require_coins(self._vaults, vault, denomination, count)
        self._save()
        change(self._vaults[vault], denomination, -count)

    def consolidate(self, from_vault, to_vault):
        self._require(from_vault)
        self._require(to_vault)
        check_different(from_vault, to_vault)
        self._require_room(self._vaults, to_vault, sum(self._vaults[from_vault].values()))
        self._save()
        return self._move_everything(from_vault, to_vault)

    def close_vault(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._require_room(self._vaults, into, sum(self._vaults[name].values()))
        self._save()
        moved = self._move_everything(name, into)
        del self._vaults[name]
        del self._capacity[name]
        return moved

    def transfer(self, moves):
        # Every move is made on a copy first, so a failing move leaves the
        # vaults untouched.
        work = self._vaults
        total = 0
        for from_vault, to_vault, denomination, count in moves:
            self._require(from_vault)
            self._require(to_vault)
            check_count(count)
            check_different(from_vault, to_vault)
            self._require_coins(work, from_vault, denomination, count)
            self._require_room(work, to_vault, count)
            change(work[from_vault], denomination, -count)
            change(work[to_vault], denomination, count)
            total += count
        self._save()
        self._vaults = work
        return total

    def undo(self):
        if not self._undo_stack:
            raise VaultError("nothing to undo")
        self._vaults, self._capacity = self._undo_stack.pop()

    def get_capacity(self, vault):
        self._require(vault)
        return self._capacity[vault]

    def get_count(self, vault, denomination):
        self._require(vault)
        return self._vaults[vault].get(denomination, 0)

    def get_denominations(self, vault):
        self._require(vault)
        return sorted(self._vaults[vault])

    def get_vaults(self):
        return list(self._vaults)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        coins = {name: dict(c) for name, c in self._vaults.items()}
        self._undo_stack.append((coins, dict(self._capacity)))

    def _move_everything(self, from_vault, to_vault):
        coins = self._vaults[from_vault]
        moved = sum(coins.values())
        for denomination, count in list(coins.items()):
            change(self._vaults[to_vault], denomination, count)
        coins.clear()
        return moved

    def _require(self, vault):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(vault, str) or vault not in self._vaults:
            raise KeyError(vault)

    def _require_coins(self, vaults, vault, denomination, count):
        if vaults[vault].get(denomination, 0) < count:
            raise NotEnoughCoins(f"vault {vault!r} holds fewer than {count} coins of {denomination}")

    def _require_room(self, vaults, vault, count):
        capacity = self._capacity[vault]
        if capacity is not None and sum(vaults[vault].values()) + count > capacity:
            raise VaultFull(f"vault {vault!r} cannot take {count} more coins")
