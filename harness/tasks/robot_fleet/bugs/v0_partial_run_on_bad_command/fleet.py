"""Robot fleet: robots on an endless grid, driven by command strings.

Planted bug (initial version): commands are checked one at a time while they
are executed, so an invalid letter in the middle of a string leaves the
robot moved by the valid letters before it. The public checks only look at
the exception, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from fleet import RobotFleet
    fleet = RobotFleet()
    fleet.add_robot("rover", 0, 0, "N")
    fleet.run("rover", "RAAL")
"""

HEADINGS = ("N", "E", "S", "W")  # clockwise order
MOVES = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}


class FleetError(Exception):
    pass


def check_commands(commands):
    if not isinstance(commands, str):
        raise ValueError(f"commands must be a str, got {commands!r}")


def step(x, y, heading, command):
    """The pose reached from (x, y, heading) after one command."""
    if command == "L":
        return x, y, HEADINGS[(HEADINGS.index(heading) - 1) % 4]
    if command == "R":
        return x, y, HEADINGS[(HEADINGS.index(heading) + 1) % 4]
    if command == "A":
        dx, dy = MOVES[heading]
        return x + dx, y + dy, heading
    raise ValueError(f"unknown command {command!r}")


class RobotFleet:
    def __init__(self):
        self._poses = {}  # name -> (x, y, heading), in the order added
        self._counts = {}  # name -> commands executed so far

    def add_robot(self, name, x, y, heading):
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty str")
        if name in self._poses:
            raise FleetError(f"robot {name!r} already exists")
        if not isinstance(x, int) or not isinstance(y, int):
            raise ValueError("x and y must be ints")
        if heading not in HEADINGS:
            raise ValueError(f"heading must be one of N, E, S, W, got {heading!r}")
        self._poses[name] = (x, y, heading)
        self._counts[name] = 0

    def run(self, name, commands):
        self._require(name)
        check_commands(commands)
        self._execute(name, commands)

    def run_all(self, commands):
        check_commands(commands)
        for name in self._poses:
            self._execute(name, commands)

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

    def _execute(self, name, commands):
        for command in commands:
            x, y, heading = self._poses[name]
            self._poses[name] = step(x, y, heading, command)
            self._counts[name] += 1

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._poses:
            raise KeyError(name)
