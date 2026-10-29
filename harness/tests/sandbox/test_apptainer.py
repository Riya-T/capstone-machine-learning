"""Tests for harness.sandbox.apptainer.

Without Apptainer: the command line, sizes, statuses, the image id, runtime
selection, and that sandbox.def and the Dockerfile pin the same image.
With Apptainer (on a compute node, never the submission node): success,
errors, timeouts, memory, process, file and tmpfs limits, network and file
isolation, the environment, the start-up probe, and cleanup (no process or
squashfuse helper is left behind).

The SIF is runs/images/harness-sandbox_py3.11-v1.sif, built on first use (about
20 s); set HARNESS_TEST_SIF to use another.

Usage:
    uv run pytest tests/sandbox/test_apptainer.py -rs            # Apptainer tests skip without it
    uv run pytest tests/sandbox/test_apptainer.py -m apptainer   # only the Apptainer tests
"""

import dataclasses
import hashlib
import os
import re
import shutil
import signal
import subprocess
import threading
import time
import uuid
from pathlib import Path

import pytest

from harness.config import load_config
from harness.sandbox.apptainer import (
    IMAGE_ID_PREFIX,
    ApptainerRunner,
    _processes,
    _wrapper_exit,
    parse_size,
    status_of,
)
from harness.sandbox.runner import RunRequest, SandboxError, SandboxRunner, make_runner

ROOT = Path(__file__).resolve().parents[2]
SIF = Path(os.environ.get("HARNESS_TEST_SIF", ROOT / "runs/images/harness-sandbox_py3.11-v1.sif"))


def sandbox_cfg(**overrides):
    base = load_config(ROOT / "configs" / "mock.yaml").sandbox
    small = dict(timeout_s=20.0, memory="128m", pids_limit=64, output_cap_bytes=4096)
    return dataclasses.replace(base, **{**small, **overrides})


def py(code: str, timeout_s: float | None = None) -> RunRequest:
    return RunRequest(files={"main.py": code.encode()}, command=["python", "main.py"],
                      timeout_s=timeout_s)  # fmt: skip


PYTEST = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
          "--junitxml=/out/report.xml", "tests"]  # fmt: skip


# --- without Apptainer ------------------------------------------------------


def test_create_command_has_every_isolation_flag(tmp_path):
    runner = ApptainerRunner(sandbox_cfg(file_size_limit_bytes=1 << 20), tmp_path / "x.sif")
    cmd = runner.create_command(
        tmp_path / "w", tmp_path / "o", tmp_path / "s", ["python", "x.py"], timeout=20
    )
    joined = " ".join(cmd)
    for flag in [
        "timeout --signal=KILL 50 apptainer --silent exec",
        "--userns",
        "--containall",
        "--no-home",
        "--cleanenv",
        "--no-mount bind-paths,home,cwd,sys",
        "--no-privs",
        "--no-eval",
        "--net --network none",
        f"--bind {tmp_path / 'w'}:/work:ro",
        f"--bind {tmp_path / 'o'}:/out",
        f"--bind {tmp_path / 's'}:/dev/shm:ro",
        "--pwd /work",
        "--env PYTHONHASHSEED=0",
        "--env HYPOTHESIS_STORAGE_DIRECTORY=/tmp/.hypothesis",
    ]:
        assert flag in joined, flag
    # The image is the SIF file; the limits are the wrapper's first three
    # arguments (processes, KiB, 512-byte blocks); the command comes last.
    image = cmd.index(str(tmp_path / "x.sif"))
    assert cmd[image + 1 : image + 3] == ["sh", "-c"]
    assert cmd[image + 4 : image + 8] == ["sandbox-wrapper", "64", str(128 * 1024), "2048"]
    assert cmd[-2:] == ["python", "x.py"]


@pytest.mark.parametrize(
    ("text", "size"),
    [("512m", 512 << 20), ("64M", 64 << 20), ("1g", 1 << 30), ("8k", 8192), ("4096", 4096),
     ("64mb", 64 << 20)],
)  # fmt: skip
def test_parse_size(text, size):
    assert parse_size(text) == size


@pytest.mark.parametrize("text", ["", "m", "1.5g", "12x", "-1m"])
def test_unreadable_size_raises(text):
    with pytest.raises(SandboxError, match="unreadable size"):
        parse_size(text)


