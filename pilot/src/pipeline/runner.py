"""Sandbox runner: executes generated programs and their tests in Docker.

Generated code never runs on the host. Each run gets a fresh container that:
- has no network (`--network none`);
- runs as the host user's uid (never root; `nobody` if the host user is
  root), with all capabilities dropped and privilege escalation blocked.
  Using the host uid means the host can read and delete everything the
  program writes under /out;
- sees the program and test files read-only at /work, with a size-limited
  tmpfs at /tmp as its only scratch space, and /out for result files;
- is limited in memory (no swap), CPUs, processes, file size and wall time;
- is removed afterwards, whatever happened, killing any process left in it.

The runner reports what happened and never raises because a program
misbehaved. Failures of Docker itself come back as status "infra_error",
which callers must never count against the program.

Usage:
    runner = SandboxRunner(cfg.sandbox, owner=run_id)
    runner.ensure_image()            # build the image from build_context if missing
    runner.sweep()                   # remove containers a crashed run left behind
    result = runner.run(RunRequest(
        files={"records.py": program, "tests/test_x.py": tests},
        command=["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                 "--junitxml=/out/report.xml", "tests"],
    ))
    result.status, result.exit_code, result.stdout, result.out_files["report.xml"]
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
import time
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import IO, Literal

from .config import SandboxConfig

Status = Literal["ok", "nonzero_exit", "timeout", "oom", "infra_error"]

NOBODY = "65534:65534"  # nobody:nogroup in the Debian-based image
LABEL = "pipeline.sandbox"  # every sandbox container carries this label
SIGKILL_EXIT = 128 + 9  # exit status of a process killed by SIGKILL
STATUS_FILE = ".sandbox_exit"  # written to /out by the wrapper; not a program output

# Runs the program, then records its exit code and the cgroup's oom_kill
# count in /out/.sandbox_exit. Docker's own OOMKilled flag is unreliable:
# it comes from an asynchronous event that is lost when the container exits
# and its cgroup disappears first (measured: 8 of 80 OOM kills unflagged with
# 8 containers running). The kernel's counter in memory.events is exact.
_WRAPPER = (
    '"$@"; rc=$?; oom=0; '
    '{ while read -r key value; do [ "$key" = oom_kill ] && oom=$value; done '
    "< /sys/fs/cgroup/memory.events; } 2>/dev/null; "
    'echo "$rc $oom" > /out/' + STATUS_FILE + "; "
    'exit "$rc"'
)
# Seconds to wait for Docker housekeeping commands (inspect, kill, rm).
_DOCKER_CMD_TIMEOUT = 60


class SandboxError(RuntimeError):
    """The sandbox can't be set up at all (e.g. the image can't be built)."""


@dataclass(frozen=True)
class RunRequest:
    files: Mapping[str, bytes]  # relative path -> contents, placed under /work
    command: Sequence[str]  # run with /work as the working directory
    timeout_s: float | None = None  # overrides the config's timeout_s


@dataclass(frozen=True)
class RunResult:
    status: Status
    exit_code: int | None
    stdout: str
    stderr: str
    stdout_truncated: bool
    stderr_truncated: bool
    out_files: dict[str, bytes]  # everything the run wrote under /out
    wall_s: float
    detail: str = ""  # what went wrong, for infra_error
    command: tuple[str, ...] = field(default=(), repr=False)


class SandboxRunner:
    def __init__(self, cfg: SandboxConfig, owner: str = "pipeline") -> None:
        self.cfg = cfg
        # A second label scopes sweep() to this owner's containers, so two
        # runs (or a test session) never remove each other's containers.
        self.owner = owner
        self._image_id: str | None = None

    # -- image --

    def ensure_image(self) -> str:
        """Return the image's content id, building it from build_context if
        the tag doesn't exist yet."""
        image_id = self._inspect_image()
        if image_id is None:
            if self.cfg.build_context is None:
                raise SandboxError(f"image {self.cfg.image} not found and no build_context set")
            build = _docker(
                ["build", "-q", "-t", self.cfg.image, str(self.cfg.build_context)], timeout=1800
            )
            if build.returncode != 0:
                raise SandboxError(f"building {self.cfg.image} failed:\n{build.stderr[-2000:]}")
            image_id = self._inspect_image()
            if image_id is None:
                raise SandboxError(f"image {self.cfg.image} still missing after build")
        self._image_id = image_id
        return image_id

    @property
    def image_id(self) -> str:
        """Content id of the image (sha256:...). Results must be keyed by
        this, not by the tag: a rebuild under the same tag changes it."""
        return self._image_id or self.ensure_image()

    def _inspect_image(self) -> str | None:
        result = _docker(["image", "inspect", "--format", "{{.Id}}", self.cfg.image])
        return result.stdout.strip() if result.returncode == 0 else None

    # -- running --

    def run(self, request: RunRequest) -> RunResult:
        timeout = request.timeout_s if request.timeout_s is not None else self.cfg.timeout_s
        name = f"pipeline-{uuid.uuid4().hex[:16]}"
        start = time.monotonic()
        # ignore_cleanup_errors: a leftover temp file must never turn into
        # an exception after the result is known.
        with tempfile.TemporaryDirectory(
            prefix="pipeline-sandbox-", ignore_cleanup_errors=True
        ) as tmp:
            work, out = Path(tmp) / "work", Path(tmp) / "out"
            _write_files(work, request.files)
            out.mkdir()
            if _container_user() == NOBODY:
                os.chmod(out, 0o777)  # let nobody write to the host user's dir
            command = self.create_command(name, work, out, request.command)
            created = _docker(command[1:])
            if created.returncode != 0:
                return _infra(f"docker create failed: {created.stderr.strip()}", start, command)
            try:
                return self._start(name, timeout, start, out, command)
            finally:
                # Removing the container kills every process still in it.
                _docker(["rm", "-f", name])

    def create_command(self, name: str, work: Path, out: Path, command: Sequence[str]) -> list[str]:
        """The full `docker create` command line; separate so the security
        flags can be checked without Docker."""
        c = self.cfg
        return [
            "docker", "create",
            "--name", name,
            # Never fetch an image from a registry: a missing image is an
            # infra_error at once, and nothing unexpected is downloaded.
            "--pull", "never",
            "--label", f"{LABEL}=1",
            "--label", f"{LABEL}.owner={self.owner}",
            "--network", "none",
            "--user", _container_user(),
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--read-only",
            "--tmpfs", f"/tmp:rw,nosuid,nodev,noexec,size={c.tmpfs_size}",
            "--mount", f"type=bind,src={work},dst=/work,readonly",
            "--mount", f"type=bind,src={out},dst=/out",
            "--workdir", "/work",
            "--memory", c.memory,
            "--memory-swap", c.memory,  # equal to --memory: no swap
            "--cpus", str(c.cpus),
            "--pids-limit", str(c.pids_limit),
            "--ulimit", f"fsize={c.file_size_limit_bytes}",
            # tini as PID 1 reaps zombie processes left by the program.
            "--init",
            # Output is captured through the attached streams; no log file
            # on the Docker host can grow without bound.
            "--log-driver", "none",
            "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--env", "PYTHONUNBUFFERED=1",  # output written before a kill is kept
            "--env", "PYTHONHASHSEED=0",  # set and dict-of-str order is reproducible
            "--env", "HOME=/tmp",
            "--env", "HYPOTHESIS_STORAGE_DIRECTORY=/tmp/.hypothesis",
            self.image_id,
            "sh", "-c", _WRAPPER, "sandbox-wrapper",
            *command,
        ]  # fmt: skip

    def _start(
        self, name: str, timeout: float, start: float, out: Path, command: list[str]
    ) -> RunResult:
        proc = subprocess.Popen(
            ["docker", "start", "--attach", name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        cap = self.cfg.output_cap_bytes
        stdout, stderr = _CappedReader(proc.stdout, cap), _CappedReader(proc.stderr, cap)
        timed_out = False
        try:
            proc.wait(timeout=max(0.0, timeout - (time.monotonic() - start)))
        except subprocess.TimeoutExpired:
            timed_out = True
            _docker(["kill", name])
            try:
                proc.wait(timeout=_DOCKER_CMD_TIMEOUT)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        stdout.join()
        stderr.join()
        wall = time.monotonic() - start

        state = _docker(["inspect", "--format", "{{json .State}}", name])
        if state.returncode != 0:
            return _infra(f"docker inspect failed: {state.stderr.strip()}", start, command)
        info = json.loads(state.stdout)
        exit_code = info.get("ExitCode")
        out_files = _read_tree(out)
        oom_kills = _oom_kills(out_files.pop(STATUS_FILE, None))
        if timed_out:
            status: Status = "timeout"
        elif info.get("OOMKilled") or (exit_code != 0 and oom_kills > 0):
            status = "oom"
        elif info.get("Error"):
            # The container never ran the command (e.g. it doesn't exist).
            return _infra(f"container error: {info['Error']}", start, command)
        elif exit_code == SIGKILL_EXIT:
            # Killed by SIGKILL, but not by our timeout and not by the memory
            # limit: something outside the program did it (the host's OOM
            # killer, a Docker restart, an operator). Exit 137 is ambiguous
            # (a program could also call sys.exit(137)), so it is treated as
            # infrastructure and never counted against the program.
            return _infra("killed by SIGKILL (exit 137), not by timeout or OOM", start, command)
        elif exit_code == 0:
            status = "ok"
        else:
            status = "nonzero_exit"
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
        """Remove this owner's leftover containers (e.g. after a crash);
        returns how many were removed."""
        listed = _docker(["ps", "-aq", "--filter", f"label={LABEL}.owner={self.owner}"])
        ids = listed.stdout.split()
        if ids:
            _docker(["rm", "-f", *ids])
        return len(ids)


class _CappedReader:
    """Drains a pipe on a background thread, keeping only the first `cap`
    bytes. Draining continues past the cap so the writer never blocks, but
    memory use stays bounded however much a program prints."""

    def __init__(self, stream: IO[bytes] | None, cap: int) -> None:
        self.cap = cap
        self.data = bytearray()
        self.truncated = False
        self._thread = threading.Thread(target=self._drain, args=(stream,), daemon=True)
        self._thread.start()

    def _drain(self, stream: IO[bytes] | None) -> None:
        if stream is None:
            return
        while chunk := stream.read1(65536):  # type: ignore[attr-defined]
            room = self.cap - len(self.data)
            self.data += chunk[:room]
            if len(chunk) > room:
                self.truncated = True
        stream.close()

    def join(self) -> None:
        self._thread.join()

    def text(self) -> str:
        return self.data.decode("utf-8", errors="replace")


def _oom_kills(status: bytes | None) -> int:
    """oom_kill count from the wrapper's status file ("<exit> <count>");
    0 if the file is missing or unreadable."""
    try:
        return int(status.split()[1]) if status else 0
    except (IndexError, ValueError):
        return 0


def _container_user() -> str:
    """The host user's uid:gid, so files written to /out belong to the host
    user (a uid only means something to the kernel; inside the container it
    is just an unprivileged user). Never root: fall back to nobody."""
    uid, gid = os.getuid(), os.getgid()
    return NOBODY if uid == 0 else f"{uid}:{gid}"


def _docker(
    args: Sequence[str], timeout: float = _DOCKER_CMD_TIMEOUT
) -> subprocess.CompletedProcess:
    """Run a docker CLI command; a missing CLI or a hang becomes a failed
    result (returncode 127), not an exception."""
    try:
        return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(["docker", *args], 127, "", str(exc))


def _infra(detail: str, start: float, command: list[str]) -> RunResult:
    return RunResult(
        status="infra_error",
        exit_code=None,
        stdout="",
        stderr="",
        stdout_truncated=False,
        stderr_truncated=False,
        out_files={},
        wall_s=time.monotonic() - start,
        detail=detail,
        command=tuple(command),
    )


def _write_files(root: Path, files: Mapping[str, bytes]) -> None:
    """Write files under root. Paths come from our own registry and parser,
    so an unsafe one is a bug in the caller: raise instead of returning a
    result."""
    root.mkdir(mode=0o755)
    for name, data in files.items():
        p = PurePosixPath(name)
        if not name or p.is_absolute() or ".." in p.parts or "\\" in name or str(p) != name:
            raise ValueError(f"unsafe path for the sandbox: {name!r}")
        target = root / p
        for parent in reversed(target.relative_to(root).parents[:-1]):
            (root / parent).mkdir(mode=0o755, exist_ok=True)
        target.write_bytes(data)
        os.chmod(target, 0o644)


def _read_tree(root: Path) -> dict[str, bytes]:
    """Regular files under root. Symlinks are skipped and never followed: a
    program could otherwise point one at a host file and have us read it."""
    found = {}
    for directory, _, names in os.walk(root, followlinks=False):
        for name in names:
            p = Path(directory) / name
            if p.is_file() and not p.is_symlink():
                found[p.relative_to(root).as_posix()] = p.read_bytes()
    return dict(sorted(found.items()))
