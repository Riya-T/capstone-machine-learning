"""Grain silos: tonnes counted per grain per silo.

Correct solution for grain_silos after c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.
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
        self._undo_stack = []  # copies of the state as it was before each recorded call

    def add_silo(self, name):
        check_name(name, "silo name")
        if name in self._silos:
            raise SiloError(f"silo name {name!r} is already used")
        self._record()
        self._silos[name] = {}

    def load(self, silo, grain, tonnes):
        self._require(silo)
        check_name(grain, "grain")
        check_tonnes(tonnes)
        self._record()
        change(self._silos[silo], grain, tonnes)

    def unload(self, silo, grain, tonnes):
        self._require(silo)
        check_tonnes(tonnes)
        if self._silos[silo].get(grain, 0) < tonnes:
            raise NotEnoughGrain(f"silo {silo!r} holds less than {tonnes} t of {grain}")
        self._record()
        change(self._silos[silo], grain, -tonnes)

    def blend_into(self, from_silo, to_silo):
        self._require(from_silo)
        self._require(to_silo)
        check_different(from_silo, to_silo)
        self._record()
        return self._move_everything(from_silo, to_silo)

    def demolish_silo(self, name, into):
        self._require(name)
        self._require(into)
        check_different(name, into)
        self._record()
        moved = self._move_everything(name, into)
        del self._silos[name]
        return moved

    def undo(self):
        if not self._undo_stack:
            raise SiloError("nothing to undo")
        self._silos = self._undo_stack.pop()

    def get_tonnes(self, silo, grain):
        self._require(silo)
        return self._silos[silo].get(grain, 0)

    def get_grains(self, silo):
        self._require(silo)
        return sorted(self._silos[silo])

    def get_silos(self):
        return list(self._silos)

    def _record(self):
        # Called by each call that changes the silos, once all its checks
        # have passed.
        silos = {name: dict(grains) for name, grains in self._silos.items()}
        self._undo_stack.append(silos)

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
