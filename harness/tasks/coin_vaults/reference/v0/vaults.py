"""Coin vaults: coins counted per denomination per vault.

Correct solution for the initial coin_vaults spec.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.
"""


class VaultError(Exception):
    pass


class NotEnoughCoins(VaultError):
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

    def add_vault(self, name):
        check_name(name)
        if name in self._vaults:
            raise VaultError(f"vault name {name!r} is already used")
        self._vaults[name] = {}

    def deposit(self, vault, denomination, count):
        self._require(vault)
        if denomination not in self._accepted:
            raise ValueError(f"denomination {denomination!r} is not accepted")
        check_count(count)
        change(self._vaults[vault], denomination, count)

    def withdraw(self, vault, denomination, count):
        self._require(vault)
        check_count(count)
        self._require_coins(self._vaults, vault, denomination, count)
        change(self._vaults[vault], denomination, -count)

    def consolidate(self, from_vault, to_vault):
        self._require(from_vault)
        self._require(to_vault)
        check_different(from_vault, to_vault)
        return self._move_everything(from_vault, to_vault)

    def close_vault(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        moved = self._move_everything(name, into)
        del self._vaults[name]
        return moved

    def get_count(self, vault, denomination):
        self._require(vault)
        return self._vaults[vault].get(denomination, 0)

    def get_denominations(self, vault):
        self._require(vault)
        return sorted(self._vaults[vault])

    def get_vaults(self):
        return list(self._vaults)

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
