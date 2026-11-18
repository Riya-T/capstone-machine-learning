Give tanks in `aquarium.py` a capacity, since a small tank can only hold
so many fish.

- `add_tank` takes a new keyword argument: `add_tank(name, capacity=None)`.
  `None` means the tank has no limit. Otherwise `capacity` is an `int`
  greater than 0: the most fish, of all species together, that the tank
  may hold. A capacity of 0 or less raises `ValueError` and adds no tank.
- Add `Aquarium.get_capacity(tank) -> int | None`. It returns the tank's
  capacity (`None` for no limit) and raises `KeyError` for a tank that is
  not in use.
- Add `class TankFull(AquariumError)` to `aquarium.py`.
- A tank never holds more fish than its capacity. Every call that puts
  fish into a tank checks it: `add_fish`, and the receiving tank
  (`to_tank`) of `move_all` and `drain_tank`. If the receiving tank would
  end up with more fish than its capacity, the call raises `TankFull` and
  changes nothing: `move_all` and `drain_tank` move no fish at all, and
  `drain_tank` does not remove the tank.
- Ending up with exactly as many fish as the capacity is allowed.
- `remove_fish` never checks the capacity, and the capacity of the tank
  the fish leave is never checked.
- A tank added under the name of a drained tank gets the capacity given
  in its own `add_tank` call, not the drained tank's.
- `undo` still puts back the exact earlier state, capacities included: an
  undone `drain_tank` brings the tank back with its capacity, and after an
  undone `add_tank` the name may be added again with any capacity.
- When a call has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
