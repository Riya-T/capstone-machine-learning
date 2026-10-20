"""Football season with removable games and current streaks.

Correct solution for football_season after c_streak and c_remove.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from season import Season
    season = Season()
    season.add_team("Bears")
    season.add_team("Lions")
    game_id = season.record_game("Bears", "Lions", 24, 17)
    season.remove_game(game_id)
"""


def check_score(score):
    if not isinstance(score, int) or score < 0:
        raise ValueError(f"a score must be an int >= 0, got {score!r}")


def standings_points(record):
    return 2 * record["wins"] + record["ties"]


def outcome(scored, allowed):
    return "wins" if scored > allowed else "losses" if scored < allowed else "ties"


LETTERS = {"wins": "W", "losses": "L", "ties": "T"}


def empty_record():
    return {"wins": 0, "losses": 0, "ties": 0, "points_for": 0, "points_against": 0}


def streak(letters):
    """ "W3" for three wins in a row at the end, and so on; "" for no games."""
    if not letters:
        return ""
    count = 0
    for letter in reversed(letters):
        if letter != letters[-1]:
            break
        count += 1
    return f"{letters[-1]}{count}"


class Season:
    def __init__(self):
        self._teams = []  # names, in the order they were added
        self._games = {}  # id -> (home, away, home_score, away_score), in id order
        self._next_id = 1

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
        game_id = self._next_id
        self._games[game_id] = (home, away, home_score, away_score)
        self._next_id += 1
        return game_id

    def remove_game(self, game_id):
        self._require_game(game_id)
        del self._games[game_id]

    def get_game(self, game_id):
        self._require_game(game_id)
        home, away, home_score, away_score = self._games[game_id]
        return {"home": home, "away": away, "home_score": home_score, "away_score": away_score}

    def get_record(self, team):
        self._require(team)
        return self._records()[team]

    def get_standings(self):
        return self._rank(self._teams)

    def _rank(self, teams):
        records = self._records()

        # sorted() is stable, so teams still tied keep the order they were added.
        def rank(team):
            r = records[team]
            return (-standings_points(r), -(r["points_for"] - r["points_against"]))

        return sorted(teams, key=rank)

    def _records(self):
        # Worked out from the games on every call, in game order, so the
        # streak always reflects each team's latest games.
        records = {team: empty_record() for team in self._teams}
        results = {team: [] for team in self._teams}  # "W", "L" or "T", oldest first
        for home, away, home_score, away_score in self._games.values():
            for team, scored, allowed in (
                (home, home_score, away_score),
                (away, away_score, home_score),
            ):
                record = records[team]
                record["points_for"] += scored
                record["points_against"] += allowed
                record[outcome(scored, allowed)] += 1
                results[team].append(LETTERS[outcome(scored, allowed)])
        for team, letters in results.items():
            records[team]["streak"] = streak(letters)
        return records

    def _require(self, team):
        if not isinstance(team, str) or team not in self._teams:
            raise KeyError(team)

    def _require_game(self, game_id):
        if not isinstance(game_id, int) or game_id not in self._games:
            raise KeyError(game_id)
