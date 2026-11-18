Add a way to install a batch of servers into a rack in one call that
succeeds or fails as a whole, so that a delivery is never left half
installed.

- Add `Racks.install_many(rack, servers) -> int`. `servers` is a list of
  server names. They are installed at the end of the rack in list order,
  as one call, and `install_many` returns how many servers it installed.
  An empty list installs nothing and returns 0.
- It raises `KeyError` when the rack is not in use, and `RackError` when
  any name in the list is already installed (in any rack) or appears more
  than once in the list.
- If it raises, no server of the list is installed, not even the ones
  before the problem.
- When a call has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
