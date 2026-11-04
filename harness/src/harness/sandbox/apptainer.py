"""Apptainer sandbox runner: runs generated programs and their tests in
Apptainer, for hosts without Docker (the Nexus cluster).

Same interface and result statuses as SandboxRunner in runner.py. Each run
is a fresh `apptainer exec` in user-namespace mode that:
- has no network (loopback only);
- runs as the host user with no capabilities and no new privileges;
- sees the image read-only, the code read-only at /work, /out for result
  files, and a small tmpfs shared by /tmp and /var/tmp; /dev/shm is
  read-only, /sys is absent, and no host path is mounted ($HOME, the
  current directory and the admin's bind paths are all turned off);
- has Docker's environment: Apptainer's own variables are removed;
- is limited in processes, memory per process, file size and time;
- is killed at the timeout with every process it started, Apptainer's
  squashfuse helper included (a plain kill of the process group leaves the
  helper running).

The process limit (sandbox.pids_limit) is RLIMIT_NPROC. The kernel counts
it per user namespace, so it binds each run alone: a fork bomb in one run
can't starve another, and the user's other processes (Ollama, the harness)
don't count.

Differences from Docker. The image id keeps their results apart.
- Memory is limited per process, by address space (ulimit -v), not for
  the whole container by RSS. A program over the limit gets a MemoryError
  instead of an OOM kill. A nonzero exit other than 1 with "MemoryError" in
  its output is reported as "oom". Exit 1 means pytest finished and wrote
  its report, and those per-test results are kept.
- No CPU limit: parallel runs share the job's CPUs, so keep
  sandbox_workers below them. A busy program is stopped only by the
  timeout.
- /tmp is not noexec. Its size is the admin's "sessiondir max size", and
  start-up fails unless that equals tmpfs_size.
Cgroup limits would need a systemd user session, which Slurm jobs lack.
Measurements behind these choices: docs/apptainer_sandbox.md.

ensure_image() checks the isolation with a probe run and raises
SandboxError if any of it is missing, so nothing runs unisolated.

Usage:
    runner = ApptainerRunner(cfg.sandbox, cfg.execution.apptainer_image)
    runner.ensure_image()     # build the SIF if it's missing, then probe it
    runner.sweep()            # kill helpers left by a crashed run
    result = runner.run(RunRequest(files={...}, command=["python", "-m", "pytest", ...]))
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path

from ..config import SandboxConfig
from .runner import (
    SIGKILL_EXIT,
    STATUS_FILE,
    RunRequest,
    RunResult,
    SandboxError,
    Status,
    _CappedReader,
    _infra,
    _read_tree,
    _write_files,
    classify,
)

# Part of every result key; never change it.
IMAGE_ID_PREFIX = "apptainer:sha256:"
DEF_FILE = "sandbox.def"  # in sandbox.build_context, next to the Dockerfile
# The host-side `timeout` kills the run this long after its own timeout, in
# case the harness dies before it can.
_GUARD_S = 30
_BUILD_TIMEOUT_S = 1800
_HELPER = "squashfuse_ll"  # mounts the SIF in user-namespace mode

# Removes Apptainer's own variables so the program sees Docker's
# environment, sets the limits (positional arguments 1-3), runs the
# program, and records its exit code in /out like the Docker wrapper ("-":
# there is no OOM counter). If a limit can't be set, the program never runs
# and the missing status file makes the run an infra_error. dash units:
# -p processes, -v KiB, -f 512-byte blocks.
_WRAPPER = (
    "for v in $(env | cut -d= -f1); do "
    "case $v in APPTAINER_*|SINGULARITY_*) unset $v;; esac; done; "
    "unset LD_LIBRARY_PATH PS1 PROMPT_COMMAND; export HOME=/tmp; "
    'ulimit -p "$1" && ulimit -v "$2" && ulimit -f "$3" || exit 125; shift 3; '
    '"$@"; rc=$?; echo "$rc -" > /out/' + STATUS_FILE + "; "
    'exit "$rc"'
)

# Runs inside the container at start-up; ensure_image compares the result
# with what the config and this module promise.
_PROBE = r"""
import json, os, resource, socket

def writable(path):
    try:
        open(path, "w").close()
        return True
    except OSError:
        return False