@pytest.mark.parametrize(
    ("timed_out", "exit_code", "memory_error", "status"),
    [
        (False, 0, False, "ok"),
        (False, 1, False, "nonzero_exit"),
        (True, 137, False, "timeout"),
        (False, 137, False, "infra_error"),  # SIGKILL that no timeout explains
        # pytest finished (exit 1) and wrote a report: its detail is kept.
        (False, 1, True, "nonzero_exit"),
        # INTERNALERROR, a collection error or any other exit: memory.
        (False, 3, True, "oom"),
        (False, 2, True, "oom"),
        (False, 120, True, "oom"),
        (False, 0, True, "ok"),  # a program that caught its MemoryError
        (False, 3, False, "nonzero_exit"),
    ],
)
def test_status_of(timed_out, exit_code, memory_error, status):
    assert status_of(timed_out, exit_code, memory_error) == status


@pytest.mark.parametrize(
    ("content", "expected"),
    [(b"0 -\n", 0), (b"3 -\n", 3), (None, None), (b"", None), (b"x -", None)],
)
def test_wrapper_exit_parsing_never_raises(content, expected):
    assert _wrapper_exit(content) == expected


def test_image_id_is_the_prefixed_sha256_of_the_file(tmp_path):
    sif = tmp_path / "x.sif"
    sif.write_bytes(b"not really an image")
    runner = ApptainerRunner(sandbox_cfg(), sif)
    assert (
        runner.existing_image_id()
        == "apptainer:sha256:" + hashlib.sha256(sif.read_bytes()).hexdigest()
    )
    assert IMAGE_ID_PREFIX == "apptainer:sha256:"  # part of every result key: never change it
    assert ApptainerRunner(sandbox_cfg(), tmp_path / "missing.sif").existing_image_id() is None


def test_def_file_and_dockerfile_pin_the_same_image():
    context = ROOT / "docker" / "sandbox"
    dockerfile = (context / "Dockerfile").read_text()
    definition = (context / "sandbox.def").read_text()

    def digest(text):
        return re.findall(
            r"^FROM:?\s+\S*@(sha256:[0-9a-f]{64})", text, re.MULTILINE | re.IGNORECASE
        )

    def packages(text):
        return sorted(re.findall(r"\b([\w.-]+==[\w.]+)", text))

    assert digest(dockerfile) and digest(dockerfile) == digest(definition)
    assert packages(dockerfile) and packages(dockerfile) == packages(definition)


def test_make_runner_picks_the_configured_runtime(tmp_path):
    cfg = load_config(ROOT / "configs" / "mock.yaml")
    assert isinstance(make_runner(cfg), SandboxRunner)
    apptainer = dataclasses.replace(
        cfg,
        execution=dataclasses.replace(
            cfg.execution, sandbox_runtime="apptainer", apptainer_image=tmp_path / "x.sif"
        ),
    )
    runner = make_runner(apptainer)
    assert isinstance(runner, ApptainerRunner) and runner.sif == tmp_path / "x.sif"


def test_missing_image_without_build_context_raises(tmp_path):
    runner = ApptainerRunner(sandbox_cfg(build_context=None), tmp_path / "x.sif")
    with pytest.raises(SandboxError, match="no build_context"):
        runner.ensure_image()


# --- with Apptainer ---------------------------------------------------------

pytestmark_apptainer = pytest.mark.apptainer


@pytest.fixture(scope="module")
def runner():
    r = ApptainerRunner(sandbox_cfg(), SIF)
    r.ensure_image()
    yield r


def leftover(marker: str) -> list[int]:
    """This user's processes whose command line contains marker."""
    found = []
    for pid in _processes():
        try:
            if marker.encode() in Path(f"/proc/{pid}/cmdline").read_bytes():
                found.append(pid)
        except OSError:
            pass
    return found


@pytest.fixture(autouse=True)
def no_leftover_helpers(request):
    yield
    if "apptainer" in request.keywords:
        # A helper that outlived its run is exactly what sweep() removes.
        assert ApptainerRunner(sandbox_cfg(), SIF).sweep() == 0, (
            "a squashfuse helper was left behind"
        )


