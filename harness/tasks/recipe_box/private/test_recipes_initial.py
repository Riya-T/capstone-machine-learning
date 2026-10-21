"""Hidden tests for the initial recipe_box spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with recipes.py importable, e.g. in the sandbox):
    python -m pytest private/test_recipes_initial.py
"""

import pytest
from recipes import RecipeBox, RecipeError

BAD_NAMES = ["", None, 3]
BAD_QUANTITIES = [0, -5, 1.5, "10", None]


@pytest.fixture
def box():
    rb = RecipeBox()
    rb.add_recipe("pancakes", 4)
    rb.add_recipe("omelette", 1)
    rb.add_ingredient("pancakes", "flour", 200)
    rb.add_ingredient("pancakes", "egg", 2)
    return rb


def state(rb):
    """Every recipe's servings and ingredients, to check that a failed call changed nothing."""
    return {r: (rb.get_servings(r), rb.get_ingredients(r)) for r in rb.get_recipes()}


# --- recipes ----------------------------------------------------------------


def test_recipes_are_listed_in_the_order_added():
    rb = RecipeBox()
    for name in ["soup", "bread", "cake"]:
        rb.add_recipe(name, 2)
    assert rb.get_recipes() == ["soup", "bread", "cake"]


def test_servings_are_kept_per_recipe(box):
    assert box.get_servings("pancakes") == 4
    assert box.get_servings("omelette") == 1


def test_a_new_recipe_has_no_ingredients(box):
    assert box.get_ingredients("omelette") == []


@pytest.mark.parametrize("name", BAD_NAMES)
def test_invalid_recipe_names_are_rejected(name):
    rb = RecipeBox()
    with pytest.raises(ValueError):
        rb.add_recipe(name, 2)
    assert rb.get_recipes() == []


@pytest.mark.parametrize("servings", BAD_QUANTITIES)
def test_invalid_servings_are_rejected(servings):
    rb = RecipeBox()
    with pytest.raises(ValueError):
        rb.add_recipe("soup", servings)
    assert rb.get_recipes() == []


def test_adding_an_existing_recipe_is_rejected_and_changes_nothing(box):
    before = state(box)
    with pytest.raises(RecipeError):
        box.add_recipe("pancakes", 8)
    assert state(box) == before
    assert box.get_recipes() == ["pancakes", "omelette"]


def test_a_bad_name_is_reported_before_a_duplicate_check():
    rb = RecipeBox()
    rb.add_recipe("soup", 2)
    with pytest.raises(ValueError):
        rb.add_recipe("soup", 0)
    assert rb.get_servings("soup") == 2


@pytest.mark.parametrize(
    "call",
    [
        lambda rb: rb.add_ingredient("soup", "water", 500),
        lambda rb: rb.get_ingredients("soup"),
        lambda rb: rb.get_servings("soup"),
        lambda rb: rb.get_shopping_list(["soup"]),
        lambda rb: rb.get_shopping_list(["pancakes", "soup"]),
        lambda rb: rb.get_servings(None),
        lambda rb: rb.get_ingredients(3),
        lambda rb: rb.add_ingredient(None, "water", 500),
    ],
)
def test_unknown_recipes_raise_key_error(box, call):
    before = state(box)
    with pytest.raises(KeyError):
        call(box)
    assert state(box) == before


# --- ingredients ------------------------------------------------------------


def test_ingredients_keep_first_added_order(box):
    box.add_ingredient("pancakes", "milk", 300)
    box.add_ingredient("pancakes", "butter", 20)
    assert box.get_ingredients("pancakes") == [
        ("flour", 200),
        ("egg", 2),
        ("milk", 300),
        ("butter", 20),
    ]


def test_repeated_ingredient_adds_to_quantity_and_keeps_its_place(box):
    box.add_ingredient("pancakes", "milk", 300)
    box.add_ingredient("pancakes", "flour", 100)
    box.add_ingredient("pancakes", "flour", 1)
    assert box.get_ingredients("pancakes") == [("flour", 301), ("egg", 2), ("milk", 300)]


def test_ingredients_are_kept_per_recipe(box):
    box.add_ingredient("omelette", "egg", 3)
    assert box.get_ingredients("pancakes") == [("flour", 200), ("egg", 2)]
    assert box.get_ingredients("omelette") == [("egg", 3)]


@pytest.mark.parametrize("ingredient", BAD_NAMES)
def test_invalid_ingredient_names_are_rejected(box, ingredient):
    before = state(box)
    with pytest.raises(ValueError):
        box.add_ingredient("pancakes", ingredient, 100)
    assert state(box) == before


@pytest.mark.parametrize("quantity", BAD_QUANTITIES)
def test_invalid_quantities_are_rejected(box, quantity):
    before = state(box)
    with pytest.raises(ValueError):
        box.add_ingredient("pancakes", "flour", quantity)
    assert state(box) == before


def test_an_unknown_recipe_is_reported_before_a_bad_ingredient(box):
    with pytest.raises(KeyError):
        box.add_ingredient("soup", "", 0)
    with pytest.raises(KeyError):
        box.add_ingredient("soup", "water", -1)


def test_a_bad_ingredient_is_reported_before_a_bad_quantity(box):
    with pytest.raises(ValueError):
        box.add_ingredient("pancakes", "", -1)


# --- shopping list ----------------------------------------------------------


def test_shopping_list_of_one_recipe_matches_its_ingredients(box):
    assert box.get_shopping_list(["pancakes"]) == [("flour", 200), ("egg", 2)]


def test_shopping_list_totals_shared_ingredients(box):
    box.add_ingredient("omelette", "egg", 3)
    box.add_ingredient("omelette", "cheese", 50)
    assert box.get_shopping_list(["pancakes", "omelette"]) == [
        ("flour", 200),
        ("egg", 5),
        ("cheese", 50),
    ]


def test_shopping_list_order_follows_the_given_recipe_order(box):
    box.add_ingredient("omelette", "cheese", 50)
    box.add_ingredient("omelette", "egg", 3)
    assert box.get_shopping_list(["omelette", "pancakes"]) == [
        ("cheese", 50),
        ("egg", 5),
        ("flour", 200),
    ]


def test_shopping_list_of_no_recipes_is_empty(box):
    assert box.get_shopping_list([]) == []


def test_recipes_without_ingredients_add_nothing_to_the_list(box):
    assert box.get_shopping_list(["omelette"]) == []
    assert box.get_shopping_list(["omelette", "pancakes"]) == [("flour", 200), ("egg", 2)]


def test_shopping_list_does_not_change_the_recipes(box):
    before = state(box)
    box.get_shopping_list(["pancakes", "omelette"])
    box.get_shopping_list(["pancakes"])
    assert state(box) == before


def test_boxes_do_not_share_recipes():
    first, second = RecipeBox(), RecipeBox()
    first.add_recipe("soup", 2)
    first.add_ingredient("soup", "water", 500)
    assert second.get_recipes() == []
    second.add_recipe("soup", 6)
    assert second.get_servings("soup") == 6
    assert second.get_ingredients("soup") == []
