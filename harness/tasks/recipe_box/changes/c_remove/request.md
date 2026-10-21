Let ingredients be taken back out of a recipe in `recipes.py`.

- Add `RecipeBox.remove_ingredient(recipe, ingredient)`, which removes the
  ingredient from the recipe entirely, whatever its quantity. Raises
  `KeyError` for a recipe that does not exist, then `RecipeError` when the
  recipe does not have that ingredient (including values that are not
  strings). An ingredient added again after being removed goes to the end
  of the recipe's ingredient list.
- Add `RecipeBox.undo_add(recipe)`, which reverses the most recent
  `add_ingredient` call on that recipe that has not been reversed yet. If
  that call created the ingredient, the ingredient disappears from the
  recipe; if it added to an ingredient the recipe already had, the
  quantity goes back to what it was before and the ingredient keeps its
  place. Calling `undo_add` again steps back one more addition. Raises
  `KeyError` for a recipe that does not exist, then `RecipeError` when
  there is nothing left to reverse.
- `remove_ingredient` discards the recipe's undo history: straight after
  it, `undo_add` raises `RecipeError` until an ingredient is added to that
  recipe again. Removals themselves cannot be undone.
- Neither method touches other recipes, and a failed call changes nothing.

All existing behavior must keep working.