@pytestmark_apptainer
def test_successful_run(runner):
    result = runner.run(py("print('hello'); import sys; print('err', file=sys.stderr)"))
    assert (result.status, result.exit_code) == ("ok", 0)
    assert result.stdout == "hello\n" and result.stderr == "err\n"
    assert not result.stdout_truncated


@pytestmark_apptainer
def test_nonzero_exit(runner):
    result = runner.run(py("raise SystemExit(3)"))
    assert (result.status, result.exit_code) == ("nonzero_exit", 3)


@pytestmark_apptainer
def test_syntax_error_is_a_program_failure_not_an_infra_error(runner):
    result = runner.run(py("def broken(:\n"))
    assert result.status == "nonzero_exit"
    assert "SyntaxError" in result.stderr


@pytestmark_apptainer
def test_pytest_report_comes_back_through_out(runner):
    files = {
        "calc.py": b"def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": (
            b"from hypothesis import given, strategies as st\nfrom calc import add\n\n"
            b"@given(st.integers(), st.integers())\ndef test_add(a, b):\n"
            b"    assert add(a, b) == add(b, a)\n"
        ),
    }
    result = runner.run(RunRequest(files=files, command=PYTEST))
    assert result.status == "ok", result.stdout + result.stderr
    assert b'tests="1"' in result.out_files["report.xml"]


@pytestmark_apptainer
def test_timeout_kills_the_run(runner):
    result = runner.run(py("while True:\n    pass\n", timeout_s=3))
    assert result.status == "timeout"
    assert 3 <= result.wall_s < 15


@pytestmark_apptainer
def test_output_printed_before_a_timeout_is_kept(runner):
    result = runner.run(py("import time\nprint('started')\ntime.sleep(60)\n", timeout_s=3))
    assert result.status == "timeout"
    assert result.stdout == "started\n"


@pytestmark_apptainer
@pytest.mark.parametrize("ignore_term", [False, True])
def test_timeout_kills_escaped_children_and_the_helper(runner, ignore_term):
    # A child in its own session escapes the process group; it must still
    # die, and the squashfuse helper must not outlive the run (checked by
    # the autouse fixture).
    marker = f"escaped-{uuid.uuid4().hex[:8]}"
    code = (
        "import signal, subprocess, time\n"
        + ("signal.signal(signal.SIGTERM, signal.SIG_IGN)\n" if ignore_term else "")
        + f"subprocess.Popen(['python', '-c', 'import time; time.sleep(600)', '{marker}'],"
        " start_new_session=True)\n"
        "while True:\n    pass\n"
    )
    result = runner.run(py(code, timeout_s=3))
    assert result.status == "timeout"
    time.sleep(1)
    assert leftover(marker) == []


@pytestmark_apptainer
def test_background_processes_die_with_the_run(runner):
    marker = f"background-{uuid.uuid4().hex[:8]}"
    code = (
        "import subprocess\n"
        f"subprocess.Popen(['python', '-c', 'import time; time.sleep(600)', '{marker}'])\n"
        "print('bye')\n"
    )
    result = runner.run(py(code))
    assert (result.status, result.stdout) == ("ok", "bye\n")
    assert result.wall_s < 15
    time.sleep(1)
    assert leftover(marker) == []


@pytestmark_apptainer
def test_memory_limit_gives_memory_error(runner):
    # 128 MB of address space; a 1 GB allocation fails inside the program.
    # A plain uncaught MemoryError exits 1, which keeps nonzero_exit.
    result = runner.run(py("x = bytearray(1 << 30)\nprint('survived')\n"))
    assert (result.status, result.exit_code) == ("nonzero_exit", 1)
    assert "MemoryError" in result.stderr and "survived" not in result.stdout


@pytestmark_apptainer
def test_memory_overrun_in_a_test_keeps_the_report(runner):
    files = {"tests/test_m.py": b"def test_m():\n    x = bytearray(1 << 30)\n"}
    result = runner.run(RunRequest(files=files, command=PYTEST))
    assert (result.status, result.exit_code) == ("nonzero_exit", 1)
    assert b'failures="1"' in result.out_files["report.xml"]


