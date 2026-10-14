"""Unit tests for pipeline.runner, the Docker sandbox.

The first group checks the container command line, path validation and the
output cap without Docker. The `docker` group runs real containers: success,
errors, timeouts, memory and process limits, network and filesystem
isolation, output caps and cleanup. After every Docker test, a fixture
checks that no container from this test session is left behind.

Usage:
    uv run pytest tests/test_runner.py -rs        # Docker tests skip without a daemon
    uv run pytest tests/test_runner.py -m docker  # only the Docker tests
"""

import dataclasses
import io
import os
import uuid
from pathlib import Path

import pytest

from pipeline.config import load_config
from pipeline.runner import LABEL, RunRequest, SandboxRunner, _CappedReader, _docker

PILOT = Path(__file__).resolve().parents[1]
SESSION_OWNER = f"pytest-{uuid.uuid4().hex[:8]}"


def sandbox_cfg(**overrides):
    base = load_config(PILOT / "configs" / "pilot_mock.yaml").sandbox
    small = dict(timeout_s=20.0, memory="128m", pids_limit=64, output_cap_bytes=4096)
    return dataclasses.replace(base, **{**small, **overrides})


def py(code: str, timeout_s: float | None = None) -> RunRequest:
    return RunRequest(files={"main.py": code.encode()}, command=["python", "main.py"],
                      timeout_s=timeout_s)  # fmt: skip


# --- without Docker ---------------------------------------------------------


def test_create_command_has_every_isolation_flag(tmp_path):
    runner = SandboxRunner(sandbox_cfg(), owner="o")
    runner._image_id = "sha256:abc"  # skip resolving the image
    cmd = runner.create_command("n", tmp_path / "w", tmp_path / "o", ["python", "x.py"])
    joined = " ".join(cmd)
    for flag in [
        "--pull never",
        "--network none",
        f"--user {os.getuid()}:{os.getgid()}",
        "--cap-drop ALL",
        "--security-opt no-new-privileges",
        "--read-only",
        "--memory 128m --memory-swap 128m",
        "--pids-limit 64",
        "--log-driver none",
        "--init",
        f"--label {LABEL}.owner=o",
        "dst=/work,readonly",
        "PYTHONDONTWRITEBYTECODE=1",
    ]:
        assert flag in joined, flag
    # The image is pinned by content id; the program's command runs under the
    # OOM-recording wrapper and comes last.
    image = cmd.index("sha256:abc")
    assert cmd[image + 1 : image + 3] == ["sh", "-c"]
    assert cmd[-2:] == ["python", "x.py"]


@pytest.mark.parametrize("name", ["/etc/x", "../x", "a/../../x", "a\\b", "./a", "", "a//b"])
def test_unsafe_file_paths_are_rejected_before_docker(name):
    runner = SandboxRunner(sandbox_cfg(), owner="o")
    with pytest.raises(ValueError, match="unsafe path"):
        runner.run(RunRequest(files={name: b""}, command=["true"]))


def test_capped_reader_keeps_the_first_bytes_and_drains_the_rest():
    stream = io.BufferedReader(io.BytesIO(b"x" * 100_000 + b"END"))
    reader = _CappedReader(stream, cap=10)
    reader.join()
    assert reader.data == b"x" * 10
    assert reader.truncated
    assert stream.closed  # read to the end, so a real writer never blocks


# --- with Docker ------------------------------------------------------------


@pytest.fixture(scope="module")
def runner():
    r = SandboxRunner(sandbox_cfg(), owner=SESSION_OWNER)
    r.ensure_image()
    yield r
    r.sweep()


@pytest.fixture(autouse=True)
def no_leftover_containers(request):
    yield
    if "docker" in request.keywords:
        left = _docker(["ps", "-aq", "--filter", f"label={LABEL}.owner={SESSION_OWNER}"])
        assert left.stdout.split() == [], "a sandbox container was left behind"


pytestmark_docker = pytest.mark.docker


@pytestmark_docker
def test_successful_run(runner):
    result = runner.run(py("print('hello'); import sys; print('err', file=sys.stderr)"))
    assert (result.status, result.exit_code) == ("ok", 0)
    assert result.stdout == "hello\n" and result.stderr == "err\n"
    assert not result.stdout_truncated


