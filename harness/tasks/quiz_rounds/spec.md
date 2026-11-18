# Quiz rounds

Write a module `quiz.py` that keeps track of the questions of a pub quiz:
which questions are in which round and in what order, as questions are
added, removed and moved, and rounds are merged or dropped.

## Interface

```python
class QuizError(Exception): ...


class Quiz:
    def __init__(self): ...
    def add_round(self, name: str) -> None: ...
    def add_question(self, round_name: str, question: str) -> None: ...
    def remove_question(self, question: str) -> None: ...
    def move_question(self, question: str, to_round: str) -> None: ...
    def merge_rounds(self, source: str, into: str) -> int: ...
    def drop_round(self, name: str) -> int: ...
    def get_questions(self, round_name: str) -> list[str]: ...
    def get_rounds(self) -> list[str]: ...
```

Round names and question ids are non-empty strings.

## Rounds

- `add_round(name)` adds an empty round. A name that is already in use
  raises `QuizError`.
- `get_rounds()` returns the names of the rounds in use, in the order they
  were added.
- Every other method that takes a round name raises `KeyError` when the
  round is not in use: it was never added, or it was merged into another
  round or dropped.

## Questions

- Each question is known by its id. Ids are unique in the whole quiz: no
  test adds an id that a question already has.
- `add_question(round_name, question)` adds the question at the end of the
  round.
- `get_questions(round_name)` returns the ids of the round's questions, in
  their order in the round.
- `remove_question(question)` removes the question from its round. Its id
  is then free and may be added again.
- `move_question(question, to_round)` takes the question out of its round
  and puts it at the end of `to_round`, which is always another round than
  the one the question is in.
- `remove_question` and `move_question` raise `KeyError` for an id that no
  question has.

## Merging and dropping rounds

- `merge_rounds(source, into)` moves every question of round `source` to the
  end of round `into`, keeping their order, and then removes round
  `source`. It returns how many questions it moved (0 if `source` was
  empty). It raises `ValueError` when both rounds are the same. Unlike
  `drop_round`, it removes no question: the moved questions are now
  questions of round `into`.
- `drop_round(name)` removes the round together with all its questions; the
  ids of those questions are then free. It returns how many questions it
  removed (0 if the round was empty).
- A round that was merged away or dropped is no longer listed by
  `get_rounds()`, and every method treats it as not in use. Its name is
  then free: `add_round` may add it again later, as a new empty round at
  the end of `get_rounds()`.

Python note: a `list` must not lose items while a `for` loop runs over it
(the loop silently skips items). For example, if `merge_rounds` calls
`move_question` inside `for question in questions:`, loop over a copy
instead: `for question in list(questions):`. Also, when a `dict` maps
round names to lists of ids, `question in rounds.values()` compares the id
with each whole list and is always `False`; check each list instead, such
as `any(question in ids for ids in rounds.values())`.

## Errors

A failed call has no effect: if a method raises, the list of rounds and the
questions of every round are unchanged.

When a call has more than one problem, which of the errors is raised is
unspecified.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes values of the wrong type (round names or ids that are not
non-empty strings, such as `""`, `None` or `1`), adding an id that a
question already has, moving a question to the round it is already in,
what `remove_question` and `move_question` do with a question that
`merge_rounds` moved, which error is raised when a call has more than one
problem, what happens if a returned list is changed, the text of error
messages, saving the quiz to a file, and use from several threads.