@pytestmark_apptainer
def test_memory_overrun_outside_a_test_is_oom(runner):
    # At import during collection: pytest exits 2, so this is the program's
    # memory overrun, not a harness problem.
    files = {
        "big.py": b"x = bytearray(1 << 30)\n",
        "tests/test_b.py": b"import big\n\ndef test_b():\n    pass\n",
    }
    result = runner.run(RunRequest(files=files, command=PYTEST))
    assert (result.status, result.exit_code) == ("oom", 2)


@pytestmark_apptainer
def test_process_limit_contains_a_fork_bomb(runner):
    code = (
        "import subprocess\n"
        "procs = []\n"
        "try:\n"
        "    for _ in range(1000):\n"
        "        procs.append(subprocess.Popen(['sleep', '60']))\n"
        "except OSError:\n"
        "    pass\n"
        "print(len(procs))\n"
    )
    result = runner.run(py(code))
    assert result.status == "ok", result.stderr
    assert 0 < int(result.stdout) < 64  # stopped by pids_limit, not by the loop


@pytestmark_apptainer
def test_a_fork_bomb_does_not_starve_another_run(runner):
    # The limit counts each run's own processes (one user namespace each),
    # so a run at its limit leaves the others theirs.
    bomb = py(
        "import subprocess, time\nprocs = []\ntry:\n    for _ in range(1000):\n"
        "        procs.append(subprocess.Popen(['sleep', '60']))\n"
        "except OSError:\n    pass\ntime.sleep(6)\n"
    )
    late = py(
        "import subprocess, time\ntime.sleep(3)\n"
        "procs = [subprocess.Popen(['sleep', '5']) for _ in range(40)]\nprint(len(procs))\n"
    )
    results = {}
    bombs = [
        threading.Thread(target=lambda i=i: results.update({i: runner.run(bomb)})) for i in range(3)
    ]
    for t in bombs:
        t.start()
    other = runner.run(late)
    for t in bombs:
        t.join()
    assert (other.status, other.stdout) == ("ok", "40\n"), other.stderr
    assert all(r.status == "ok" for r in results.values())


@pytestmark_apptainer
def test_network_is_blocked(runner):
    code = (
        "import socket\n"
        "print(sorted(n for _, n in socket.if_nameindex()))\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        "    print('connected')\n"
        "except OSError as exc:\n"
        "    print('blocked', type(exc).__name__)\n"
    )
    result = runner.run(py(code))
    interfaces, outcome = result.stdout.splitlines()
    assert interfaces == "['lo']"
    assert outcome.startswith("blocked"), outcome


@pytestmark_apptainer
def test_filesystem_is_read_only_except_tmp_and_out(runner):
    code = (
        "import os\n"
        "paths = ['/work/x', '/etc/x', '/usr/x', '/dev/shm/x', '/tmp/x', '/var/tmp/x', '/out/x']\n"
        "for path in paths:\n"
        "    try:\n"
        "        open(path, 'w').write('x')\n"
        "        print(path, 'writable')\n"
        "    except OSError:\n"
        "        print(path, 'read-only')\n"
    )
    result = runner.run(py(code))
    assert result.stdout.splitlines() == [
        "/work/x read-only",
        "/etc/x read-only",
        "/usr/x read-only",
        "/dev/shm/x read-only",
        "/tmp/x writable",
        "/var/tmp/x writable",
        "/out/x writable",
    ]


@pytestmark_apptainer
def test_host_paths_are_not_visible(runner):
    paths = ["/fs", str(Path.home()), str(ROOT), str(SIF.parent), "/sys/kernel", "/nfshomes"]
    code = (
        f"import os\nprint([p for p in {paths!r} if os.path.exists(p)])\n"
        "print(sorted({l.split()[1] for l in open('/proc/self/mounts')}))\n"
    )
    result = runner.run(py(code))
    visible, mounts = result.stdout.splitlines()
    assert visible == "[]"
    # Only the image, the kernel's pseudo-filesystems, the tmpfs, the user
    # files Apptainer writes, and our three binds.
    assert set(eval(mounts)) <= {
        "/", "/dev", "/dev/shm", "/dev/mqueue", "/dev/pts", "/dev/tty", "/dev/null",
        "/dev/zero", "/dev/random", "/dev/urandom", "/proc", "/tmp", "/var/tmp",
        "/etc/passwd", "/etc/group", "/out", "/work",
    }  # fmt: skip