@pytestmark_docker
def test_nonzero_exit(runner):
    result = runner.run(py("raise SystemExit(3)"))
    assert (result.status, result.exit_code) == ("nonzero_exit", 3)


@pytestmark_docker
def test_syntax_error_is_a_program_failure_not_an_infra_error(runner):
    result = runner.run(py("def broken(:\n"))
    assert result.status == "nonzero_exit"
    assert "SyntaxError" in result.stderr


@pytestmark_docker
def test_pytest_report_comes_back_through_out(runner):
    files = {
        "calc.py": b"def add(a, b):\n    return a + b\n",
        "tests/test_calc.py": (
            b"from calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n"
        ),
    }
    command = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               "--junitxml=/out/report.xml", "tests"]  # fmt: skip
    result = runner.run(RunRequest(files=files, command=command))
    assert result.status == "ok", result.stdout + result.stderr
    assert b'tests="1"' in result.out_files["report.xml"]


@pytestmark_docker
def test_timeout_kills_the_container(runner):
    result = runner.run(py("while True:\n    pass\n", timeout_s=3))
    assert result.status == "timeout"
    assert 3 <= result.wall_s < 15


@pytestmark_docker
def test_output_printed_before_a_timeout_is_kept(runner):
    result = runner.run(py("import time\nprint('started')\ntime.sleep(60)\n", timeout_s=3))
    assert result.status == "timeout"
    assert result.stdout == "started\n"


@pytestmark_docker
def test_memory_limit_is_enforced(runner):
    # 128 MB container; touching 1 GB gets the process OOM-killed.
    result = runner.run(py("x = bytearray(1 << 30)\nprint('survived')\n"))
    assert result.status == "oom"
    assert "survived" not in result.stdout


@pytestmark_docker
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
    assert 0 < int(result.stdout) < 64  # stopped by --pids-limit, not by the loop


@pytestmark_docker
def test_background_processes_die_with_the_container(runner):
    # The program leaves a child running and exits; removing the container
    # must kill it (the leftover-container fixture checks the removal).
    code = "import subprocess\nsubprocess.Popen(['sleep', '600'])\nprint('bye')\n"
    result = runner.run(py(code))
    assert result.status == "ok"
    assert result.wall_s < 15


@pytestmark_docker
def test_network_is_blocked(runner):
    code = (
        "import socket\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=3)\n"
        "    print('connected')\n"
        "except OSError as exc:\n"
        "    print('blocked', type(exc).__name__)\n"
    )
    result = runner.run(py(code))
    assert result.stdout.startswith("blocked"), result.stdout


@pytestmark_docker
def test_filesystem_is_read_only_except_tmp_and_out(runner):
    code = (
        "import os\n"
        "for path in ['/work/x', '/etc/x', '/usr/x', '/tmp/x', '/out/x']:\n"
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
        "/tmp/x writable",
        "/out/x writable",
    ]


@pytestmark_docker
def test_runs_unprivileged_without_capabilities(runner):
    code = (
        "import os\n"
        "print(os.getuid(), os.getgid())\n"
        "print([l for l in open('/proc/self/status') if l.startswith('CapEff')][0].split()[1])\n"
    )
    result = runner.run(py(code))
    expected_uid = "65534" if os.getuid() == 0 else str(os.getuid())
    uid, _, capabilities = result.stdout.split()
    assert uid == expected_uid and uid != "0"
    assert capabilities == "0000000000000000"


@pytestmark_docker
def test_tmpfs_and_file_size_limits(tmp_path):
    runner = SandboxRunner(
        sandbox_cfg(tmpfs_size="8m", file_size_limit_bytes=1024 * 1024), owner=SESSION_OWNER
    )
    code = (
        "def write(path, mb):\n"
        "    try:\n"
        "        with open(path, 'wb') as f:\n"
        "            for _ in range(mb):\n"
        "                f.write(b'x' * (1 << 20))\n"
        "        return 'ok'\n"
        "    except OSError as exc:\n"
        "        return type(exc).__name__\n"
        "print(write('/tmp/a', 1), write('/out/big', 4), write('/tmp/b', 20))\n"
    )
    result = runner.run(py(code))
    ok, too_big_file, tmpfs_full = result.stdout.split()
    assert ok == "ok"
    assert too_big_file == "OSError"  # EFBIG: over file_size_limit_bytes
    assert tmpfs_full == "OSError"  # ENOSPC/EFBIG: /tmp holds only 8 MB
    assert len(result.out_files["big"]) <= 1024 * 1024


