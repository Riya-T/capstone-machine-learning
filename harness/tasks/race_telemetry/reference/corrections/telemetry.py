"""Race telemetry with versioned lap corrections.

Correct solution for race_telemetry after c_lap_corrections.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from telemetry import RaceTelemetry
    tel = RaceTelemetry()
    tel.add_car("red")
    tel.add_race("monza", 3)
    tel.record_lap("monza", "red", 81250)
    tel.correct_lap("monza", "red", 1, 81100, expected_version=2)
"""

POINTS = (10, 6, 4, 3, 2, 1)  # points for 1st, 2nd, ... place


class TelemetryError(Exception):
    pass


class VersionConflict(TelemetryError):
    pass


def check_id(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str")


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class RaceTelemetry:
    def __init__(self):
        self._cars = []  # car ids in the order they were added
        self._races = {}  # race id -> number of laps
        self._versions = {}  # race id -> version, bumped by every lap change
        self._laps = {}  # (race id, car id) -> lap times in recording order

    def add_car(self, car_id):
        check_id(car_id, "car_id")
        if car_id in self._cars:
            raise TelemetryError(f"car {car_id!r} is already entered")
        self._cars.append(car_id)

    def add_race(self, race_id, laps):
        check_id(race_id, "race_id")
        check_positive(laps, "laps")
        if race_id in self._races:
            raise TelemetryError(f"race {race_id!r} already exists")
        self._races[race_id] = laps
        self._versions[race_id] = 1

    def record_lap(self, race_id, car_id, lap_time, expected_version=None):
        self._require_race(race_id)
        self._require_car(car_id)
        check_positive(lap_time, "lap_time")
        self._check_version(race_id, expected_version)
        if self._finished(race_id, car_id):
            raise TelemetryError(f"car {car_id!r} has already finished {race_id!r}")
        self._laps.setdefault((race_id, car_id), []).append(lap_time)
        self._versions[race_id] += 1

    def correct_lap(self, race_id, car_id, lap_number, lap_time, expected_version=None):
        self._require_race(race_id)
        self._require_car(car_id)
        laps = self._laps.get((race_id, car_id), [])
        if (
            isinstance(lap_number, bool)
            or not isinstance(lap_number, int)
            or not 1 <= lap_number <= len(laps)
        ):
            raise ValueError(f"no lap {lap_number!r} recorded for {car_id!r}")
        check_positive(lap_time, "lap_time")
        self._check_version(race_id, expected_version)
        laps[lap_number - 1] = lap_time
        self._versions[race_id] += 1

    def get_version(self, race_id):
        self._require_race(race_id)
        return self._versions[race_id]

    def get_lap_times(self, race_id, car_id):
        self._require_race(race_id)
        self._require_car(car_id)
        return list(self._laps.get((race_id, car_id), []))

    def get_results(self, race_id):
        self._require_race(race_id)
        finished = [c for c in self._cars if self._finished(race_id, c)]
        # sorted() is stable, so equal times keep the order cars were added.
        return sorted(finished, key=lambda c: sum(self._laps[(race_id, c)]))

    def get_points(self, car_id):
        self._require_car(car_id)
        total = 0
        for race_id in self._races:
            results = self.get_results(race_id)
            if car_id in results:
                place = results.index(car_id)
                if place < len(POINTS):
                    total += POINTS[place]
        return total

    def get_cars(self):
        return list(self._cars)

    def _check_version(self, race_id, expected_version):
        if expected_version is not None and expected_version != self._versions[race_id]:
            raise VersionConflict(
                f"race {race_id!r} is at version {self._versions[race_id]}, "
                f"not {expected_version!r}"
            )

    def _finished(self, race_id, car_id):
        return len(self._laps.get((race_id, car_id), [])) >= self._races[race_id]

    def _require_race(self, race_id):
        if not isinstance(race_id, str) or race_id not in self._races:
            raise KeyError(race_id)

    def _require_car(self, car_id):
        if not isinstance(car_id, str) or car_id not in self._cars:
            raise KeyError(car_id)
