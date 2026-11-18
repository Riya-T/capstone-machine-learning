"""Recipe binder: recipes in a tree of sections.

Planted bug (initial spec): delete_section gives its recipes to its parent
but does not update which section holds them, so get_section_of still
reports the deleted section. Never shown to the writer or the editor;
validate-tasks checks that the tests catch it.

Usage:
    from binder import RecipeBinder
    b = RecipeBinder()
    b.add_section("soups", "root")
    b.add_recipe("soups", "minestrone")
    b.delete_section("soups")  # minestrone is now in root
"""

ROOT = "root"


class BinderError(Exception):
    pass


def check_name(name, what):
    if not isinstance(name, str) or not name:
        raise ValueError(f"{what} must be a non-empty str")


class RecipeBinder:
    def __init__(self):
        self._parent = {ROOT: None}  # section -> parent section (None for root)
        self._subsections = {ROOT: []}  # section -> subsections in arrival order
        self._recipes = {ROOT: []}  # section -> recipes in arrival order
        self._where = {}  # recipe -> section that holds it

    def add_section(self, name, parent):
        self._require(parent)
        check_name(name, "section name")
        if name in self._parent:
            raise BinderError(f"section {name!r} already exists")
        self._parent[name] = parent
        self._subsections[name] = []
        self._recipes[name] = []
        self._subsections[parent].append(name)

    def add_recipe(self, section, recipe):
        self._require(section)
        check_name(recipe, "recipe name")
        if recipe in self._where:
            raise BinderError(f"recipe {recipe!r} is already in the binder")
        self._recipes[section].append(recipe)
        self._where[recipe] = section

    def remove_recipe(self, recipe):
        self._require_recipe(recipe)
        section = self._where.pop(recipe)
        self._recipes[section].remove(recipe)

    def move_section(self, name, new_parent):
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
        self._require(name)
        if name == ROOT:
            raise BinderError("the root section cannot be deleted")
        parent = self._parent.pop(name)
        recipes = self._recipes.pop(name)
        subsections = self._subsections.pop(name)
        self._subsections[parent].remove(name)
        self._recipes[parent].extend(recipes)
        self._subsections[parent].extend(subsections)
        for section in subsections:
            self._parent[section] = parent

    def get_recipes(self, section):
        self._require(section)
        return list(self._recipes[section])

    def get_subsections(self, section):
        self._require(section)
        return list(self._subsections[section])

    def get_section_of(self, recipe):
        self._require_recipe(recipe)
        return self._where[recipe]

    def _require(self, section):
        if not isinstance(section, str) or section not in self._parent:
            raise KeyError(section)

    def _require_recipe(self, recipe):
        if not isinstance(recipe, str) or recipe not in self._where:
            raise KeyError(recipe)
