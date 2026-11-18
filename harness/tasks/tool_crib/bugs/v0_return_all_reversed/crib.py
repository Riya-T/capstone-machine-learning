"""Tool crib: tools in ordered bins, checked out to people and returned.

Planted bug (initial spec): return_all walks the person's tools from the
last checked out to the first, so the bin gets them in reverse order.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from crib import ToolCrib
    crib = ToolCrib()
    crib.add_bin("drills")
    crib.add_tool("drills", "hammer drill")
    crib.check_out("hammer drill", "ann")
    crib.return_all("ann", "drills")  # 1
"""


class CribError(Exception):
    pass


class ToolCrib:
    def __init__(self):
        self._bins = {}  # bin name -> tools in the bin, in order
        self._held = {}  # checked-out tool -> person, in the order checked out

    def add_bin(self, name):
        if name in self._bins:
            raise CribError(f"bin name {name!r} is already used")
        self._bins[name] = []

    def add_tool(self, bin_name, tool):
        self._require_bin(bin_name)
        self._bins[bin_name].append(tool)

    def check_out(self, tool, person):
        self._bins[self._bin_of(tool)].remove(tool)
        self._held[tool] = person

    def return_tool(self, tool, bin_name):
        self._require_bin(bin_name)
        if tool not in self._held:
            raise KeyError(tool)
        del self._held[tool]
        self._bins[bin_name].append(tool)

    def return_all(self, person, bin_name):
        self._require_bin(bin_name)
        tools = [tool for tool, holder in self._held.items() if holder == person]
        for tool in reversed(tools):
            del self._held[tool]
            self._bins[bin_name].append(tool)
        return len(tools)

    def close_bin(self, name, into):
        self._require_bin(name)
        self._require_bin(into)
        if name == into:
            raise ValueError("cannot close a bin into itself")
        moved = self._bins.pop(name)
        self._bins[into].extend(moved)
        return len(moved)

    def get_tools(self, bin_name):
        self._require_bin(bin_name)
        return list(self._bins[bin_name])

    def get_holder(self, tool):
        return self._held.get(tool)

    def _bin_of(self, tool):
        for name, tools in self._bins.items():
            if tool in tools:
                return name
        raise KeyError(tool)

    def _require_bin(self, name):
        if not isinstance(name, str) or name not in self._bins:
            raise KeyError(name)
