"""Elevator dispatch: cars, passengers waiting on floors and riders in cars.

Planted bug (initial version): get_delivered lists only the passengers who
got out at the last stop where anybody got out, because each stop replaces
the list instead of adding to it. The public checks never let passengers
arrive at two different stops.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from elevators import Building
    building = Building(top_floor=9)
    building.add_car("east")
    building.call("ann", 3)
    building.move_car("east", 3)
"""

CAPACITY = 4  # riders per car


class ElevatorError(Exception):
    pass


class Building:
    def __init__(self, top_floor):
        if isinstance(top_floor, bool) or not isinstance(top_floor, int) or top_floor < 1:
            raise ValueError(f"top_floor must be an int >= 1, got {top_floor!r}")
        self._top_floor = top_floor
        self._cars = {}  # car id -> {"floor": int, "riders": [ids in boarding order]}
        self._waiting = {floor: [] for floor in range(top_floor + 1)}  # ids in call order
        self._delivered = []

    def add_car(self, car_id):
        if not isinstance(car_id, str) or not car_id:
            raise ValueError("car_id must be a non-empty str")
        if car_id in self._cars:
            raise ElevatorError(f"car {car_id!r} already exists")
        self._cars[car_id] = {"floor": 0, "riders": []}

    def call(self, passenger_id, floor):
        if not isinstance(passenger_id, str) or not passenger_id:
            raise ValueError("passenger_id must be a non-empty str")
        self._check_floor(floor)
        self._waiting[floor].append(passenger_id)

    def move_car(self, car_id, floor):
        car = self._car(car_id)
        self._check_floor(floor)
        car["floor"] = floor
        if car["riders"]:
            self._delivered = list(car["riders"])  # every rider gets out here
        room = CAPACITY
        queue = self._waiting[floor]
        car["riders"] = queue[:room]
        self._waiting[floor] = queue[room:]

    def get_car_floor(self, car_id):
        return self._car(car_id)["floor"]

    def get_riders(self, car_id):
        return list(self._car(car_id)["riders"])

    def get_waiting(self, floor):
        self._check_floor(floor)
        return list(self._waiting[floor])

    def get_delivered(self):
        return list(self._delivered)

    def _car(self, car_id):
        # Non-str ids are never stored, so they count as "not a car" too.
        if not isinstance(car_id, str) or car_id not in self._cars:
            raise KeyError(car_id)
        return self._cars[car_id]

    def _check_floor(self, floor):
        if (
            isinstance(floor, bool)
            or not isinstance(floor, int)
            or not 0 <= floor <= self._top_floor
        ):
            raise ValueError(f"floor must be an int from 0 to {self._top_floor}, got {floor!r}")
