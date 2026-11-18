"""Quiz rounds with undo and round limits.

Planted bug (after c_undo and c_limit): round limits were added correctly,
but drop_round, rewritten to also forget the round's limit, no longer
records itself, so undo skips it and reverses the call before it instead.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from quiz import Quiz
    quiz = Quiz()
    quiz.add_round("music")
    quiz.set_limit("music", 10)
    quiz.add_question("music", "q1")
    quiz.undo()  # music is empty again, still with limit 10
"""

import copy


class QuizError(Exception):
    pass


class RoundFull(QuizError):
    pass


class Quiz:
    def __init__(self):
        self._rounds = {}  # round name -> question ids, in order; rounds in the order added
        self._round_of = {}  # question id -> the round it is in
        self._limits = {}  # round name -> limit; missing = no limit
        self._undo_stack = []  # copies of the state as it was before each call

    def add_round(self, name):
        if name in self._rounds:
            raise QuizError(f"round name {name!r} is already used")
        self._save()
        self._rounds[name] = []
        self._limits.pop(name, None)  # the name may have been used before

    def add_question(self, round_name, question):
        self._require_round(round_name)
        if question in self._round_of:
            raise QuizError(f"question id {question!r} is already used")
        self._require_room(round_name, 1)
        self._save()
        self._rounds[round_name].append(question)
        self._round_of[question] = round_name

    def remove_question(self, question):
        self._require_question(question)
        self._save()
        self._rounds[self._round_of.pop(question)].remove(question)

    def move_question(self, question, to_round):
        self._require_question(question)
        self._require_round(to_round)
        if self._round_of[question] == to_round:
            raise ValueError(f"{question!r} is already in round {to_round!r}")
        self._require_room(to_round, 1)
        self._save()
        self._rounds[self._round_of[question]].remove(question)
        self._rounds[to_round].append(question)
        self._round_of[question] = to_round

    def merge_rounds(self, source, into):
        self._require_round(source)
        self._require_round(into)
        if source == into:
            raise ValueError("cannot merge a round into itself")
        self._require_room(into, len(self._rounds[source]))
        self._save()
        moved = self._rounds.pop(source)
        self._limits.pop(source, None)
        for question in moved:
            self._round_of[question] = into
        self._rounds[into].extend(moved)
        return len(moved)

    def drop_round(self, name):
        self._require_round(name)
        dropped = self._rounds.pop(name)
        self._limits.pop(name, None)
        for question in dropped:
            del self._round_of[question]
        return len(dropped)

    def set_limit(self, round_name, limit):
        self._require_round(round_name)
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0):
            raise ValueError(f"limit must be None or a positive int, got {limit!r}")
        self._save()
        if limit is None:
            self._limits.pop(round_name, None)
        else:
            self._limits[round_name] = limit

    def get_limit(self, round_name):
        self._require_round(round_name)
        return self._limits.get(round_name)

    def undo(self):
        if not self._undo_stack:
            raise QuizError("nothing to undo")
        self._rounds, self._round_of, self._limits = self._undo_stack.pop()

    def get_questions(self, round_name):
        self._require_round(round_name)
        return list(self._rounds[round_name])

    def get_rounds(self):
        return list(self._rounds)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        state = (self._rounds, self._round_of, self._limits)
        self._undo_stack.append(copy.deepcopy(state))

    def _require_round(self, name):
        if not isinstance(name, str) or name not in self._rounds:
            raise KeyError(name)

    def _require_question(self, question):
        if not isinstance(question, str) or question not in self._round_of:
            raise KeyError(question)

    def _require_room(self, round_name, adding):
        limit = self._limits.get(round_name)
        if limit is not None and len(self._rounds[round_name]) + adding > limit:
            raise RoundFull(f"round {round_name!r} has room for fewer than {adding} more questions")
