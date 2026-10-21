"""Recipe box with a pantry and recipe categories.

Planted bug (after c_pantry and c_categories): categories were added
correctly, but cook no longer refuses a recipe with missing ingredients and
takes what it can from the pantry.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from recipes import RecipeBox
    box = RecipeBox()
    box.add_recipe("pancakes", 4, category="breakfast")
    box.add_ingredient("pancakes", "flour", 200)
    box.stock("flour", 500)
    box.get_cookable(category="breakfast")
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
        self._categories = {}  # recipe name -> category
        self._pantry = {}  # ingredient -> quantity in stock, in first-stocked order

    def add_recipe(self, name, servings, category="uncategorized"):
        check_name(name, "recipe name")
        check_quantity(servings, "servings")
        check_name(category, "category")
        if name in self._servings:
            raise RecipeError(f"recipe {name!r} already exists")
        self._servings[name] = servings
        self._ingredients[name] = {}
        self._categories[name] = category

    def add_ingredient(self, recipe, ingredient, quantity):
        self._require(recipe)
        check_name(ingredient, "ingredient")
        check_quantity(quantity, "quantity")
        amounts = self._ingredients[recipe]
        amounts[ingredient] = amounts.get(ingredient, 0) + quantity

    def get_ingredients(self, recipe):
        self._require(recipe)
        return list(self._ingredients[recipe].items())

    def get_servings(self, recipe):
        self._require(recipe)
        return self._servings[recipe]

    def get_recipes(self, category=None):
        return [name for name in self._servings if self._in_category(name, category)]

    def get_shopping_list(self, recipes):
        for recipe in recipes:
            self._require(recipe)
        totals = {}
        for recipe in recipes:
            for ingredient, quantity in self._ingredients[recipe].items():
                totals[ingredient] = totals.get(ingredient, 0) + quantity
        return list(totals.items())

    def get_category(self, recipe):
        self._require(recipe)
        return self._categories[recipe]

    def set_category(self, recipe, category):
        self._require(recipe)
        check_name(category, "category")
        self._categories[recipe] = category

    def get_categories(self):
        seen = []
        for name in self._servings:
            if self._categories[name] not in seen:
                seen.append(self._categories[name])
        return seen

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

    def get_cookable(self, category=None):
        return [name for name in self.get_recipes(category) if not self.get_missing(name)]

    def cook(self, recipe):
        self._require(recipe)
        for ingredient, needed in self._ingredients[recipe].items():
            self._pantry[ingredient] = self._pantry.get(ingredient, 0) - needed

    def _in_category(self, recipe, category):
        return category is None or self._categories[recipe] == category

    def _require(self, recipe):
        # Non-str names are never stored, so they count as "unknown" too.
        if not isinstance(recipe, str) or recipe not in self._servings:
            raise KeyError(recipe)
