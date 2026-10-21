Sort the recipes in `recipes.py` into categories such as "breakfast" or
"dessert".

- `add_recipe` takes a new keyword argument `category="uncategorized"`. It
  must be a non-empty string, or `ValueError` is raised and no recipe is
  added. When several arguments are invalid, any of their `ValueError`s may
  be raised; a `ValueError` always comes before the `RecipeError` for a
  duplicate name.
- Add `RecipeBox.get_category(recipe) -> str`, which returns the recipe's
  current category. Raises `KeyError` for a recipe that does not exist.
- Add `RecipeBox.set_category(recipe, category)`, which moves the recipe to
  another category. Raises `KeyError` for a recipe that does not exist,
  then `ValueError` for an invalid category. Nothing changes on failure.
- `get_recipes` takes a new keyword argument `category=None`. With a
  category, only the recipes currently in that category are returned, still
  in the order they were added. A category no recipe is in gives `[]`.
- Add `RecipeBox.get_categories() -> list[str]`: every category that at
  least one recipe is currently in, in the order of first appearance when
  going through `get_recipes()`. A category every recipe has left is not
  listed.
- `get_cookable` takes the same keyword argument `category=None`, with the
  same meaning.
- Categories play no part in `get_shopping_list`.

All existing behavior must keep working.
