Let a person in `crib.py` check out several tools in one call, for example
the set of tools for one job, so that they get either all of them or none.

- Add `ToolCrib.check_out_many(tools, person) -> None`. `tools` is a list of
  tool names. It checks the tools out to `person` in the list's order, as
  if `check_out` were called for each one: each tool leaves its bin, and a
  later `return_all` for the person returns them in the list's order,
  after any tools the person checked out before.
- The call succeeds or fails as a whole. Before checking out any tool it
  checks all of them, and raises without checking out any tool when:
  - a tool in the list is not in any bin (there is no such tool, or it is
    checked out, to anyone): `KeyError`;
  - the list names the same tool more than once, or is empty:
    `ValueError`.
- When a call has more than one problem, which error is raised is
  unspecified.
- Tools checked out with `check_out_many` are like any other checked-out
  tools: `get_holder`, `return_tool` and `return_all` work on them as
  before.

All existing behavior must keep working.
