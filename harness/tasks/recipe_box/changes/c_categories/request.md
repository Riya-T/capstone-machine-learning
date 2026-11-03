Sort the recipes in `recipes.py` into categories such as "breakfast" or
"dessert".

- `add_recipe` takes a new keyword argument `category="uncategorized"`. An
  empty string or `None` as the category raises `ValueError`, and no recipe
  is added. When several arguments are invalid, any of their `ValueError`s
  may be raised. If the category is invalid and the name already exists,
  which error is raised is unspecified.
- Add `RecipeBox.get_category(recipe) -> str`, which returns the recipe's
  current category. Raises `KeyError` for a recipe that does not exist.
- Add `RecipeBox.set_category(recipe, category)`, which moves the recipe to
  another category. Raises `KeyError` for a recipe that does not exist and
  `ValueError` for an invalid category; which of the two is raised when
  both apply is unspecified. Nothing changes on failure.
- `get_recipes` takes a new keyword argument `category=None`. With a
  category, only the recipes currently in that category are returned, still
  in the order they were added. A category no recipe is in gives `[]`.
- Add `RecipeBox.get_categories() -> list[str]`: every category that at
  least one recipe is currently in, in the order of first appearance when
  going through `get_recipes()`. A category every recipe has left is not
  listed. For example, after adding `"toast"` with category `"breakfast"`,
  `"cake"` with `"dessert"` and `"tea"` with no category,
  `get_categories()` is `["breakfast", "dessert", "uncategorized"]`. After
  `set_category("cake", "snack")` it is
  `["breakfast", "snack", "uncategorized"]`, and after
  `set_category("tea", "dessert")` it is `["breakfast", "snack", "dessert"]`.
- `get_cookable` takes the same keyword argument `category=None`, with the
  same meaning.
- Categories play no part in `get_shopping_list`.

All existing behavior must keep working.
