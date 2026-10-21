"""Rover fleet on an adjustable plateau with obstacles, remembering the path
of every rover.

Correct solution for rover_fleet after c_grid_size, c_obstacles and c_paths.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from rovers import RoverFleet
    fleet = RoverFleet(width=20, height=5, wrap=False)
    fleet.land("scout", 0, 0, "north")
    fleet.land("glider", 19, 4, "east", wrap=True)
    fleet.drive("scout", "FFRF")
    fleet.add_obstacle(3, 3)
    fleet.get_path("scout")
"""

FACINGS = ["north", "east", "south", "west"]  # clockwise order
STEPS = {"north": (0, 1), "east": (1, 0), "south": (0, -1), "west": (-1, 0)}
COMMANDS = set("FBLR")


class RoverError(Exception):
    pass


def check_size(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be an int of at least 1, got {value!r}")


def check_commands(commands):
    if not isinstance(commands, str) or not set(commands) <= COMMANDS:
        raise ValueError(f"invalid commands {commands!r}")


class RoverFleet:
    def __init__(self, width=10, height=10, wrap=True):
        check_size(width, "width")
        check_size(height, "height")
        if not isinstance(wrap, bool):
            raise ValueError(f"wrap must be a bool, got {wrap!r}")
        self._width = width
        self._height = height
        self._wrap = wrap
        # rover id -> {"x", "y", "facing", "odometer", "wrap", "path"}, in
        # landing order; "wrap" is None when the rover follows the fleet's
        # setting, and "path" lists every cell it has stood on
        self._rovers = {}
        self._obstacles = []  # obstacle cells as (x, y), in the order added

    def land(self, rover_id, x, y, facing, wrap=None):
        if not isinstance(rover_id, str) or not rover_id:
            raise ValueError("rover_id must be a non-empty str")
        if rover_id in self._rovers:
            raise RoverError(f"rover {rover_id!r} has already landed")
        self._check_cell(x, y)
        if facing not in FACINGS:
            raise ValueError(f"facing must be one of {FACINGS}, got {facing!r}")
        if wrap is not None and not isinstance(wrap, bool):
            raise ValueError(f"wrap must be None or a bool, got {wrap!r}")
        if self._blocked(x, y):
            raise RoverError(f"cell {(x, y)} is taken")
        self._rovers[rover_id] = {
            "x": x, "y": y, "facing": facing, "odometer": 0, "wrap": wrap,
            "path": [(x, y)],
        }

    def drive(self, rover_id, commands):
        rover = self._require(rover_id)
        check_commands(commands)
        done = 0
        for command in commands:
            if command in "LR":
                turn = 1 if command == "R" else -1
                rover["facing"] = FACINGS[(FACINGS.index(rover["facing"]) + turn) % 4]
            else:
                target = self._target(rover, command)
                if target is None or self._blocked(*target, mover=rover_id):
                    break
                rover["x"], rover["y"] = target
                rover["odometer"] += 1
                rover["path"].append(target)
            done += 1
        return done

    def get_location(self, rover_id):
        rover = self._require(rover_id)
        return (rover["x"], rover["y"], rover["facing"])

    def get_rover_at(self, x, y):
        self._check_cell(x, y)
        return self._occupant(x, y)

    def get_odometer(self, rover_id):
        return self._require(rover_id)["odometer"]

    def get_rovers(self):
        return list(self._rovers)

    def get_path(self, rover_id):
        return list(self._require(rover_id)["path"])

    def get_visitors(self, x, y):
        self._check_cell(x, y)
        return [r for r, rover in self._rovers.items() if (x, y) in rover["path"]]

    def get_explored(self, rover_id):
        return len(set(self._require(rover_id)["path"]))

    def get_plateau(self):
        return (self._width, self._height)

    def add_obstacle(self, x, y):
        self._check_cell(x, y)
        if self._blocked(x, y):
            raise RoverError(f"cell {(x, y)} already holds a rover or an obstacle")
        self._obstacles.append((x, y))

    def get_obstacles(self):
        return list(self._obstacles)

    def _target(self, rover, command):
        """The cell a move leads to, or None if it would leave the plateau."""
        dx, dy = STEPS[rover["facing"]]
        if command == "B":
            dx, dy = -dx, -dy
        nx, ny = rover["x"] + dx, rover["y"] + dy
        wraps = self._wrap if rover["wrap"] is None else rover["wrap"]
        if wraps:
            return (nx % self._width, ny % self._height)
        if 0 <= nx < self._width and 0 <= ny < self._height:
            return (nx, ny)
        return None

    def _check_cell(self, x, y):
        for value, limit in ((x, self._width), (y, self._height)):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value < limit:
                raise ValueError(f"cell {(x, y)!r} is not on the plateau")

    def _blocked(self, x, y, mover=None):
        # On a plateau one cell wide a rover may wrap onto its own cell.
        return (x, y) in self._obstacles or self._occupant(x, y) not in (None, mover)

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
