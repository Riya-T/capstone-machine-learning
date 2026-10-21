"""URL shortener: short codes, the addresses they point to, and hit counts.

Planted bug (initial version): codes with the same number of hits come out
newest first instead of in the order added, because the sort key includes
the position and the whole key is reversed. The public checks have no ties,
so only the hidden initial tests catch it. Never shown to the writer or the
editor; validate-tasks checks that the tests catch it.

Usage:
    from shortener import Shortener
    links = Shortener()
    links.add_link("promo", "https://example.com/spring-sale")
    links.visit("promo")
"""


class ShortenerError(Exception):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class Shortener:
    def __init__(self):
        self._targets = {}  # code -> current target, in added order
        self._hits = {}  # code -> number of visits

    def add_link(self, code, target):
        check_text(code, "code")
        check_text(target, "target")
        if code in self._targets:
            raise ShortenerError(f"code {code!r} already exists")
        self._targets[code] = target
        self._hits[code] = 0

    def visit(self, code):
        self._require(code)
        self._hits[code] += 1
        return self._targets[code]

    def set_target(self, code, target):
        self._require(code)
        check_text(target, "target")
        self._targets[code] = target

    def get_target(self, code):
        self._require(code)
        return self._targets[code]

    def get_hits(self, code):
        self._require(code)
        return self._hits[code]

    def get_codes(self):
        return list(self._targets)

    def get_most_visited(self):
        order = {code: i for i, code in enumerate(self._targets)}
        return sorted(self._targets, key=lambda c: (self._hits[c], order[c]), reverse=True)

    def _require(self, code):
        # Non-str codes are never stored, so they count as missing too.
        if not isinstance(code, str) or code not in self._targets:
            raise KeyError(code)
