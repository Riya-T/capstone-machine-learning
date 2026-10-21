# Recipe box

Write a module `recipes.py` that keeps a collection of recipes, the number
of servings each one makes, and the ingredients each one needs.

## Interface

```python
class RecipeError(Exception): ...


class RecipeBox:
    def __init__(self): ...
    def add_recipe(self, name: str, servings: int) -> None: ...
    def add_ingredient(self, recipe: str, ingredient: str, quantity: int) -> None: ...
    def get_ingredients(self, recipe: str) -> list[tuple[str, int]]: ...
    def get_servings(self, recipe: str) -> int: ...
    def get_recipes(self) -> list[str]: ...
    def get_shopping_list(self, recipes: list[str]) -> list[tuple[str, int]]: ...
```

All quantities are whole units (grams, millilitres, pieces), as `int`.

## Recipes

- `add_recipe(name, servings)` adds a recipe with no ingredients. The name
  must be a non-empty string and the servings an `int` greater than 0, or
  `ValueError` is raised. Adding a name that already exists raises
  `RecipeError`. If both the name and the servings are invalid, either
  `ValueError` may come first.
- `get_recipes()` returns the names of all recipes, in the order they were
  added.
- `get_servings(recipe)` returns the servings the recipe was added with.
- Every method that takes a recipe name raises `KeyError` when the recipe
  does not exist, including values that are not strings at all, such as
  `None` or `3`.

## Ingredients

- `add_ingredient(recipe, ingredient, quantity)` adds `quantity` of the
  ingredient to the recipe. The ingredient must be a non-empty string and
  the quantity an `int` greater than 0, or `ValueError` is raised.
- Adding an ingredient the recipe already has adds to its quantity; the
  ingredient keeps its place in the list.
- `get_ingredients(recipe)` returns `(ingredient, quantity)` tuples, in the
  order the ingredients were first added to that recipe.

When a call has several problems, the first of these is raised:

1. `KeyError` for a recipe that does not exist;
2. `ValueError` for an invalid ingredient;
3. `ValueError` for an invalid quantity.

## Shopping list

`get_shopping_list(recipes)` takes a list of recipe names and returns the
total quantity of every ingredient those recipes need together, as
`(ingredient, total)` tuples. Ingredients are listed in the order they are
first met when going through the given recipes in the given order, and
through each recipe's ingredients in their order. An empty list gives `[]`.
If any name in the list is not a recipe, `KeyError` is raised.

A failed call has no effect: if a method raises, every recipe and every
ingredient list is unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes `bool` values passed as servings or quantities, a recipe named more
than once in the list given to `get_shopping_list`, what happens if a
returned list is changed, the text of error messages, saving the recipes to
a file, and use from several threads.
