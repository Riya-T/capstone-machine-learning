Let each round in `quiz.py` have a limit on how many questions it holds,
so that no round runs too long.

- Add `Quiz.set_limit(round_name, limit) -> None` and
  `Quiz.get_limit(round_name) -> int | None`. Both raise `KeyError` for a
  round that is not in use.
- `limit` is either `None`, meaning no limit, or an `int` greater than 0.
  Anything else (such as 0 or a negative number) raises `ValueError` and
  changes nothing. Each call replaces the round's earlier limit.
- Every new round has limit `None`, including a round added again under
  the name of one that was merged away or dropped: it does not keep the
  old round's limit.
- Add `class RoundFull(QuizError)` to `quiz.py`.
- Every call that puts questions into a round checks the receiving round:
  `add_question`, the `to_round` of `move_question`, and the `into` round of
  `merge_rounds`. If that round would then hold more questions than its
  limit, the call raises `RoundFull` and changes nothing: `merge_rounds`
  moves no question and keeps round `source`. Filling a round exactly to
  its limit is allowed.
- A limit below the number of questions a round already holds is allowed:
  the questions stay and can be removed or moved away as before, and every
  call that would put more questions into the round raises `RoundFull`.
- `remove_question` and `drop_round` never check a limit, and the limit of
  the round questions leave is never checked.
- When a call has another problem as well, which error is raised is
  unspecified.
- Every successful `set_limit` changes the quiz, so `undo` reverses it like
  every other such call: an undone `set_limit` gives the round back the
  limit it had before. `undo` still puts everything back exactly as it was
  before the call it reverses; an undone `merge_rounds` or `drop_round`
  brings the round back with its limit too.

All existing behavior must keep working.
