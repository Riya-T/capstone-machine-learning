Show each team's current streak in `season.py`.

- `get_record` returns a new key `streak`: a `str` made of a letter and a
  count that describes the team's latest games, in the order they were
  recorded. `"W3"` means the team won its last three games and did not win
  the game before those; `"L1"` means it lost its last game after a win or a
  tie; `"T2"` means it tied its last two games. Home and away games both
  count.
- A team that has not played yet has the streak `""`.

All existing behavior must keep working.
