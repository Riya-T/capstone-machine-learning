"""URL shortener with code rules (allowed alphabet, length limit,
case-insensitive matching, reserved codes) where links can be disabled.

Correct solution for url_shortener after c_alias and c_disable.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from shortener import Shortener
    links = Shortener(reserved=("admin", "login"))
    links.add_link("Promo", "https://example.com/spring-sale")
    links.disable("promo")
"""

import string

CODE_CHARS = frozenset(string.ascii_letters + string.digits + "-_")
MAX_CODE_LENGTH = 32


class ShortenerError(Exception):
    pass


class ReservedCode(ShortenerError):
    pass


class LinkDisabled(ShortenerError):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_code(code):
    check_text(code, "code")
    if len(code) > MAX_CODE_LENGTH or not set(code) <= CODE_CHARS:
        raise ValueError(f"code {code!r} must be 1-32 letters, digits, '-' or '_'")


class Shortener:
    def __init__(self, reserved=()):
        self._reserved = set()
        for code in reserved:
            check_code(code)
            self._reserved.add(code.lower())
        self._names = {}  # lower-cased code -> code as added, in added order
        self._targets = {}  # lower-cased code -> current target
        self._hits = {}  # lower-cased code -> number of visits
        self._disabled = set()  # lower-cased codes that refuse visits

    def add_link(self, code, target):
        check_code(code)
        check_text(target, "target")
        key = code.lower()
        if key in self._reserved:
            raise ReservedCode(f"code {code!r} is reserved")
        if key in self._names:
            raise ShortenerError(f"code {code!r} already exists")
        self._names[key] = code
        self._targets[key] = target
        self._hits[key] = 0

    def visit(self, code):
        key = self._require(code)
        if key in self._disabled:
            raise LinkDisabled(f"code {code!r} is disabled")
        self._hits[key] += 1
        return self._targets[key]

    def set_target(self, code, target):
        key = self._require(code)
        check_text(target, "target")
        self._targets[key] = target

    def get_target(self, code):
        return self._targets[self._require(code)]

    def get_hits(self, code):
        return self._hits[self._require(code)]

    def get_codes(self):
        return list(self._names.values())

    def get_most_visited(self):
        # sorted is stable, so equal hit counts keep the added order.
        keys = sorted(self._names, key=lambda key: -self._hits[key])
        return [self._names[key] for key in keys]

    def disable(self, code):
        self._disabled.add(self._require(code))

    def enable(self, code):
        self._disabled.discard(self._require(code))

    def is_enabled(self, code):
        return self._require(code) not in self._disabled

    def _require(self, code):
        """Return the lookup key for an existing code, else raise KeyError."""
        if not isinstance(code, str) or code.lower() not in self._names:
            raise KeyError(code)
        return code.lower()
