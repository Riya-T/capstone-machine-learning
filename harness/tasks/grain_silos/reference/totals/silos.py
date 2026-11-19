"""Grain silos: tonnes counted per grain per silo.

Correct solution for grain_silos after c_totals.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from silos import Silos
    silos = Silos()
    silos.add_silo("north")
    silos.load("north", "wheat", 40)
    silos.unload("north", "wheat", 15)
    silos.get_tonnes("north", "wheat")  # 25
"""


class SiloError(Exception):
    pass


class NotEnoughGrain(SiloError):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} must be a non-empty str")


def check_tonnes(tonnes):
    if isinstance(tonnes, bool) or not isinstance(tonnes, int) or tonnes <= 0:
        raise ValueError(f"tonnes must be a positive int, got {tonnes!r}")


def check_different(from_silo, to_silo):
    if from_silo == to_silo:
        raise ValueError("the two silos must be different")


def change(grains, grain, delta):
    """Add delta tonnes to one silo's {grain: tonnes}; only amounts above 0
    are stored."""
    new_tonnes = grains.get(grain, 0) + delta
    if new_tonnes:
        grains[grain] = new_tonnes
    else:
        del grains[grain]


class Silos:
    def __init__(self):
        # silo name -> {grain: tonnes}, in the order the silos were added
        self._silos = {}

    def add_silo(self, name):
        check_name(name, "silo name")
        if name in self._silos:
            raise SiloError(f"silo name {name!r} is already used")
        self._silos[name] = {}

    def load(self, silo, grain, tonnes):
        self._require(silo)
        check_name(grain, "grain")
        check_tonnes(tonnes)
        change(self._silos[silo], grain, tonnes)

    def unload(self, silo, grain, tonnes):
        self._require(silo)
        check_tonnes(tonnes)
        if self._silos[silo].get(grain, 0) < tonnes:
            raise NotEnoughGrain(f"silo {silo!r} holds less than {tonnes} t of {grain}")
        change(self._silos[silo], grain, -tonnes)

    def blend_into(self, from_silo, to_silo):
        self._require(from_silo)
        self._require(to_silo)
        check_different(from_silo, to_silo)
        return self._move_everything(from_silo, to_silo)

    def demolish_silo(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        moved = self._move_everything(name, into)
        del self._silos[name]
        return moved

    def get_total(self, silo):
        self._require(silo)
        return sum(self._silos[silo].values())

    def get_grain_total(self, grain):
        return sum(grains.get(grain, 0) for grains in self._silos.values())

    def get_tonnes(self, silo, grain):
        self._require(silo)
        return self._silos[silo].get(grain, 0)

    def get_grains(self, silo):
        self._require(silo)
        return sorted(self._silos[silo])

    def get_silos(self):
        return list(self._silos)

    def _move_everything(self, from_silo, to_silo):
        grains = self._silos[from_silo]
        moved = sum(grains.values())
        for grain, tonnes in list(grains.items()):
            change(self._silos[to_silo], grain, tonnes)
        grains.clear()
        return moved

    def _require(self, silo):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(silo, str) or silo not in self._silos:
            raise KeyError(silo)
