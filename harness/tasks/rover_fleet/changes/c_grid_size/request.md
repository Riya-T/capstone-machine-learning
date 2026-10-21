Missions now land on plateaus of different sizes, and some plateaus are
bounded by cliffs instead of wrapping around. Make the plateau adjustable
in `rovers.py`.

- `RoverFleet` takes three new keyword arguments:
  `RoverFleet(width=10, height=10, wrap=True)`. `width` is the number of
  cells from west to east and `height` from south to north, so `x` runs
  from 0 to `width - 1` and `y` from 0 to `height - 1`. Both must be `int`s
  of at least 1 (not `bool`s), and `wrap` must be a `bool`; anything else
  raises `ValueError`.
- Every rule that used the fixed 10 by 10 plateau now uses `width` and
  `height`: the cells `land` accepts, the cells `get_rover_at` accepts, and
  where a rover comes back in when it wraps around an edge.
- With `wrap=False` the edges cannot be crossed. A move that would take a
  rover off the plateau is blocked, exactly like a move onto another
  rover: the rover stays, and that move and the rest of the string are not
  carried out.
- `land` takes a new keyword argument `wrap=None`. `None` means the rover
  follows the fleet's `wrap` setting; `True` or `False` sets it for this
  rover alone. Any other value raises `ValueError`, in the same place in
  the error order as an invalid `facing`, and no rover lands.
- Add `RoverFleet.get_plateau() -> tuple[int, int]`, which returns
  `(width, height)`.

All existing behavior must keep working.
