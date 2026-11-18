Add an undo to `quiz.py`, so a mistake while putting the quiz together can
be taken back.

- Add `Quiz.undo() -> None`. It reverses the most recent successful call
  that has not been undone yet among `add_round`, `add_question`,
  `remove_question`, `move_question`, `merge_rounds` and `drop_round`, and
  any method added later that changes the quiz. Each further `undo` goes
  one call further back.
- Undoing a call puts the list of rounds in its order, and the questions of
  every round in their order, back to what they were just before that
  call. A call that changed several rounds or questions is undone as a
  whole by one `undo`:
  - an undone `remove_question` puts the question back at its old position
    in its round, not at the end; its id is in use again;
  - an undone `move_question` puts the question back at its old position in
    the round it came from;
  - an undone `merge_rounds` brings round `source` back at its old position
    in `get_rounds()` with its questions in their order, and takes those
    questions off the end of `into`;
  - an undone `drop_round` brings the round back at its old position in
    `get_rounds()`, with all its questions in their order; their ids are in
    use again;
  - an undone `add_round` or `add_question` removes the round or question,
    and its name or id may then be added again.
- Calls that raised are not recorded, so `undo` skips them. Calls to any
  other method (the `get_` methods, and `undo` itself) are not recorded
  either and are never undone. There is no redo.
- With nothing left to undo, `undo` raises `QuizError` and changes nothing.

All existing behavior must keep working.
