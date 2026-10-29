"""Elevator dispatch with cancellable calls, capacities and cars out of service.

Correct solution for elevator_dispatch after c_cancel, c_capacity and c_service.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from elevators import Building
    building = Building(top_floor=9, capacity=6)
    building.add_car("freight", capacity=10)
    building.call("ann", 3, 7)
    building.move_car("freight", 3)
"""

DEFAULT_CAPACITY = 4  # riders per car unless the building or car says otherwise


class ElevatorError(Exception):
    pass


class CarOutOfService(ElevatorError):
    pass


def check_capacity(capacity):
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity < 1:
        raise ValueError(f"capacity must be an int >= 1, got {capacity!r}")


class Building:
    def __init__(self, top_floor, capacity=DEFAULT_CAPACITY):
        if isinstance(top_floor, bool) or not isinstance(top_floor, int) or top_floor < 1:
            raise ValueError(f"top_floor must be an int >= 1, got {top_floor!r}")
        check_capacity(capacity)
        self._top_floor = top_floor
        self._capacity = capacity
        # car id -> {"floor": int, "riders": [ids in boarding order], "capacity": int,
        #            "in_service": bool}
        self._cars = {}
        self._waiting = {floor: [] for floor in range(top_floor + 1)}  # ids in call order
        self._destinations = {}  # passenger id -> destination, for every id ever called
        self._delivered = []
        self._cancelled = []  # ids of cancelled calls, oldest first

    def add_car(self, car_id, capacity=None):
        if not isinstance(car_id, str) or not car_id:
            raise ValueError("car_id must be a non-empty str")
        if capacity is None:
            capacity = self._capacity
        check_capacity(capacity)
        if car_id in self._cars:
            raise ElevatorError(f"car {car_id!r} already exists")
        self._cars[car_id] = {
            "floor": 0,
            "riders": [],
            "capacity": capacity,
            "in_service": True,
        }

    def call(self, passenger_id, floor, destination):
        if not isinstance(passenger_id, str) or not passenger_id:
            raise ValueError("passenger_id must be a non-empty str")
        self._check_floor(floor)
        self._check_floor(destination)
        if floor == destination:
            raise ValueError("floor and destination must differ")
        if passenger_id in self._destinations:
            raise ElevatorError(f"passenger id {passenger_id!r} was already used")
        self._destinations[passenger_id] = destination
        self._waiting[floor].append(passenger_id)

    def move_car(self, car_id, floor):
        car = self._car(car_id)
        self._check_floor(floor)
        if not car["in_service"]:
            raise CarOutOfService(f"car {car_id!r} is out of service")
        car["floor"] = floor
        staying = []
        for passenger_id in car["riders"]:
            if self._destinations[passenger_id] == floor:
                self._delivered.append(passenger_id)
            else:
                staying.append(passenger_id)
        room = car["capacity"] - len(staying)
        queue = self._waiting[floor]
        car["riders"] = staying + queue[:room]
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

    def get_destination(self, passenger_id):
        if passenger_id not in self._destinations:
            raise KeyError(f"no passenger {passenger_id!r}")
        return self._destinations[passenger_id]

    def get_capacity(self, car_id):
        return self._car(car_id)["capacity"]

    def set_capacity(self, car_id, capacity):
        car = self._car(car_id)
        check_capacity(capacity)
        if len(car["riders"]) > capacity:
            raise ElevatorError(f"car {car_id!r} has more than {capacity} riders")
        car["capacity"] = capacity

    def take_out_of_service(self, car_id):
        car = self._car(car_id)
        if car["riders"]:
            raise ElevatorError(f"car {car_id!r} still has riders")
        car["in_service"] = False

    def return_to_service(self, car_id):
        self._car(car_id)["in_service"] = True

    def is_in_service(self, car_id):
        return self._car(car_id)["in_service"]

    def get_cars_in_service(self):
        return [car_id for car_id, car in self._cars.items() if car["in_service"]]

    def cancel_call(self, passenger_id):
        if not isinstance(passenger_id, str) or passenger_id not in self._destinations:
            raise KeyError(passenger_id)
        floor = self._waiting_floor(passenger_id)
        if floor is None:
            raise ElevatorError(f"passenger {passenger_id!r} already got into a car")
        self._waiting[floor].remove(passenger_id)
        del self._destinations[passenger_id]  # the id may be called again
        self._cancelled.append(passenger_id)

    def get_cancelled(self):
        return list(self._cancelled)

    def _waiting_floor(self, passenger_id):
        for floor, queue in self._waiting.items():
            if passenger_id in queue:
                return floor
        return None

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
