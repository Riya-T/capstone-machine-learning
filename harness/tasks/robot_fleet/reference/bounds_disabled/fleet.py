"""Robot fleet on a grid with optional edges, where robots can be disabled.

Correct solution for robot_fleet after c_bounds and c_disabled.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from fleet import RobotFleet
    fleet = RobotFleet(width=10, height=10)
    fleet.add_robot("rover", 0, 0, "N")
    fleet.disable("rover")
"""

HEADINGS = ("N", "E", "S", "W")  # clockwise order
MOVES = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
COMMANDS = ("L", "R", "A")


class FleetError(Exception):
    pass


class RobotDisabled(FleetError):
    pass


def check_commands(commands):
    if not isinstance(commands, str) or any(c not in COMMANDS for c in commands):
        raise ValueError(f"commands must be a str of L, R and A, got {commands!r}")


def check_bound(value, what):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{what} must be None or an int >= 1, got {value!r}")


def step(x, y, heading, command):
    """The pose reached from (x, y, heading) after one command."""
    if command == "L":
        return x, y, HEADINGS[(HEADINGS.index(heading) - 1) % 4]
    if command == "R":
        return x, y, HEADINGS[(HEADINGS.index(heading) + 1) % 4]
    dx, dy = MOVES[heading]
    return x + dx, y + dy, heading


class RobotFleet:
    def __init__(self, width=None, height=None):
        check_bound(width, "width")
        check_bound(height, "height")
        self._width = width
        self._height = height
        self._poses = {}  # name -> (x, y, heading), in the order added
        self._counts = {}  # name -> commands executed so far
        self._disabled = set()

    def add_robot(self, name, x, y, heading):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._poses:
            raise FleetError(f"robot {name!r} already exists")
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("x and y must be ints")
        if heading not in HEADINGS:
            raise ValueError(f"heading must be one of N, E, S, W, got {heading!r}")
        if not self._inside(x, y):
            raise ValueError(f"({x}, {y}) is outside the grid")
        self._poses[name] = (x, y, heading)
        self._counts[name] = 0

    def run(self, name, commands):
        self._require(name)
        check_commands(commands)
        if name in self._disabled:
            raise RobotDisabled(f"robot {name!r} is disabled")
        pose = self._simulate(name, commands)
        self._commit(name, pose, len(commands))

    def run_all(self, commands):
        check_commands(commands)
        # Simulate every enabled robot before moving any, so a failure changes nothing.
        poses = {name: self._simulate(name, commands) for name in self.get_enabled_robots()}
        for name, pose in poses.items():
            self._commit(name, pose, len(commands))

    def get_position(self, name):
        self._require(name)
        x, y, _ = self._poses[name]
        return (x, y)

    def get_heading(self, name):
        self._require(name)
        return self._poses[name][2]

    def get_robots(self):
        return list(self._poses)

    def get_command_count(self, name):
        self._require(name)
        return self._counts[name]

    def get_bounds(self):
        return (self._width, self._height)

    def disable(self, name):
        self._require(name)
        self._disabled.add(name)

    def enable(self, name):
        self._require(name)
        self._disabled.discard(name)

    def is_enabled(self, name):
        self._require(name)
        return name not in self._disabled

    def get_enabled_robots(self):
        return [name for name in self._poses if name not in self._disabled]

    def _simulate(self, name, commands):
        x, y, heading = self._poses[name]
        for command in commands:
            x, y, heading = step(x, y, heading, command)
            if not self._inside(x, y):
                raise FleetError(f"robot {name!r} would leave the grid at ({x}, {y})")
        return (x, y, heading)

    def _commit(self, name, pose, count):
        self._poses[name] = pose
        self._counts[name] += count

    def _inside(self, x, y):
        if self._width is not None and not 0 <= x < self._width:
            return False
        if self._height is not None and not 0 <= y < self._height:
            return False
        return True

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._poses:
            raise KeyError(name)
