"""Recipe binder with undo, locked sections and recipe orders.

Correct solution for recipe_binder after c_undo, c_locked and
c_recipe_order. Never shown to the writer or the editor; validate-tasks
checks that it passes every test it should.

Usage:
    from binder import RecipeBinder
    b = RecipeBinder(recipe_order="name")
    b.add_recipe("root", "toast")
    b.add_recipe("root", "bagel")
    b.get_recipes("root")  # ["bagel", "toast"]
"""

import copy

ROOT = "root"
RECIPE_ORDERS = ("added", "name")


class BinderError(Exception):
    pass


class SectionLocked(BinderError):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} must be a non-empty str")


def check_order(order):
    if not isinstance(order, str) or order not in RECIPE_ORDERS:
        raise ValueError(f"recipe order must be 'added' or 'name', got {order!r}")


class RecipeBinder:
    def __init__(self, recipe_order="added"):
        check_order(recipe_order)
        self._default_order = recipe_order
        self._parent = {ROOT: None}  # section -> parent section (None for root)
        self._subsections = {ROOT: []}  # section -> subsections in arrival order
        self._recipes = {ROOT: []}  # section -> recipes in arrival order
        self._where = {}  # recipe -> section that holds it
        self._locked = {ROOT: False}  # section -> locked?
        self._order = {ROOT: recipe_order}  # section -> "added" or "name"
        self._history = []  # copies of the state from before each recorded call

    def add_section(self, name, parent):
        with _Recorded(self):
            self._require(parent)
            check_name(name, "section name")
            if name in self._parent:
                raise BinderError(f"section {name!r} already exists")
            self._parent[name] = parent
            self._subsections[name] = []
            self._recipes[name] = []
            self._locked[name] = False
            self._order[name] = self._default_order
            self._subsections[parent].append(name)

    def add_recipe(self, section, recipe):
        with _Recorded(self):
            self._require(section)
            check_name(recipe, "recipe name")
            if recipe in self._where:
                raise BinderError(f"recipe {recipe!r} is already in the binder")
            self._require_unlocked(section)
            self._recipes[section].append(recipe)
            self._where[recipe] = section

    def remove_recipe(self, recipe):
        with _Recorded(self):
            self._require_recipe(recipe)
            section = self._where.pop(recipe)
            self._require_unlocked(section)
            self._recipes[section].remove(recipe)

    def move_section(self, name, new_parent):
        with _Recorded(self):
            self._require(name)
            self._require(new_parent)
            if name == ROOT:
                raise BinderError("the root section cannot be moved")
            section = new_parent
            while section is not None:
                if section == name:
                    raise BinderError(f"section {name!r} cannot be put inside itself")
                section = self._parent[section]
            self._subsections[self._parent[name]].remove(name)
            self._subsections[new_parent].append(name)
            self._parent[name] = new_parent

    def delete_section(self, name):
        with _Recorded(self):
            self._require(name)
            if name == ROOT:
                raise BinderError("the root section cannot be deleted")
            parent = self._parent[name]
            self._require_unlocked(name)
            self._require_unlocked(parent)
            del self._parent[name]
            del self._locked[name]
            del self._order[name]
            recipes = self._recipes.pop(name)
            subsections = self._subsections.pop(name)
            self._subsections[parent].remove(name)
            self._recipes[parent].extend(recipes)
            for recipe in recipes:
                self._where[recipe] = parent
            self._subsections[parent].extend(subsections)
            for section in subsections:
                self._parent[section] = parent

    def set_locked(self, section, locked):
        with _Recorded(self):
            self._require(section)
            if not isinstance(locked, bool):
                raise ValueError("locked must be True or False")
            self._locked[section] = locked

    def get_locked(self, section):
        self._require(section)
        return self._locked[section]

    def set_recipe_order(self, section, order):
        with _Recorded(self):
            self._require(section)
            check_order(order)
            self._order[section] = order

    def get_recipe_order(self, section):
        self._require(section)
        return self._order[section]

    def undo(self):
        if not self._history:
            raise BinderError("nothing to undo")
        self._set_state(self._history.pop())

    def get_recipes(self, section):
        self._require(section)
        if self._order[section] == "name":
            return sorted(self._recipes[section])
        return list(self._recipes[section])

    def get_subsections(self, section):
        self._require(section)
        return list(self._subsections[section])

    def get_section_of(self, recipe):
        self._require_recipe(recipe)
        return self._where[recipe]

    def _get_state(self):
        state = (
            self._parent,
            self._subsections,
            self._recipes,
            self._where,
            self._locked,
            self._order,
        )
        return copy.deepcopy(state)

    def _set_state(self, state):
        (
            self._parent,
            self._subsections,
            self._recipes,
            self._where,
            self._locked,
            self._order,
        ) = state

    def _require_unlocked(self, section):
        if self._locked[section]:
            raise SectionLocked(f"section {section!r} is locked")

    def _require(self, section):
        if not isinstance(section, str) or section not in self._parent:
            raise KeyError(section)

    def _require_recipe(self, recipe):
        if not isinstance(recipe, str) or recipe not in self._where:
            raise KeyError(recipe)


class _Recorded:
    """One recorded call: on success the state from before it goes on the
    history; on an error the state is put back and nothing is recorded."""

    def __init__(self, binder):
        self.binder = binder

    def __enter__(self):
        self.before = self.binder._get_state()

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.binder._history.append(self.before)
        else:
            self.binder._set_state(self.before)
        return False