@pytestmark_docker
def test_memory_limit_status_comes_from_docker_oom_flag(runner):
    # Same exit code (137) as an outside kill; only Docker's OOMKilled flag
    # makes it "oom".
    result = runner.run(py("x = bytearray(1 << 30)\n"))
    assert (result.status, result.exit_code) == ("oom", 137)


@pytestmark_docker
@pytest.mark.parametrize(
    "code",
    [
        "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n",
        # Indistinguishable from a kill, so also treated as infrastructure.
        "raise SystemExit(137)\n",
    ],
)
def test_unexplained_exit_137_is_an_infra_error(runner, code):
    result = runner.run(py(code))
    assert result.status == "infra_error"
    assert "exit 137" in result.detail


@pytestmark_docker
def test_oom_is_detected_under_parallel_load():
    # Docker's OOMKilled flag alone missed about 1 in 10 OOM kills with 8
    # containers running; the kernel counter recorded by the wrapper must not.
    from concurrent.futures import ThreadPoolExecutor

    runner = SandboxRunner(sandbox_cfg(memory="128m"), owner=SESSION_OWNER)
    hog = py("x = bytearray(1 << 30)\n")
    busy = py("import time\ntime.sleep(1)\n")
    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(runner.run, [hog, busy] * 16))
    assert [r.status for r in results[0::2]] == ["oom"] * 16
    assert [r.status for r in results[1::2]] == ["ok"] * 16


@pytestmark_docker
def test_status_file_is_not_returned_as_program_output(runner):
    result = runner.run(py("print('hi')"))
    assert result.out_files == {}


@pytestmark_docker
def test_output_is_capped(runner):
    result = runner.run(py("import sys\nsys.stdout.write('y' * 1_000_000)\n"))
    assert result.status == "ok"
    assert result.stdout == "y" * 4096 and result.stdout_truncated


@pytestmark_docker
def test_hash_seed_is_fixed_so_runs_are_reproducible(runner):
    code = "print(hash('record_store'), list({'a', 'b', 'c', 'd'}))\n"
    assert runner.run(py(code)).stdout == runner.run(py(code)).stdout


@pytestmark_docker
def test_symlinks_in_out_are_not_followed(runner):
    code = (
        "import os\n"
        "os.symlink('/etc/passwd', '/out/leak')\n"
        "os.mkdir('/out/d')\n"
        "open('/out/d/f', 'w').write('ok')\n"
    )
    result = runner.run(py(code))
    assert result.out_files == {"d/f": b"ok"}


@pytestmark_docker
def test_missing_image_is_an_infra_error(runner):
    broken = SandboxRunner(sandbox_cfg(), owner=SESSION_OWNER)
    broken._image_id = "pipeline-sandbox:does-not-exist"
    result = broken.run(py("print(1)"))
    assert result.status == "infra_error"
    assert "docker create failed" in result.detail


@pytestmark_docker
def test_sweep_removes_only_this_owners_containers(runner):
    mine = f"{SESSION_OWNER}-sweep"
    other = f"{SESSION_OWNER}x-other"
    for owner in (mine, other):
        _docker(["create", "--label", f"{LABEL}.owner={owner}", runner.image_id, "true"])
    assert SandboxRunner(sandbox_cfg(), owner=mine).sweep() == 1
    assert SandboxRunner(sandbox_cfg(), owner=other).sweep() == 1


@pytestmark_docker
def test_image_id_is_the_content_id(runner):
    assert runner.image_id.startswith("sha256:")
    inspect = _docker(["image", "inspect", "--format", "{{.Id}}", runner.cfg.image])
    assert inspect.stdout.strip() == runner.image_id


@pytestmark_docker
def test_record_store_reference_passes_its_public_checks(runner):
    from pipeline.registry import load_tasks

    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    files = {**task.reference, **{f.path: f.content for f in task.public_checks}}
    command = ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
               *[f.path for f in task.public_checks]]  # fmt: skip
    result = runner.run(RunRequest(files=files, command=command))
    assert result.status == "ok", result.stdout + result.stderr
    assert "3 passed" in result.stdout
