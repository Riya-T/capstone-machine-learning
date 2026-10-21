"""Recipe box with a pantry, where ingredients can be removed and additions undone.

Planted bug (after c_remove and c_pantry): the pantry was added correctly,
but remove_ingredient no longer discards the recipe's undo history, so an
undo after a removal re-applies an old addition.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from recipes import RecipeBox
    box = RecipeBox()
    box.add_recipe("pancakes", 4)
    box.add_ingredient("pancakes", "flour", 200)
    box.undo_add("pancakes")
    box.stock("flour", 500)
"""


class RecipeError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_quantity(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class RecipeBox:
    def __init__(self):
        self._servings = {}  # recipe name -> servings, in the order added
        self._ingredients = {}  # recipe name -> {ingredient: quantity}, in first-added order
        self._additions = {}  # recipe name -> [(ingredient, quantity)] not yet undone
        self._pantry = {}  # ingredient -> quantity in stock, in first-stocked order

    def add_recipe(self, name, servings):
        check_name(name, "recipe name")
        check_quantity(servings, "servings")
        if name in self._servings:
            raise RecipeError(f"recipe {name!r} already exists")
        self._servings[name] = servings
        self._ingredients[name] = {}
        self._additions[name] = []

    def add_ingredient(self, recipe, ingredient, quantity):
        self._require(recipe)
        check_name(ingredient, "ingredient")
        check_quantity(quantity, "quantity")
        amounts = self._ingredients[recipe]
        amounts[ingredient] = amounts.get(ingredient, 0) + quantity
        self._additions[recipe].append((ingredient, quantity))

    def get_ingredients(self, recipe):
        self._require(recipe)
        return list(self._ingredients[recipe].items())

    def get_servings(self, recipe):
        self._require(recipe)
        return self._servings[recipe]

    def get_recipes(self):
        return list(self._servings)

    def get_shopping_list(self, recipes):
        for recipe in recipes:
            self._require(recipe)
        totals = {}
        for recipe in recipes:
            for ingredient, quantity in self._ingredients[recipe].items():
                totals[ingredient] = totals.get(ingredient, 0) + quantity
        return list(totals.items())

    def remove_ingredient(self, recipe, ingredient):
        self._require(recipe)
        amounts = self._ingredients[recipe]
        if not isinstance(ingredient, str) or ingredient not in amounts:
            raise RecipeError(f"recipe {recipe!r} has no ingredient {ingredient!r}")
        del amounts[ingredient]

    def undo_add(self, recipe):
        self._require(recipe)
        if not self._additions[recipe]:
            raise RecipeError(f"nothing to undo on recipe {recipe!r}")
        ingredient, quantity = self._additions[recipe].pop()
        amounts = self._ingredients[recipe]
        amounts[ingredient] -= quantity
        if amounts[ingredient] == 0:
            del amounts[ingredient]

    def stock(self, ingredient, quantity):
        check_name(ingredient, "ingredient")
        check_quantity(quantity, "quantity")
        self._pantry[ingredient] = self._pantry.get(ingredient, 0) + quantity

    def get_pantry(self):
        return list(self._pantry.items())

    def get_missing(self, recipe):
        self._require(recipe)
        missing = []
        for ingredient, needed in self._ingredients[recipe].items():
            shortfall = needed - self._pantry.get(ingredient, 0)
            if shortfall > 0:
                missing.append((ingredient, shortfall))
        return missing

    def get_cookable(self):
        return [name for name in self._servings if not self.get_missing(name)]

    def cook(self, recipe):
        self._require(recipe)
        if self.get_missing(recipe):
            raise RecipeError(f"not enough in the pantry for {recipe!r}")
        for ingredient, needed in self._ingredients[recipe].items():
            self._pantry[ingredient] -= needed

    def _require(self, recipe):
        # Non-str names are never stored, so they count as "unknown" too.
        if not isinstance(recipe, str) or recipe not in self._servings:
            raise KeyError(recipe)