@pytestmark_apptainer
def test_runs_unprivileged_without_capabilities(runner):
    code = (
        "import os\n"
        "print(os.getuid(), os.getgid())\n"
        "status = dict(l.split(':\\t', 1) for l in open('/proc/self/status'))\n"
        "print(status['CapEff'].strip(), status['CapBnd'].strip(), status['NoNewPrivs'].strip())\n"
    )
    result = runner.run(py(code))
    uid, gid, cap_eff, cap_bnd, no_new_privs = result.stdout.split()
    assert (uid, gid) == (str(os.getuid()), str(os.getgid())) and uid != "0"
    assert cap_eff == cap_bnd == "0000000000000000"
    assert no_new_privs == "1"


@pytestmark_apptainer
def test_environment_matches_docker(runner):
    result = runner.run(
        py("import os\nfor k in sorted(os.environ):\n    print(k, os.environ[k])\n")
    )
    env = dict(line.split(" ", 1) for line in result.stdout.splitlines())
    # Docker's: the image's own ENV, plus HOME and ours. PWD is set by sh.
    assert sorted(env) == sorted([
        "GPG_KEY", "LANG", "PATH", "PYTHON_SHA256", "PYTHON_VERSION",
        "HOME", "PWD", "PYTHONDONTWRITEBYTECODE", "PYTHONUNBUFFERED", "PYTHONHASHSEED",
        "HYPOTHESIS_STORAGE_DIRECTORY",
    ])  # fmt: skip
    assert (env["HOME"], env["PWD"], env["PYTHONHASHSEED"]) == ("/tmp", "/work", "0")


@pytestmark_apptainer
def test_tmpfs_and_file_size_limits():
    runner = ApptainerRunner(sandbox_cfg(file_size_limit_bytes=1024 * 1024), SIF)
    code = (
        "def write(path, mb):\n"
        "    try:\n"
        "        with open(path, 'wb') as f:\n"
        "            for _ in range(mb):\n"
        "                f.write(b'x' * (1 << 20))\n"
        "        return 'ok'\n"
        "    except OSError as exc:\n"
        "        return type(exc).__name__\n"
        "fill = [write(f'/tmp/f{i}', 1) for i in range(80)]\n"  # 1 MiB each, 64 MiB tmpfs
        "print(write('/out/small', 1), write('/out/big', 4), fill[0], fill[-1])\n"
    )
    result = runner.run(py(code))
    ok, too_big_file, first, last = result.stdout.split()
    assert ok == first == "ok"
    assert too_big_file == "OSError"  # EFBIG: over file_size_limit_bytes
    assert last == "OSError"  # ENOSPC: /tmp holds only 64 MiB
    assert len(result.out_files["big"]) <= 1024 * 1024


@pytestmark_apptainer
def test_probe_refuses_a_tmpfs_size_apptainer_cannot_give():
    runner = ApptainerRunner(sandbox_cfg(tmpfs_size="8m"), SIF)
    with pytest.raises(SandboxError, match="tmpfs_size is 8m"):
        runner.ensure_image()


@pytestmark_apptainer
def test_unexplained_exit_137_is_an_infra_error(runner):
    for code in [
        "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n",
        "raise SystemExit(137)\n",
    ]:
        result = runner.run(py(code))
        assert result.status == "infra_error"
        assert result.infra_cause == "unexplained_sigkill"


@pytestmark_apptainer
def test_status_file_is_not_returned_as_program_output(runner):
    result = runner.run(py("print('hi')"))
    assert result.out_files == {}


@pytestmark_apptainer
def test_a_forged_status_file_is_an_infra_error(runner):
    # The program writes a success status and kills the wrapper before it
    # can write the real one.
    code = (
        "import os, signal\n"
        "open('/out/.sandbox_exit', 'w').write('0 -')\n"
        "os.kill(os.getppid(), signal.SIGKILL)\n"
    )
    result = runner.run(py(code))
    assert result.status == "infra_error"
    assert result.infra_cause in ("status_mismatch", "unexplained_sigkill")


@pytestmark_apptainer
def test_output_is_capped(runner):
    result = runner.run(py("import sys\nsys.stdout.write('y' * 1_000_000)\n"))
    assert result.status == "ok"
    assert result.stdout == "y" * 4096 and result.stdout_truncated


