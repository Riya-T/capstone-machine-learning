"""Tram lines with undo and at most 6 stops per line.

Planted bug (after c_undo and c_line_limit): the limit was added
correctly, but merge_lines, rewritten to count the new stops before adding
them, no longer records itself, so undo skips it and reverses the call
before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from trams import TramNetwork
    network = TramNetwork()
    network.add_line("1")
    network.add_stop("1", "Central")
    network.undo()  # line 1 has no stops again
"""


class TramError(Exception):
    pass


class LineFull(TramError):
    pass


MAX_STOPS = 6


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class TramNetwork:
    def __init__(self):
        # line name -> list of its stops in order; the dict keeps the lines
        # in the order they were added.
        self._lines = {}
        self._undo_stack = []  # copies of the lines as they were before each call

    def add_line(self, name):
        check_name(name, "line name")
        if name in self._lines:
            raise TramError(f"line {name!r} already exists")
        self._save()
        self._lines[name] = []

    def add_stop(self, line, stop):
        stops = self._require(line)
        check_name(stop, "stop")
        if stop in stops:
            raise TramError(f"line {line!r} already has stop {stop!r}")
        if len(stops) >= MAX_STOPS:
            raise LineFull(f"line {line!r} already has {MAX_STOPS} stops")
        self._save()
        stops.append(stop)

    def remove_stop(self, line, stop):
        stops = self._require(line)
        if stop not in stops:
            raise TramError(f"line {line!r} has no stop {stop!r}")
        self._save()
        stops.remove(stop)

    def close_stop(self, stop):
        having = [stops for stops in self._lines.values() if stop in stops]
        if not having:
            raise TramError(f"no line has stop {stop!r}")
        self._save()
        for stops in having:
            stops.remove(stop)
        return len(having)

    def merge_lines(self, first, second):
        first_stops = self._require(first)
        second_stops = self._require(second)
        if first == second:
            raise ValueError("cannot merge a line into itself")
        new_stops = [s for s in second_stops if s not in first_stops]
        if len(first_stops) + len(new_stops) > MAX_STOPS:
            raise LineFull(f"line {first!r} would have more than {MAX_STOPS} stops")
        first_stops.extend(new_stops)
        del self._lines[second]

    def undo(self):
        if not self._undo_stack:
            raise TramError("nothing to undo")
        self._lines = self._undo_stack.pop()

    def get_stops(self, line):
        return list(self._require(line))

    def get_lines(self):
        return list(self._lines)

    def get_lines_through(self, stop):
        return [name for name, stops in self._lines.items() if stop in stops]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(stops) for name, stops in self._lines.items()})

    def _require(self, line):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(line, str) or line not in self._lines:
            raise KeyError(line)
        return self._lines[line]
