"""Tool crib with checking out several tools in one call, and undo.

Correct solution for tool_crib after c_many and c_undo. Never shown to the
writer or the editor; validate-tasks checks that it passes every test it
should.

Usage:
    from crib import ToolCrib
    crib = ToolCrib()
    crib.add_bin("drills")
    crib.add_tool("drills", "hammer drill")
    crib.add_tool("drills", "drill press")
    crib.check_out_many(["drill press", "hammer drill"], "ann")
    crib.undo()  # both drills are back in their old places
"""

import copy


class CribError(Exception):
    pass


class ToolCrib:
    def __init__(self):
        self._bins = {}  # bin name -> tools in the bin, in order
        self._held = {}  # checked-out tool -> person, in the order checked out
        self._undo_stack = []  # copies of the state as it was before each call

    def add_bin(self, name):
        if name in self._bins:
            raise CribError(f"bin name {name!r} is already used")
        self._save()
        self._bins[name] = []

    def add_tool(self, bin_name, tool):
        self._require_bin(bin_name)
        self._save()
        self._bins[bin_name].append(tool)

    def check_out(self, tool, person):
        bin_name = self._bin_of(tool)
        self._save()
        self._bins[bin_name].remove(tool)
        self._held[tool] = person

    def check_out_many(self, tools, person):
        if not isinstance(tools, list) or not tools:
            raise ValueError("tools must be a non-empty list")
        if len(set(tools)) != len(tools):
            raise ValueError("a tool is named more than once")
        bins = [self._bin_of(tool) for tool in tools]
        self._save()
        for tool, bin_name in zip(tools, bins):
            self._bins[bin_name].remove(tool)
            self._held[tool] = person

    def return_tool(self, tool, bin_name):
        self._require_bin(bin_name)
        if tool not in self._held:
            raise KeyError(tool)
        self._save()
        del self._held[tool]
        self._bins[bin_name].append(tool)

    def return_all(self, person, bin_name):
        self._require_bin(bin_name)
        self._save()
        tools = [tool for tool, holder in self._held.items() if holder == person]
        for tool in tools:
            del self._held[tool]
            self._bins[bin_name].append(tool)
        return len(tools)

    def close_bin(self, name, into):
        self._require_bin(name)
        self._require_bin(into)
        if name == into:
            raise ValueError("cannot close a bin into itself")
        self._save()
        moved = self._bins.pop(name)
        self._bins[into].extend(moved)
        return len(moved)

    def undo(self):
        if not self._undo_stack:
            raise CribError("nothing to undo")
        self._bins, self._held = self._undo_stack.pop()

    def get_tools(self, bin_name):
        self._require_bin(bin_name)
        return list(self._bins[bin_name])

    def get_holder(self, tool):
        return self._held.get(tool)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append(copy.deepcopy((self._bins, self._held)))

    def _bin_of(self, tool):
        for name, tools in self._bins.items():
            if tool in tools:
                return name
        raise KeyError(tool)

    def _require_bin(self, name):
        if not isinstance(name, str) or name not in self._bins:
            raise KeyError(name)