@pytestmark_apptainer
def test_memory_error_after_long_output_is_still_seen(runner):
    # The message is past the output cap; the reader's tail still has it.
    code = (
        "import sys\nprint('y' * 100_000)\n"
        "try:\n    bytearray(1 << 30)\n"
        "except MemoryError as exc:\n    print(type(exc).__name__)\n    sys.exit(3)\n"
    )
    result = runner.run(py(code))
    assert result.stdout_truncated and "MemoryError" not in result.stdout + result.stderr
    assert (result.status, result.exit_code) == ("oom", 3)


@pytestmark_apptainer
def test_hash_seed_is_fixed_so_runs_are_reproducible(runner):
    code = "print(hash('record_store'), list({'a', 'b', 'c', 'd'}))\n"
    assert runner.run(py(code)).stdout == runner.run(py(code)).stdout


@pytestmark_apptainer
def test_symlinks_in_out_are_not_followed(runner):
    code = (
        "import os\n"
        "os.symlink('/etc/passwd', '/out/leak')\n"
        "os.mkdir('/out/d')\n"
        "open('/out/d/f', 'w').write('ok')\n"
    )
    result = runner.run(py(code))
    assert result.out_files == {"d/f": b"ok"}


@pytestmark_apptainer
def test_a_broken_image_fails_at_start_up(tmp_path):
    broken = tmp_path / "broken.sif"
    broken.write_bytes(b"not an image")
    with pytest.raises(SandboxError, match="probe failed"):
        ApptainerRunner(sandbox_cfg(), broken).ensure_image()


@pytestmark_apptainer
def test_a_replaced_image_is_an_infra_error(tmp_path):
    sif = tmp_path / "copy.sif"
    shutil.copyfile(SIF, sif)
    runner = ApptainerRunner(sandbox_cfg(), sif)
    runner.ensure_image()
    os.utime(sif, ns=(time.time_ns(), time.time_ns()))
    result = runner.run(py("print(1)"))
    assert (result.status, result.infra_cause) == ("infra_error", "image_changed")


@pytestmark_apptainer
def test_image_id_is_the_sif_hash(runner):
    digest = hashlib.sha256(SIF.read_bytes()).hexdigest()
    assert runner.image_id == f"apptainer:sha256:{digest}"


@pytestmark_apptainer
def test_sweep_kills_a_helper_left_by_a_crashed_run(runner, tmp_path):
    # A crash leaves the helper running: kill only the run's process group,
    # as an outside kill of the harness would.
    work, out, shm = tmp_path / "w", tmp_path / "o", tmp_path / "s"
    for d in (work, out, shm):
        d.mkdir()
    (work / "main.py").write_text("while True:\n    pass\n")
    cmd = runner.create_command(work, out, shm, ["python", "main.py"], timeout=20)
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)  # fmt: skip
    time.sleep(2)
    os.killpg(proc.pid, signal.SIGKILL)
    proc.wait()
    time.sleep(1)
    assert runner.sweep() == 1
    assert runner.sweep() == 0


@pytestmark_apptainer
def test_record_store_reference_passes_its_public_checks(runner):
    from harness.registry import load_tasks

    cfg = load_config(ROOT / "configs" / "mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    files = {**task.reference, **{f.path: f.content for f in task.public_checks}}
    command = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               *[f.path for f in task.public_checks]]  # fmt: skip
    result = runner.run(RunRequest(files=files, command=command))
    assert result.status == "ok", result.stdout + result.stderr
    assert re.search(r"\b\d+ passed", result.stdout) and "failed" not in result.stdout


@pytestmark_apptainer
@pytest.mark.slow
def test_parallel_runs_are_reliable():
    from concurrent.futures import ThreadPoolExecutor

    runner = ApptainerRunner(sandbox_cfg(), SIF)
    runner.ensure_image()
    files = {
        "calc.py": b"def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": (
            b"from hypothesis import given, strategies as st\nfrom calc import add\n\n"
            b"@given(st.integers(), st.integers())\ndef test_add(a, b):\n"
            b"    assert add(a, b) == add(b, a)\n"
        ),
    }
    with ThreadPoolExecutor(6) as pool:
        results = list(pool.map(runner.run, [RunRequest(files=files, command=PYTEST)] * 36))
    assert [r.status for r in results] == ["ok"] * 36
