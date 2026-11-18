"""Quiz rounds: question ids in ordered rounds.

Planted bug (initial spec): drop_round removes the round but forgets to
free the ids of its questions, so adding one of those ids again raises
QuizError.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from quiz import Quiz
    quiz = Quiz()
    quiz.add_round("music")
    quiz.add_round("sport")
    quiz.add_question("music", "q1")
    quiz.merge_rounds("music", "sport")  # 1
"""


class QuizError(Exception):
    pass


class Quiz:
    def __init__(self):
        self._rounds = {}  # round name -> question ids, in order; rounds in the order added
        self._round_of = {}  # question id -> the round it is in

    def add_round(self, name):
        if name in self._rounds:
            raise QuizError(f"round name {name!r} is already used")
        self._rounds[name] = []

    def add_question(self, round_name, question):
        self._require_round(round_name)
        if question in self._round_of:
            raise QuizError(f"question id {question!r} is already used")
        self._rounds[round_name].append(question)
        self._round_of[question] = round_name

    def remove_question(self, question):
        self._require_question(question)
        self._rounds[self._round_of.pop(question)].remove(question)

    def move_question(self, question, to_round):
        self._require_question(question)
        self._require_round(to_round)
        if self._round_of[question] == to_round:
            raise ValueError(f"{question!r} is already in round {to_round!r}")
        self._rounds[self._round_of[question]].remove(question)
        self._rounds[to_round].append(question)
        self._round_of[question] = to_round

    def merge_rounds(self, source, into):
        self._require_round(source)
        self._require_round(into)
        if source == into:
            raise ValueError("cannot merge a round into itself")
        moved = self._rounds.pop(source)
        for question in moved:
            self._round_of[question] = into
        self._rounds[into].extend(moved)
        return len(moved)

    def drop_round(self, name):
        self._require_round(name)
        dropped = self._rounds.pop(name)
        return len(dropped)

    def get_questions(self, round_name):
        self._require_round(round_name)
        return list(self._rounds[round_name])

    def get_rounds(self):
        return list(self._rounds)

    def _require_round(self, name):
        if not isinstance(name, str) or name not in self._rounds:
            raise KeyError(name)

    def _require_question(self, question):
        if not isinstance(question, str) or question not in self._round_of:
            raise KeyError(question)
