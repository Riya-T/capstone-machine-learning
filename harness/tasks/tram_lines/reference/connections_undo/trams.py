"""Tram lines with queries for connections and shared stops, and undo.

Correct solution for tram_lines after c_connections and c_undo.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from trams import TramNetwork
    network = TramNetwork()
    network.add_line("1")
    network.add_stop("1", "Central")
    network.undo()  # line 1 has no stops again
"""


class TramError(Exception):
    pass


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
        self._save()
        first_stops.extend([s for s in second_stops if s not in first_stops])
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

    def get_connections(self, line):
        stops = self._require(line)
        return [
            name
            for name, other in self._lines.items()
            if name != line and any(stop in other for stop in stops)
        ]

    def get_shared_stops(self, first, second):
        first_stops = self._require(first)
        second_stops = self._require(second)
        if first == second:
            raise ValueError("pass two different lines")
        return [stop for stop in first_stops if stop in second_stops]

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append({name: list(stops) for name, stops in self._lines.items()})

    def _require(self, line):
        # Non-str names are never stored, so they count as "not in use" too.
        if not isinstance(line, str) or line not in self._lines:
            raise KeyError(line)
        return self._lines[line]
