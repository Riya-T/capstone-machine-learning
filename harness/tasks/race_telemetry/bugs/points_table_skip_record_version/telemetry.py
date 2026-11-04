"""Race telemetry: one race, its cars, lap times, and the results with points.

Planted bug in race_telemetry after c_lap_corrections and c_points_table.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it. The bug: record_lap no longer counts toward the version.

Usage:
    from telemetry import RaceTelemetry
    tel = RaceTelemetry(3)
    tel.add_car("red")
    tel.record_lap("red", 81250)
"""



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


def check_table(table):
    if not isinstance(table, (list, tuple)) or not all(
        isinstance(p, int) and not isinstance(p, bool) and p >= 0 for p in table
    ):
        raise ValueError(f"invalid points table {table!r}")
    return list(table)


class RaceTelemetry:
    def __init__(self, laps, points_table=(10, 6, 4, 3, 2, 1)):
        check_positive(laps, "laps")
        self._table = check_table(points_table)  # points for 1st, 2nd, ... place
        self._laps = laps  # laps a car must drive to finish
        self._cars = []  # car ids in the order they were added
        self._times = {}  # car id -> lap times in recording order
        self._version = 1

    def add_car(self, car_id):
        check_id(car_id, "car_id")
        if car_id in self._times:
            raise TelemetryError(f"car {car_id!r} is already entered")
        self._cars.append(car_id)
        self._times[car_id] = []

    def get_cars(self):
        return list(self._cars)

    def record_lap(self, car_id, lap_time, expected_version=None):
        self._require_car(car_id)
        check_positive(lap_time, "lap_time")
        if self._finished(car_id):
            raise TelemetryError(f"car {car_id!r} has already finished")
        self._check_version(expected_version)
        self._times[car_id].append(lap_time)

    def get_lap_times(self, car_id):
        self._require_car(car_id)
        return list(self._times[car_id])

    def get_results(self):
        finished = [c for c in self._cars if self._finished(c)]
        # sorted() is stable, so equal times keep the order cars were added.
        order = sorted(finished, key=self._total)
        table = self._table
        return [(c, table[i] if i < len(table) else 0) for i, c in enumerate(order)]

    def set_points_table(self, points_table):
        self._table = check_table(points_table)

    def get_points_table(self):
        return list(self._table)

    def get_version(self):
        return self._version

    def correct_lap(self, car_id, lap_number, lap_time, expected_version=None):
        self._require_car(car_id)
        times = self._times[car_id]
        if isinstance(lap_number, bool) or not isinstance(lap_number, int) or not 1 <= lap_number <= len(times):
            raise ValueError(f"car {car_id!r} has no lap {lap_number!r}")
        check_positive(lap_time, "lap_time")
        self._check_version(expected_version)
        times[lap_number - 1] = lap_time
        self._version += 1

    def _check_version(self, expected_version):
        if expected_version is not None and expected_version != self._version:
            raise VersionConflict(f"the race is at version {self._version}, not {expected_version}")

    def _total(self, car_id):
        return sum(self._times[car_id])

    def _finished(self, car_id):
        return len(self._times[car_id]) >= self._laps

    def _require_car(self, car_id):
        if not isinstance(car_id, str) or car_id not in self._times:
            raise KeyError(car_id)
