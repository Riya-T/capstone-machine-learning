"""Quiz rounds with undo.

Correct solution for quiz_rounds after c_undo. Never shown to the writer or
the editor; validate-tasks checks that it passes every test it should.

Usage:
    from quiz import Quiz
    quiz = Quiz()
    quiz.add_round("music")
    quiz.add_question("music", "q1")
    quiz.drop_round("music")
    quiz.undo()  # music is back with q1
"""

import copy


class QuizError(Exception):
    pass


class Quiz:
    def __init__(self):
        self._rounds = {}  # round name -> question ids, in order; rounds in the order added
        self._round_of = {}  # question id -> the round it is in
        self._undo_stack = []  # copies of the state as it was before each call

    def add_round(self, name):
        if name in self._rounds:
            raise QuizError(f"round name {name!r} is already used")
        self._save()
        self._rounds[name] = []

    def add_question(self, round_name, question):
        self._require_round(round_name)
        if question in self._round_of:
            raise QuizError(f"question id {question!r} is already used")
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
        self._save()
        self._rounds[self._round_of[question]].remove(question)
        self._rounds[to_round].append(question)
        self._round_of[question] = to_round

    def merge_rounds(self, source, into):
        self._require_round(source)
        self._require_round(into)
        if source == into:
            raise ValueError("cannot merge a round into itself")
        self._save()
        moved = self._rounds.pop(source)
        for question in moved:
            self._round_of[question] = into
        self._rounds[into].extend(moved)
        return len(moved)

    def drop_round(self, name):
        self._require_round(name)
        self._save()
        dropped = self._rounds.pop(name)
        for question in dropped:
            del self._round_of[question]
        return len(dropped)

    def undo(self):
        if not self._undo_stack:
            raise QuizError("nothing to undo")
        self._rounds, self._round_of = self._undo_stack.pop()

    def get_questions(self, round_name):
        self._require_round(round_name)
        return list(self._rounds[round_name])

    def get_rounds(self):
        return list(self._rounds)

    def _save(self):
        # Called by each recorded call once all its checks have passed.
        self._undo_stack.append(copy.deepcopy((self._rounds, self._round_of)))

    def _require_round(self, name):
        if not isinstance(name, str) or name not in self._rounds:
            raise KeyError(name)

    def _require_question(self, question):
        if not isinstance(question, str) or question not in self._round_of:
            raise KeyError(question)
