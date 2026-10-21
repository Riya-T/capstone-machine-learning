"""URL shortener where links can be disabled, with hit statistics.

Correct solution for url_shortener after c_disable and c_stats.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from shortener import Shortener
    links = Shortener()
    links.add_link("promo", "https://example.com/spring-sale")
    links.visit("promo")
    links.get_target_hits("https://example.com/spring-sale")
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
        self._visits = []  # (code, target served) for every successful visit
        self._retargeted_at = {}  # code -> len(self._visits) when last set_target ran

    def add_link(self, code, target):
        check_text(code, "code")
        check_text(target, "target")
        if code in self._targets:
            raise ShortenerError(f"code {code!r} already exists")
        self._targets[code] = target
        self._hits[code] = 0
        self._retargeted_at[code] = 0

    def visit(self, code):
        self._require(code)
        if code in self._disabled:
            raise LinkDisabled(f"code {code!r} is disabled")
        target = self._targets[code]
        self._hits[code] += 1
        self._visits.append((code, target))
        return target

    def set_target(self, code, target):
        self._require(code)
        check_text(target, "target")
        self._targets[code] = target
        self._retargeted_at[code] = len(self._visits)

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

    def get_total_hits(self):
        return len(self._visits)

    def get_target_hits(self, target):
        check_text(target, "target")
        return sum(1 for _, served in self._visits if served == target)

    def get_hits_for_current_target(self, code):
        self._require(code)
        since = self._retargeted_at[code]
        return sum(1 for visited, _ in self._visits[since:] if visited == code)

    def get_unvisited(self):
        return [code for code in self._targets if self._hits[code] == 0]

    def _require(self, code):
        # Non-str codes are never stored, so they count as missing too.
        if not isinstance(code, str) or code not in self._targets:
            raise KeyError(code)
