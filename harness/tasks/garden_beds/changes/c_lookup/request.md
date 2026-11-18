Let `garden.py` answer questions about one species across the whole
garden, for example where the roses are and how many there are.

- Add `Garden.get_beds_with(species) -> list[str]`. It returns the beds
  that have at least one plant of `species`, in the order of `get_beds()`.
  A species that grows nowhere gives an empty list.
- Add `Garden.get_total(species) -> int`. It returns how many plants of
  `species` there are in all beds together: 0 for a species that grows
  nowhere.
- Both always reflect the current beds: after a `plant`, `pull`,
  `transplant_all` or `clear_bed` they report the plants where they are
  now, and a cleared bed is never listed.
- Neither of them changes anything.

All existing behavior must keep working.
