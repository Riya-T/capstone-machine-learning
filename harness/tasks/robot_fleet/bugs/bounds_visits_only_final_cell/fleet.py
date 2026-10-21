"""Robot fleet on a grid with optional edges that reports how far each robot
travelled.

Planted bug (after c_distance and c_bounds): the bounds were added
correctly, but the new simulate-then-commit path records only the cell the
robot ends on, so cells passed through in the middle of a run are missing
from get_visited_cells.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from fleet import RobotFleet
    fleet = RobotFleet(width=10, height=10)
    fleet.add_robot("rover", 0, 0, "N")
    fleet.run("rover", "RAAL")
"""

HEADINGS = ("N", "E", "S", "W")  # clockwise order
MOVES = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
COMMANDS = ("L", "R", "A")


class FleetError(Exception):
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
        self._starts = {}  # name -> (x, y) the robot was added at
        self._advances = {}  # name -> advance commands executed so far
        self._visited = {}  # name -> cells in the order first entered

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
        self._starts[name] = (x, y)
        self._advances[name] = 0
        self._visited[name] = [(x, y)]

    def run(self, name, commands):
        self._require(name)
        check_commands(commands)
        pose, advances = self._simulate(name, commands)
        self._commit(name, pose, advances, len(commands))

    def run_all(self, commands):
        check_commands(commands)
        results = {name: self._simulate(name, commands) for name in self._poses}
        for name, (pose, advances) in results.items():
            self._commit(name, pose, advances, len(commands))

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

    def get_distance_travelled(self, name):
        self._require(name)
        return self._advances[name]

    def get_displacement(self, name):
        self._require(name)
        x, y, _ = self._poses[name]
        start_x, start_y = self._starts[name]
        return abs(x - start_x) + abs(y - start_y)

    def get_visited_cells(self, name):
        self._require(name)
        return list(self._visited[name])

    def _simulate(self, name, commands):
        x, y, heading = self._poses[name]
        advances = 0
        for command in commands:
            x, y, heading = step(x, y, heading, command)
            if not self._inside(x, y):
                raise FleetError(f"robot {name!r} would leave the grid at ({x}, {y})")
            if command == "A":
                advances += 1
        return (x, y, heading), advances

    def _commit(self, name, pose, advances, count):
        self._poses[name] = pose
        self._counts[name] += count
        self._advances[name] += advances
        cell = (pose[0], pose[1])
        if cell not in self._visited[name]:
            self._visited[name].append(cell)

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
