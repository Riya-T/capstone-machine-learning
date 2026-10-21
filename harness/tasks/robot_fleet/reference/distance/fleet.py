"""Robot fleet on an endless grid that reports how far each robot travelled.

Correct solution for robot_fleet after c_distance.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from fleet import RobotFleet
    fleet = RobotFleet()
    fleet.add_robot("rover", 0, 0, "N")
    fleet.run("rover", "RAAL")
    fleet.get_distance_travelled("rover")  # 2
"""

HEADINGS = ("N", "E", "S", "W")  # clockwise order
MOVES = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}
COMMANDS = ("L", "R", "A")


class FleetError(Exception):
    pass


def check_commands(commands):
    if not isinstance(commands, str) or any(c not in COMMANDS for c in commands):
        raise ValueError(f"commands must be a str of L, R and A, got {commands!r}")


def step(x, y, heading, command):
    """The pose reached from (x, y, heading) after one command."""
    if command == "L":
        return x, y, HEADINGS[(HEADINGS.index(heading) - 1) % 4]
    if command == "R":
        return x, y, HEADINGS[(HEADINGS.index(heading) + 1) % 4]
    dx, dy = MOVES[heading]
    return x + dx, y + dy, heading


class RobotFleet:
    def __init__(self):
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
        self._poses[name] = (x, y, heading)
        self._counts[name] = 0
        self._starts[name] = (x, y)
        self._advances[name] = 0
        self._visited[name] = [(x, y)]

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

    def _execute(self, name, commands):
        x, y, heading = self._poses[name]
        for command in commands:
            x, y, heading = step(x, y, heading, command)
            if command == "A":
                self._advances[name] += 1
                if (x, y) not in self._visited[name]:
                    self._visited[name].append((x, y))
        self._poses[name] = (x, y, heading)
        self._counts[name] += len(commands)

    def _require(self, name):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(name, str) or name not in self._poses:
            raise KeyError(name)