status = dict(line.split(":\t", 1) for line in open("/proc/self/status"))
tmp = os.statvfs("/tmp")
print(json.dumps({
    "uid": os.getuid(),
    "uid_map": open("/proc/self/uid_map").read().split(),
    "cap_eff": status["CapEff"].strip(),
    "no_new_privs": status["NoNewPrivs"].strip(),
    "interfaces": sorted(name for _, name in socket.if_nameindex()),
    "visible": [p for p in json.load(open("host_paths.json")) if os.path.exists(p)],
    "tmp_bytes": tmp.f_blocks * tmp.f_frsize,
    "shm_writable": writable("/dev/shm/probe"),
    "sys": os.path.exists("/sys/kernel"),  # /sys itself is an empty dir in the image
    "nproc": resource.getrlimit(resource.RLIMIT_NPROC)[0],
    "address_space": resource.getrlimit(resource.RLIMIT_AS)[0],
    "file_size": resource.getrlimit(resource.RLIMIT_FSIZE)[0],
    "env": sorted(os.environ),
}))
"""


class ApptainerRunner:
    def __init__(self, cfg: SandboxConfig, sif: Path) -> None:
        self.cfg = cfg
        self.sif = Path(sif)
        self._image_id: str | None = None
        self._image_stat: tuple[int, int, int] | None = None
        self._memory_kib = parse_size(cfg.memory) // 1024
        self._file_blocks = cfg.file_size_limit_bytes // 512

    # -- image --

    def ensure_image(self) -> str:
        """Return the image id, building the SIF from sandbox.def if it's
        missing, and check the sandbox's isolation with a probe run."""
        if not self.sif.is_file():
            self._build()
        image_id = self.existing_image_id()
        if image_id is None:
            raise SandboxError(f"image {self.sif} still missing after build")
        self._image_id, self._image_stat = image_id, _stat(self.sif)
        try:
            self._probe()
        except BaseException:
            self._image_id = None  # the next run probes again
            raise
        return image_id

    @property
    def image_id(self) -> str:
        """apptainer:sha256:<hex> of the SIF file. Results must be keyed by
        this: a rebuild gives a different file even from the same
        definition."""
        return self._image_id or self.ensure_image()

    def existing_image_id(self) -> str | None:
        """The image id if the SIF exists; never builds it."""
        if not self.sif.is_file():
            return None
        digest = hashlib.sha256()
        with self.sif.open("rb") as f:
            while chunk := f.read(1 << 20):
                digest.update(chunk)
        return IMAGE_ID_PREFIX + digest.hexdigest()

    def _build(self) -> None:
        if self.cfg.build_context is None:
            raise SandboxError(f"image {self.sif} not found and no build_context set")
        definition = self.cfg.build_context / DEF_FILE
        if not definition.is_file():
            raise SandboxError(f"image {self.sif} not found and {definition} is missing")
        self.sif.parent.mkdir(parents=True, exist_ok=True)
        # Built under another name and renamed, so a half-built file is
        # never taken for the image.
        partial = self.sif.with_name(self.sif.name + ".building")
        partial.unlink(missing_ok=True)
        build = _command(["apptainer", "build", str(partial), str(definition)], _BUILD_TIMEOUT_S)
        if build.returncode != 0 or not partial.is_file():
            partial.unlink(missing_ok=True)
            output = (build.stdout + build.stderr)[-2000:]
            raise SandboxError(f"building {self.sif} failed:\n{output}")
        os.replace(partial, self.sif)

    def _probe(self) -> None:
        """Raise SandboxError unless a run is isolated as promised."""
        host_paths = sorted({"/fs", str(Path.home()), str(Path.cwd()), str(self.sif.parent)})
        result = self.run(
            RunRequest(
                files={
                    "probe.py": _PROBE.encode(),
                    "host_paths.json": json.dumps(host_paths).encode(),
                },
                command=["python", "probe.py"],
            )
        )
        if result.status != "ok":
            raise SandboxError(
                f"sandbox probe failed ({result.status}): {result.detail or result.stderr[-1000:]}"
            )
        got = json.loads(result.stdout)
        uid = os.getuid()
        tmpfs = parse_size(self.cfg.tmpfs_size)
        problems = [
            (uid == 0, "the harness runs as root; run it as an ordinary user"),
            (got["uid"] != uid, f"runs as uid {got['uid']}, not {uid}"),
            # One uid mapped onto itself: user-namespace mode, which the
            # per-run process limit relies on.
            (got["uid_map"] != [str(uid), str(uid), "1"], f"uid_map is {got['uid_map']}"),
            (got["cap_eff"] != "0" * 16, f"has capabilities {got['cap_eff']}"),
            (got["no_new_privs"] != "1", "no_new_privs is not set"),
            (got["interfaces"] != ["lo"], f"network interfaces {got['interfaces']}"),
            (bool(got["visible"]), f"host paths visible: {got['visible']}"),
            (
                got["tmp_bytes"] != tmpfs,
                f"/tmp holds {got['tmp_bytes']} bytes but sandbox.tmpfs_size is "
                f"{self.cfg.tmpfs_size}; Apptainer's size is the admin's 'sessiondir max size'",
            ),
            (got["shm_writable"], "/dev/shm is writable"),
            (got["sys"], "/sys is mounted"),
            (got["nproc"] != self.cfg.pids_limit, f"process limit is {got['nproc']}"),
            (
                got["address_space"] != self._memory_kib * 1024,
                f"memory limit is {got['address_space']}",
            ),
            (got["file_size"] != self._file_blocks * 512, f"file size limit is {got['file_size']}"),
            (
                any(v.startswith(("APPTAINER_", "SINGULARITY_")) for v in got["env"]),
                f"Apptainer variables left in the environment: {got['env']}",
            ),
        ]
        failed = [message for bad, message in problems if bad]
        if failed:
            raise SandboxError("sandbox isolation check failed: " + "; ".join(failed))

    # -- running --

    def run(self, request: RunRequest) -> RunResult:
        timeout = request.timeout_s if request.timeout_s is not None else self.cfg.timeout_s
        _ = self.image_id  # build and probe before the first run
        start = time.monotonic()
        with tempfile.TemporaryDirectory(
            prefix="harness-sandbox-", ignore_cleanup_errors=True
        ) as tmp:
            work, out, shm = Path(tmp) / "work", Path(tmp) / "out", Path(tmp) / "shm"
            _write_files(work, request.files)
            out.mkdir()
            shm.mkdir()  # stays empty: mounted read-only over /dev/shm
            command = self.create_command(work, out, shm, request.command, timeout)
            # Results are keyed by the hash taken at start-up; a SIF replaced
            # since then must not produce results under the old key.
            if _stat(self.sif) != self._image_stat:
                return _infra("image_changed", f"{self.sif} changed since start-up", start, command)
            return self._start(command, timeout, start, out)

    def create_command(
        self, work: Path, out: Path, shm: Path, command: Sequence[str], timeout: float
    ) -> list[str]:
        """The full command line; separate so the isolation flags can be
        checked without Apptainer."""
        c = self.cfg
        return [
            "timeout", "--signal=KILL", str(int(timeout) + _GUARD_S),
            "apptainer", "--silent", "exec",
            # User-namespace mode: the process limit counts this run only.
            "--userns",
            # Own PID, IPC and mount namespaces, clean environment, private
            # /tmp; no home directory.
            "--containall", "--no-home", "--cleanenv",
            # No admin bind paths, home, current directory or /sys.
            "--no-mount", "bind-paths,home,cwd,sys",
            "--no-privs",
            "--no-eval",
            "--net", "--network", "none",
            "--bind", f"{work}:/work:ro",
            "--bind", f"{out}:/out",
            "--bind", f"{shm}:/dev/shm:ro",
            "--pwd", "/work",
            "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--env", "PYTHONUNBUFFERED=1",  # output written before a kill is kept
            "--env", "PYTHONHASHSEED=0",  # set and dict-of-str order is reproducible
            "--env", "HYPOTHESIS_STORAGE_DIRECTORY=/tmp/.hypothesis",
            str(self.sif),
            "sh", "-c", _WRAPPER, "sandbox-wrapper",
            str(c.pids_limit), str(self._memory_kib), str(self._file_blocks),
            *command,
        ]  # fmt: skip

    def _start(self, command: list[str], timeout: float, start: float, out: Path) -> RunResult:
        try:
            # A session of its own, so the whole run can be killed as a group.
            proc = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
            )
        except OSError as exc:
            return _infra("apptainer_start", f"could not start apptainer: {exc}", start, command)
        cap = self.cfg.output_cap_bytes
        stdout, stderr = _CappedReader(proc.stdout, cap), _CappedReader(proc.stderr, cap)
        timed_out = False
        try:
            proc.wait(timeout=max(0.0, timeout - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_tree(proc.pid)
            proc.wait()
        stdout.join()
        stderr.join()
        wall = time.monotonic() - start

        out_files = _read_tree(out)
        exit_code = _wrapper_exit(out_files.pop(STATUS_FILE, None))
        if not timed_out:
            if exit_code is None:
                detail = stderr.text()[-1000:].strip()
                return _infra(
                    "apptainer_start",
                    f"apptainer exited {proc.returncode} before the program ran: {detail}",
                    start,
                    command,
                )
            # The wrapper's exit is the container's. A mismatch means the
            # wrapper was killed after something else wrote the status file.
            if exit_code != proc.returncode:
                return _infra(
                    "status_mismatch",
                    f"status file says {exit_code}, apptainer exited {proc.returncode}",
                    start,
                    command,
                )
        if exit_code is None:  # killed at the timeout before the wrapper finished
            exit_code = SIGKILL_EXIT
        status = status_of(timed_out, exit_code, _memory_error(stdout, stderr))
        if status == "infra_error":
            return _infra(
                "unexplained_sigkill",
                "killed by SIGKILL (exit 137), not by timeout",
                start,
                command,
            )
        return RunResult(
            status=status,
            exit_code=exit_code,
            stdout=stdout.text(),
            stderr=stderr.text(),
            stdout_truncated=stdout.truncated,
            stderr_truncated=stderr.truncated,
            out_files=out_files,
            wall_s=wall,
            command=tuple(command),
        )

    # -- cleanup --

    def sweep(self) -> int:
        """Kill squashfuse helpers for this SIF that outlived their run (the
        harness died before it could kill them); returns how many. A live
        run's helper always has Apptainer's starter as its parent, so it is
        never touched."""
        sif = os.path.realpath(self.sif)
        table = _processes()
        killed = 0
        for pid, (ppid, name) in table.items():
            parent = table.get(ppid, (0, ""))[1]
            if name == _HELPER and parent != "starter" and _holds_file(pid, sif):
                try:
                    os.kill(pid, signal.SIGKILL)
                    killed += 1
                except ProcessLookupError:
                    pass
        return killed


def status_of(timed_out: bool, exit_code: int, memory_error: bool) -> Status:
    """A finished run's status. As with Docker, exit 137 without a timeout
    is infrastructure (never scored).

    A run that hit the memory limit shows MemoryError in its output. It is
    "oom" unless it exited 1: then pytest finished and wrote its report,
    whose per-test results are worth keeping. Without this rule, pytest's
    INTERNALERROR (exit 3) or a missing report would make the program's own
    memory overrun an infra_error, which never counts against it.
    """
    status = classify(timed_out, {"ExitCode": exit_code}, None)
    if status == "nonzero_exit" and exit_code != 1 and memory_error:
        return "oom"
    return status


def parse_size(text: str) -> int:
    """Bytes in a Docker-style size: "512m", "64m", "1g", "4096"."""
    match = re.fullmatch(r"(\d+)([kmg]?)b?", text.strip().lower())
    if match is None:
        raise SandboxError(f"unreadable size {text!r}")
    return int(match[1]) * {"": 1, "k": 1 << 10, "m": 1 << 20, "g": 1 << 30}[match[2]]


def _memory_error(*readers: _CappedReader) -> bool:
    return any(b"MemoryError" in r.data or b"MemoryError" in r.tail for r in readers)


def _wrapper_exit(status: bytes | None) -> int | None:
    """The program's exit code from the wrapper's status file ("<exit> -");
    None when the file is missing or garbled."""
    try:
        return int(status.split()[0]) if status else None
    except (IndexError, ValueError):
        return None


def _kill_tree(root: int) -> None:
    """SIGKILL the run's process group and every process descended from it.
    The group alone misses Apptainer's squashfuse helper, which runs in a
    group of its own. Processes inside the container die with its PID
    namespace either way."""
    tree = _descendants(root)
    for pid in [-root, *tree]:  # a negative pid is the process group
        with contextlib.suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)


def _descendants(root: int) -> list[int]:
    children: dict[int, list[int]] = {}
    for pid, (ppid, _) in _processes().items():
        children.setdefault(ppid, []).append(pid)
    found, todo = [], [root]
    while todo:
        for child in children.get(todo.pop(), []):
            found.append(child)
            todo.append(child)
    return found


def _processes() -> dict[int, tuple[int, str]]:
    """pid -> (parent pid, name) for this user's processes."""
    table = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != os.getuid():
                continue
            stat = (entry / "stat").read_text()
        except OSError:
            continue  # exited meanwhile
        # The name is in parentheses and may itself contain spaces or ")".
        name = stat[stat.index("(") + 1 : stat.rindex(")")]
        table[int(entry.name)] = (int(stat[stat.rindex(")") + 2 :].split()[1]), name)
    return table


def _holds_file(pid: int, path: str) -> bool:
    try:
        fds = list(Path(f"/proc/{pid}/fd").iterdir())
    except OSError:
        return False
    for fd in fds:
        try:
            if os.readlink(fd) == path:
                return True
        except OSError:
            pass
    return False


def _stat(path: Path) -> tuple[int, int, int] | None:
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_ino, st.st_size, st.st_mtime_ns)


def _command(args: Sequence[str], timeout: float) -> subprocess.CompletedProcess:
    """Run a command; a missing program or a hang becomes a failed result
    (returncode 127), not an exception."""
    try:
        return subprocess.run(list(args), capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(list(args), 127, "", str(exc))
