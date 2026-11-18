# Tool crib

Write a module `crib.py` that keeps track of the tools in a workshop's tool
crib: which tools are stored in which bin and in what order, and which
tools are checked out to which person.

## Interface

```python
class CribError(Exception): ...


class ToolCrib:
    def __init__(self): ...
    def add_bin(self, name: str) -> None: ...
    def add_tool(self, bin_name: str, tool: str) -> None: ...
    def check_out(self, tool: str, person: str) -> None: ...
    def return_tool(self, tool: str, bin_name: str) -> None: ...
    def return_all(self, person: str, bin_name: str) -> int: ...
    def close_bin(self, name: str, into: str) -> int: ...
    def get_tools(self, bin_name: str) -> list[str]: ...
    def get_holder(self, tool: str) -> str | None: ...
```

Bin names, tool names and people are non-empty strings.

## Bins

- `add_bin(name)` adds an empty bin. A name that is already in use raises
  `CribError`.
- Every other method that takes a bin name raises `KeyError` when the bin
  is not in use: it was never added, or it was closed.
- `get_tools(bin_name)` returns the names of the tools that are in the bin
  right now, in their order in the bin.

## Tools

- `add_tool(bin_name, tool)` adds a new tool at the end of the bin. Tool
  names are unique: no test adds a name that a tool already has.
- `check_out(tool, person)` takes the tool out of the bin it is in and
  gives it to `person`. People do not need to be added first. It raises
  `KeyError` when the tool is not in any bin: there is no such tool, or it
  is checked out.
- `get_holder(tool)` returns the person who has the tool checked out, or
  `None` when the tool is in a bin.
- `return_tool(tool, bin_name)` takes the tool back from the person who has
  it and puts it at the end of bin `bin_name`, which may be any bin in use.
  It raises `KeyError` when the tool is not checked out.
- `return_all(person, bin_name)` returns every tool that `person` has to
  the end of bin `bin_name`, in the order they were checked out, and
  returns how many tools it returned.

## Closing a bin

- `close_bin(name, into)` moves every tool in bin `name` to the end of bin
  `into`, keeping their order, and then closes bin `name`. It returns how
  many tools it moved (0 if the bin was empty). Checked-out tools are in no
  bin, so closing a bin does not change them.
- A closed bin is gone: every method treats it as not in use. Its name is
  then free: `add_bin` may add it again later, as a new empty bin.
- `close_bin` raises `ValueError` when both bins are the same.

Python notes: a `dict` must not gain or lose keys while a `for` loop runs
over it (Python raises `RuntimeError`), and a `list` must not lose items
while a `for` loop runs over it (the loop skips items); loop over a copy,
such as `list(holders.items())`, when the loop removes entries. Also, when
a `dict` maps names to lists, `tool in d.values()` compares the tool with
each whole list and is always `False`; check each list instead, such as
`any(tool in tools for tools in d.values())`.

## Errors

A failed call has no effect: if a method raises, the tools in every bin and
the holder of every tool are unchanged.

When a call has more than one problem, which of the errors is raised is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type (names that are not non-empty strings,
such as `""`, `None` or `1`), adding a tool name that a tool already has,
`get_holder` of a name that no tool has, `return_all` for a person who has
no tools, which error is raised when a call has more than one problem, what
happens if a returned list is changed, the text of error messages, saving
the crib to a file, and use from several threads.
