"""Race telemetry with adjustable points tables and time penalties.

Correct solution for race_telemetry after c_points_table and c_penalties.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from telemetry import RaceTelemetry
    tel = RaceTelemetry(points_table=(25, 18, 15))
    tel.add_car("red")
    tel.add_race("finale", 3, points_table=[50, 36, 30])
    tel.record_lap("finale", "red", 81250)
    tel.add_penalty("finale", "red", 5000)
"""

DEFAULT_POINTS = (10, 6, 4, 3, 2, 1)  # points for 1st, 2nd, ... place


class TelemetryError(Exception):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_table(table):
    if not isinstance(table, (list, tuple)):
        raise ValueError(f"points table must be a list or tuple, got {table!r}")
    for points in table:
        if isinstance(points, bool) or not isinstance(points, int) or points < 0:
            raise ValueError(f"points must be ints >= 0, got {points!r}")
    return list(table)


class RaceTelemetry:
    def __init__(self, points_table=DEFAULT_POINTS):
        self._table = check_table(points_table)  # the series table
        self._cars = []  # car ids in the order they were added
        self._races = {}  # race id -> number of laps
        self._race_tables = {}  # race id -> its own table, or None for the series table
        self._laps = {}  # (race id, car id) -> lap times in recording order
        self._penalties = {}  # (race id, car id) -> sum of penalties in ms

    def add_car(self, car_id):
        check_id(car_id, "car_id")
        if car_id in self._cars:
            raise TelemetryError(f"car {car_id!r} is already entered")
        self._cars.append(car_id)

    def add_race(self, race_id, laps, points_table=None):
        check_id(race_id, "race_id")
        check_positive(laps, "laps")
        table = None if points_table is None else check_table(points_table)
        if race_id in self._races:
            raise TelemetryError(f"race {race_id!r} already exists")
        self._races[race_id] = laps
        self._race_tables[race_id] = table

    def set_points_table(self, points_table):
        self._table = check_table(points_table)

    def get_points_table(self, race_id=None):
        if race_id is None:
            return list(self._table)
        self._require_race(race_id)
        return list(self._table_for(race_id))

    def record_lap(self, race_id, car_id, lap_time):
        self._require_race(race_id)
        self._require_car(car_id)
        check_positive(lap_time, "lap_time")
        if self._finished(race_id, car_id):
            raise TelemetryError(f"car {car_id!r} has already finished {race_id!r}")
        self._laps.setdefault((race_id, car_id), []).append(lap_time)

    def get_lap_times(self, race_id, car_id):
        self._require_race(race_id)
        self._require_car(car_id)
        return list(self._laps.get((race_id, car_id), []))

    def add_penalty(self, race_id, car_id, penalty):
        self._require_race(race_id)
        self._require_car(car_id)
        check_positive(penalty, "penalty")
        key = (race_id, car_id)
        self._penalties[key] = self._penalties.get(key, 0) + penalty

    def get_penalty(self, race_id, car_id):
        self._require_race(race_id)
        self._require_car(car_id)
        return self._penalties.get((race_id, car_id), 0)

    def get_total_time(self, race_id, car_id):
        self._require_race(race_id)
        self._require_car(car_id)
        return self._total(race_id, car_id)

    def get_results(self, race_id):
        self._require_race(race_id)
        finished = [c for c in self._cars if self._finished(race_id, c)]
        # sorted() is stable, so equal times keep the order cars were added.
        return sorted(finished, key=lambda c: self._total(race_id, c))

    def get_points(self, car_id):
        self._require_car(car_id)
        total = 0
        for race_id in self._races:
            results = self.get_results(race_id)
            if car_id in results:
                total += self._score(race_id, results.index(car_id))
        return total

    def get_cars(self):
        return list(self._cars)

    def _table_for(self, race_id):
        own = self._race_tables[race_id]
        return self._table if own is None else own

    def _score(self, race_id, place):
        table = self._table_for(race_id)
        return table[place] if place < len(table) else 0

    def _total(self, race_id, car_id):
        key = (race_id, car_id)
        return sum(self._laps.get(key, [])) + self._penalties.get(key, 0)

    def _finished(self, race_id, car_id):
        return len(self._laps.get((race_id, car_id), [])) >= self._races[race_id]

    def _require_race(self, race_id):
        if not isinstance(race_id, str) or race_id not in self._races:
            raise KeyError(race_id)

    def _require_car(self, car_id):
        if not isinstance(car_id, str) or car_id not in self._cars:
            raise KeyError(car_id)
