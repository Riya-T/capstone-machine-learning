Add hit statistics to `shortener.py`.

- Add `Shortener.get_total_hits() -> int`: the number of hits over all
  links.
- Add `Shortener.get_target_hits(target) -> int`: how many visits were
  answered with `target`, through any code, including visits made before a
  code was pointed somewhere else by `set_target`. A target that was never
  served gives 0. `target` must be a non-empty `str`, or `ValueError` is
  raised.
- Add `Shortener.get_hits_for_current_target(code) -> int`: the link's hits
  since its target was last set with `set_target`, or all of its hits if
  `set_target` was never called on it. Every successful `set_target` call
  starts the count again at 0, even when the target is the same as before.
  Raises `KeyError` for a code that does not exist.
- Add `Shortener.get_unvisited() -> list[str]`: the codes with no hits at
  all, in the order they were added.
- A `visit` that raises counts for nothing in any of these.

All existing behavior must keep working.
