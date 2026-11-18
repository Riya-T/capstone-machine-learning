Let several questions in `quiz.py` be moved to another round in one call,
so that they move together or not at all.

- Add `Quiz.move_questions(questions, to_round) -> int`. `questions` is a
  list of question ids. It moves each question to the end of `to_round`,
  in the list's order, as if `move_question` were called for each one, and
  returns how many questions it moved.
- The questions may come from several rounds. A round that loses all its
  questions stays in use, empty.
- The call succeeds or fails as a whole. Before moving any question it
  checks all of them, and raises without moving any question when:
  - `to_round` is not in use, or a name in the list is not the id of a
    question: `KeyError`;
  - a question in the list is already in `to_round`: `ValueError`;
  - the list names the same question more than once, or is empty:
    `ValueError`.
- When a call has more than one problem, which error is raised is
  unspecified.

All existing behavior must keep working.
