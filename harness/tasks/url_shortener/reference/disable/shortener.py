"""URL shortener where links can be disabled.

Correct solution for url_shortener after c_disable.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from shortener import Shortener
    links = Shortener()
    links.add_link("promo", "https://example.com/spring-sale")
    links.disable("promo")
"""


class ShortenerError(Exception):
    pass


class LinkDisabled(ShortenerError):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class Shortener:
    def __init__(self):
        self._targets = {}  # code -> current target, in added order
        self._hits = {}  # code -> number of visits
        self._disabled = set()  # codes that refuse visits

    def add_link(self, code, target):
        check_text(code, "code")
        check_text(target, "target")
        if code in self._targets:
            raise ShortenerError(f"code {code!r} already exists")
        self._targets[code] = target
        self._hits[code] = 0

    def visit(self, code):
        self._require(code)
        if code in self._disabled:
            raise LinkDisabled(f"code {code!r} is disabled")
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
        # sorted is stable, so equal hit counts keep the added order.
        return sorted(self._targets, key=lambda code: -self._hits[code])

    def disable(self, code):
        self._require(code)
        self._disabled.add(code)

    def enable(self, code):
        self._require(code)
        self._disabled.discard(code)

    def is_enabled(self, code):
        self._require(code)
        return code not in self._disabled

    def _require(self, code):
        # Non-str codes are never stored, so they count as missing too.
        if not isinstance(code, str) or code not in self._targets:
            raise KeyError(code)
