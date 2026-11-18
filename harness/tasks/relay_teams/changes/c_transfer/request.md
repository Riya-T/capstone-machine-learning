Let `relay.py` move several runners into one team in a single call, for
example when a coach rebuilds a lineup.

- Add `RelayMeet.move_runners(runners, team) -> int`. `runners` is a list
  of runner names. Each runner is taken out of their team and added at the
  end of `team`'s lineup, in list order, just as `move_runner` would do. It
  returns how many runners it moved.
- Every runner follows the rules of `move_runner`: `team` must be in use
  (otherwise `KeyError`), every runner must be in a team (otherwise
  `KeyError`), and no runner may already be in `team` (otherwise
  `ValueError`).
- The call succeeds or fails as a whole: if any runner breaks a rule,
  `move_runners` raises that error and changes nothing. The runners before
  it in the list do not move either: every lineup is left as it was before
  the call. When several runners break rules, which error is raised is
  unspecified, and so is a list that names the same runner twice.
- The runners may come from different teams. Each of their old teams keeps
  its other runners in order.

All existing behavior must keep working.
