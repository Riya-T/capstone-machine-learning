Add a pantry to `recipes.py`, so the box can tell which recipes can be
cooked with what is in stock.

- Add `RecipeBox.stock(ingredient, quantity)`, which adds `quantity` of the
  ingredient to the pantry. The ingredient must be a non-empty string and
  the quantity an `int` greater than 0, or `ValueError` is raised (the
  ingredient is checked first). The pantry is independent of the recipes:
  stocking an ingredient no recipe uses is fine.
- Add `RecipeBox.get_pantry() -> list[tuple[str, int]]`: every stocked
  ingredient with the quantity currently in the pantry, in the order the
  ingredients were first stocked. An ingredient stays listed when its
  quantity has fallen to 0.
- Add `RecipeBox.get_missing(recipe) -> list[tuple[str, int]]`: for every
  ingredient of the recipe that the pantry does not fully cover, the
  ingredient and the shortfall (needed minus in stock), in the recipe's
  ingredient order. An ingredient never stocked counts as 0 in stock. A
  recipe that can be cooked gives `[]`. Raises `KeyError` for a recipe that
  does not exist.
- Add `RecipeBox.get_cookable() -> list[str]`: the names of the recipes
  with nothing missing, in the order the recipes were added. A recipe
  without ingredients is always cookable.
- Add `RecipeBox.cook(recipe)`, which takes the recipe's ingredients out of
  the pantry. Raises `KeyError` for a recipe that does not exist, then
  `RecipeError` if anything is missing. A failed call changes nothing. The
  recipe itself is unchanged by cooking.

All existing behavior must keep working.
