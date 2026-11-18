"""Tool crib with undo and locked bins.

Correct solution for tool_crib after c_undo and c_lock. Never shown to the
writer or the editor; validate-tasks checks that it passes every test it
should.

Usage:
    from crib import ToolCrib
    crib = ToolCrib()
    crib.add_bin("drills")
    crib.add_tool("drills", "hammer drill")
    crib.lock_bin("drills")
    crib.undo()  # drills is unlocked again
"""

import copy


class CribError(Exception):
    pass


class BinLocked(CribError):
    pass


class ToolCrib:
    def __init__(self):
        self._bins = {}  # bin name -> tools in the bin, in order
        self._held = {}  # checked-out tool -> person, in the order checked out
        self._locked = set()  # names of locked bins
        self._undo_stack = []  # copies of the state as it was before each call

    def add_bin(self, name):
        if name in self._bins:
            raise CribError(f"bin name {name!r} is already used")
        self._save()
        self._bins[name] = []

    def add_tool(self, bin_name, tool):
        self._require_bin(bin_name)
        self._require_unlocked(bin_name)
        self._save()
        self._bins[bin_name].append(tool)

    def check_out(self, tool, person):
        bin_name = self._bin_of(tool)
        self._require_unlocked(bin_name)
        self._save()
        self._bins[bin_name].remove(tool)
        self._held[tool] = person

    def return_tool(self, tool, bin_name):
        self._require_bin(bin_name)
        if tool not in self._held:
            raise KeyError(tool)
        self._require_unlocked(bin_name)
        self._save()
        del self._held[tool]
        self._bins[bin_name].append(tool)

    def return_all(self, person, bin_name):
        self._require_bin(bin_name)
        self._require_unlocked(bin_name)
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
        self._require_unlocked(name)
        self._require_unlocked(into)
        self._save()
        moved = self._bins.pop(name)
        self._bins[into].extend(moved)
        return len(moved)

    def lock_bin(self, name):
        self._require_bin(name)
        if name in self._locked:
            raise CribError(f"bin {name!r} is already locked")
        self._save()
        self._locked.add(name)

    def unlock_bin(self, name):
        self._require_bin(name)
        if name not in self._locked:
            raise CribError(f"bin {name!r} is not locked")
        self._save()
        self._locked.discard(name)

    def undo(self):
        if not self._undo_stack:
            raise CribError("nothing to undo")
        self._bins, self._held, self._locked = self._undo_stack.pop()

    def get_tools(self, bin_name):
        self._require_bin(bin_name)
        return list(self._bins[bin_name])

    def get_holder(self, tool):
        return self._held.get(tool)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append(copy.deepcopy((self._bins, self._held, self._locked)))

    def _bin_of(self, tool):
        for name, tools in self._bins.items():
            if tool in tools:
                return name
        raise KeyError(tool)

    def _require_bin(self, name):
        if not isinstance(name, str) or name not in self._bins:
            raise KeyError(name)

    def _require_unlocked(self, name):
        if name in self._locked:
            raise BinLocked(f"bin {name!r} is locked")
