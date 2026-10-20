"""Football season: records game results and ranks the teams.

Correct solution for football_season before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from season import Season
    season = Season()
    season.add_team("Bears")
    season.add_team("Lions")
    season.record_game("Bears", "Lions", 24, 17)
    season.get_standings()
"""


def check_score(score):
    if not isinstance(score, int) or score < 0:
        raise ValueError(f"a score must be an int >= 0, got {score!r}")


def empty_record():
    return {"wins": 0, "losses": 0, "ties": 0, "points_for": 0, "points_against": 0}


def add_result(record, scored, allowed):
    record["points_for"] += scored
    record["points_against"] += allowed
    if scored > allowed:
        record["wins"] += 1
    elif scored < allowed:
        record["losses"] += 1
    else:
        record["ties"] += 1


def standings_points(record):
    return 2 * record["wins"] + record["ties"]


class Season:
    def __init__(self):
        self._teams = []  # names, in the order they were added
        self._games = []  # (home, away, home_score, away_score); id = index + 1

    def add_team(self, name):
        if not isinstance(name, str) or not name:
            raise ValueError("a team name must be a non-empty str")
        if name in self._teams:
            raise ValueError(f"team {name!r} was already added")
        self._teams.append(name)

    def record_game(self, home, away, home_score, away_score):
        self._require(home)
        self._require(away)
        if home == away:
            raise ValueError("a team cannot play itself")
        check_score(home_score)
        check_score(away_score)
        self._games.append((home, away, home_score, away_score))
        return len(self._games)

    def get_record(self, team):
        self._require(team)
        return self._records()[team]

    def get_standings(self):
        records = self._records()

        # sorted() is stable, so teams still tied keep the order they were added.
        def rank(team):
            r = records[team]
            return (-standings_points(r), -(r["points_for"] - r["points_against"]))

        return sorted(self._teams, key=rank)

    def _records(self):
        # Worked out from the games on every call, so records can never drift
        # out of step with the games.
        records = {team: empty_record() for team in self._teams}
        for home, away, home_score, away_score in self._games:
            add_result(records[home], home_score, away_score)
            add_result(records[away], away_score, home_score)
        return records

    def _require(self, team):
        if not isinstance(team, str) or team not in self._teams:
            raise KeyError(team)
