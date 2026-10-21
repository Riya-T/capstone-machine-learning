"""Rover fleet: rovers on a wrapping 10 by 10 plateau, driven by command
strings and stopped before they run into each other.

Planted bug (initial version): a blocked move is skipped, but the rest of
the string is still carried out. The public checks only block the last
command of a string, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from rovers import RoverFleet
    fleet = RoverFleet()
    fleet.land("scout", 0, 0, "north")
    fleet.drive("scout", "FFRF")
"""

SIZE = 10  # the plateau is SIZE by SIZE cells
FACINGS = ["north", "east", "south", "west"]  # clockwise order
STEPS = {"north": (0, 1), "east": (1, 0), "south": (0, -1), "west": (-1, 0)}
COMMANDS = set("FBLR")


class RoverError(Exception):
    pass


def check_cell(x, y):
    for value in (x, y):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < SIZE:
            raise ValueError(f"cell coordinates must be ints from 0 to {SIZE - 1}")


def check_commands(commands):
    if not isinstance(commands, str) or not set(commands) <= COMMANDS:
        raise ValueError(f"invalid commands {commands!r}")


class RoverFleet:
    def __init__(self):
        # rover id -> {"x", "y", "facing", "odometer"}, in landing order
        self._rovers = {}

    def land(self, rover_id, x, y, facing):
        if not isinstance(rover_id, str) or not rover_id:
            raise ValueError("rover_id must be a non-empty str")
        if rover_id in self._rovers:
            raise RoverError(f"rover {rover_id!r} has already landed")
        check_cell(x, y)
        if facing not in FACINGS:
            raise ValueError(f"facing must be one of {FACINGS}, got {facing!r}")
        if self._occupant(x, y) is not None:
            raise RoverError(f"cell {(x, y)} is taken")
        self._rovers[rover_id] = {"x": x, "y": y, "facing": facing, "odometer": 0}

    def drive(self, rover_id, commands):
        rover = self._require(rover_id)
        check_commands(commands)
        done = 0
        for command in commands:
            if command in "LR":
                turn = 1 if command == "R" else -1
                rover["facing"] = FACINGS[(FACINGS.index(rover["facing"]) + turn) % 4]
            else:
                dx, dy = STEPS[rover["facing"]]
                if command == "B":
                    dx, dy = -dx, -dy
                nx, ny = (rover["x"] + dx) % SIZE, (rover["y"] + dy) % SIZE
                if self._occupant(nx, ny) is not None:
                    continue
                rover["x"], rover["y"] = nx, ny
                rover["odometer"] += 1
            done += 1
        return done

    def get_location(self, rover_id):
        rover = self._require(rover_id)
        return (rover["x"], rover["y"], rover["facing"])

    def get_rover_at(self, x, y):
        check_cell(x, y)
        return self._occupant(x, y)

    def get_odometer(self, rover_id):
        return self._require(rover_id)["odometer"]

    def get_rovers(self):
        return list(self._rovers)

    def _occupant(self, x, y):
        for rover_id, rover in self._rovers.items():
            if (rover["x"], rover["y"]) == (x, y):
                return rover_id
        return None

    def _require(self, rover_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(rover_id, str) or rover_id not in self._rovers:
            raise KeyError(rover_id)
        return self._rovers[rover_id]
