# Design: an Apptainer runtime for the sandbox runner

Status: implemented in `src/harness/sandbox/apptainer.py` (2026-10-29),
tests in `tests/sandbox/test_apptainer.py`. The final design is the
"Implemented" section at the end; the sections before it record how we
got there.

## Decisions (review of 2026-10-28)

1. A nonzero exit with `MemoryError` in the output becomes `oom` **only
   when the exit code is not 1**. Exit 1 means pytest finished and wrote a
   report, and its per-test detail is kept.
2. Process limit: at wrapper start, set RLIMIT_NPROC to the user's current
   process+thread count + 256. dash spells this `ulimit -p`, not `-u`.
3. Memory: `ulimit -v` and `ulimit -d` were both measured (results below).
4. Image id: `apptainer:sha256:<hex>`. It is part of the keys, so it never
   changes.
5. `tmpfs_size` ≠ the session tmpfs size: fail at start-up.
6. Branch: `apptainer-sandbox` off main.

## Measurements (2026-10-29, tron54, 4 CPUs, setuid mode)

Scripts and raw output are in `runs/measure/` (gitignored).

| Item | Result |
|---|---|
| 1. Unprivileged build | works: root-mapped namespace + `fakeroot`, 17 s, 52 MiB SIF. Apptainer rejects `tag@digest`, so the def file uses `python@sha256:<same digest>` |
| 2. Start-up | 0.09 s per `apptainer exec` (median of 10) |
| 3. Memory | pytest + Hypothesis runs under `ulimit -v 64m` and `ulimit -d 64m` (fails at 32m for both). At 512m, a 1 GiB bytearray and a growing list both end in `MemoryError` (exit 1), and a test that exhausts memory gives pytest exit 1 **with** a report. `-v` and `-d` behaved the same in every case |
| 4. Kill at timeout | a `setsid()` child is gone after the timeout's `killpg`. A background child left at normal exit is gone too, and `exec` returns at once (0.2 s) |
| 5. Visibility | `/fs`, `/fs/classhomes`, `$HOME` and `/nfshomes` are absent. `/etc/hosts` is empty (the host's is not bound). `/etc/localtime` is the image's own file. Mounts: only `/work` (ro) and `/out` from the host. uid 19265, CapPrm/CapEff/CapBnd 0, NoNewPrivs 1. Interfaces: `lo` only; connect gives ENETUNREACH. `/etc`, `/usr` and `/work` are read-only |
| 5. /tmp | 64 MiB tmpfs **shared by /tmp and /var/tmp** (40 MiB to each: the second write fails) |
| 5. /dev/shm | **separate tmpfs with no size limit**: wrote 200 MiB. A read-only empty bind over it stops this, but `multiprocessing.Lock()` then fails (EROFS). No task or prompt uses multiprocessing or /dev/shm |
| 6. Environment | Docker's set (the image ENV plus ours), and in addition `APPTAINER_*` and `SINGULARITY_*` (incl. the SIF's host path), `LD_LIBRARY_PATH=/.singularity.d/libs`, `PS1` and `PROMPT_COMMAND` |
| 7. Slurm cgroup | job `memory.max` = the `--mem` value; no `cpu.max`; `pids.max` = max (none) |
| nproc | `ulimit -p (tasks+256)`: a fork bomb stops at 236 processes (BlockingIOError), a thread bomb at 236 threads. 6 workers × 15 pytest runs with a 200-thread "Ollama" hog: 0 failures, median 2.9 s. A fork bomb run during them broke none of the others |
| file size | dash's `ulimit -f` is in 512-byte blocks (confirmed) |

## Second review (2026-10-29): do all the recommendations

- Mount an empty directory read-only over `/dev/shm`.
- Unset the `APPTAINER_*`, `SINGULARITY_*`, `LD_LIBRARY_PATH`, `PS1` and
  `PROMPT_COMMAND` variables in the wrapper, so the environment matches
  Docker's.
- Memory limit: `ulimit -v`.
- Fork bombs: find a way to prevent them, or else document the gap.

### Userns mode (`--userns`): makes the process limit per container

Measured on tron60 and tron54 (`runs/measure/measure3.py`, `measure4.py`).

- **RLIMIT_NPROC becomes per container.** Kernel ucounts count processes
  per user namespace.
  - `ulimit -p 64` (an absolute number, not the user count + 256) let
    pytest pass while the user had 205 processes and threads on the node.
  - A fork bomb under it stopped at 41.
  - A run that forked 100 processes while 4 bombs ran got all 100.
  - 6 workers × 15 pytest runs with a bomb in the middle: 0 failures.
  - So a fixed `ulimit -p` (e.g. `sandbox.pids_limit`, as Docker uses)
    works, and runs can't starve each other.
- **The other guarantees hold.**
  - uid_map is `19265 19265 1`.
  - CapEff and CapBnd are 0, and NoNewPrivs is 1.
  - The only interface is `lo`, and `/tmp` is 64 MiB.
  - `/fs` and `$HOME` are absent.
  - `/work`, `/etc` and `/usr` are read-only.
  - A `setsid()` child is killed at timeout.
  - `/dev/shm` is read-only with the bind.
- **Start-up is 0.12 s.** The SIF is mounted with squashfuse instead of a
  loop device.
- **Userns mounts the host's whole `/sys` tree** (debug, bpf, efivars,
  cgroup, …). `--no-mount sys` removes `/sys` entirely, and pytest +
  Hypothesis still pass (`os.cpu_count()` still works).
- **Problem: one `squashfuse_ll` process is left behind per run killed at
  timeout.**
  - 10 runs killed with `killpg` left 10 of them, mounting
    `/var/lib/apptainer/mnt/session/rootfs`.
  - No `sleep` children and no host-visible mounts were left.
  - Slurm removes them when the job ends, but a long collect would pile
    them up.
- **Next step:** find a clean kill that lets Apptainer tear down
  squashfuse. Option: SIGTERM the starter first, wait a moment, then
  SIGKILL the group. Or reap leftovers by tracking the squashfuse PIDs.
  Then decide userns (per-container nproc) vs setuid (user-wide nproc,
  documented gap).
- **Seen in passing:** a missing bind source gives exit 255, `FATAL`, and
  no status file. That is the planned `infra_error` (`apptainer_start`)
  path.

## Why

The sandbox runner (`src/harness/sandbox/runner.py`) calls the `docker` CLI.
The Nexus cluster has no Docker, and Podman fails there (the account has no
`/etc/subuid` entry). Apptainer 1.5.5 works. This adds Apptainer as a second
runtime and leaves the Docker path unchanged.

Facts about the install (read from `/etc/apptainer/apptainer.conf` and
`/usr/libexec/apptainer/bin`):

- `allow setuid = yes`, and `starter-suid` is installed. Runs therefore use
  setuid mode by default: no user namespace, and the SIF is mounted by the
  kernel through a loop device, so start-up is fast.
- `sessiondir max size = 64` and `memory fs type = tmpfs`. With `--contain`,
  `/tmp` lives in this per-run 64 MiB tmpfs.
- `bind path = /etc/localtime` and `bind path = /etc/hosts`. `--no-mount
  bind-paths` drops both. `mount hostfs = no`.
- `systemd cgroups = yes`. Cgroup limits need a systemd user session, which
  jobs don't have.
- `proot` is installed. Apptainer ≥1.3 uses it to build a definition file
  with `%post` when neither root nor subuid fakeroot is available.

## 1. Config and result keys

The `sandbox` section stays exactly as it is, so no existing key changes.
Two fields are added to `ExecutionConfig`:

```yaml
execution:
  sandbox_runtime: apptainer        # docker (default) | apptainer
  apptainer_image: ../runs/images/harness-sandbox_py3.11-v1.sif   # OutputPath; built if missing
```

- `apptainer_image` is required when the runtime is `apptainer` and rejected
  when it is `docker`.
- The SIF is built from `sandbox.build_context/sandbox.def`. That is the same
  directory as the Dockerfile, and the `build_context` path is already part
  of the hash.
- Image id is `sha256:<hex of the SIF file>`, computed once in
  `ensure_image()`.

**The runtime still reaches the keys, through the image id.** The SIF hash can
never equal a Docker image id. Docker and Apptainer results therefore never
share a key, even though the sandbox section and its hash are identical. That
is what we want, because memory and CPU behave differently (see Gaps). One
consequence: on the cluster, initial checks and trials are all recomputed.
Writer programs are keyed without the sandbox, so they are reused. I'll update
the `ExecutionConfig` docstring to say "the runtime affects results only
through the image id".

**Rebuilding the SIF gives a new hash, so it means new results.** Apptainer
builds are not byte-reproducible (timestamps). Build the SIF once and keep it,
just as you would keep a Docker image. It is about 50 MB in the home
directory.

## 2. Image

`docker/sandbox/sandbox.def`:

```
Bootstrap: docker
From: python:3.11-slim@sha256:e88e9763f943ec1834f992a4b51e0f24500486803e8bc534e5767af9ea65f6ce

%post
    pip install --no-cache-dir --no-deps \
        pytest==9.1.1 iniconfig==2.3.1 packaging==26.3 pluggy==1.6.0 pygments==2.21.0 \
        hypothesis==6.169.1 sortedcontainers==2.4.0 \
    && pip check
```

- A unit test parses both files and checks that the base digest and the
  pinned package list are identical, so the two images can't drift apart.
- `ensure_image()` runs `apptainer build <sif>.tmp <def>`, then renames the
  file into place. A half-built file is never hashed.
- After building, and on every start-up, `ensure_image()` does one **probe
  run** that checks the isolation it relies on. If any check fails it raises
  `SandboxError`, so a run fails fast instead of running unisolated. The
  probe checks:
  - uid is not 0
  - CapEff is 0
  - `/tmp` size equals `tmpfs_size`
  - `/fs` and `$HOME` are absent
  - no network interface except `lo`

## 3. The run command

The command is built by `create_command()`, a pure function, so the flags are
unit-tested without Apptainer:

```
timeout --signal=KILL <timeout_s + 30>      # host-side guard, see section 4
apptainer --silent exec
    --containall                             # own PID + IPC + mount ns, clean env, no home, private /tmp
    --no-home --cleanenv                     # already implied by --containall; stated for clarity
    --no-mount bind-paths,home,cwd           # ignore admin bind paths; never bind $HOME or the cwd
    --no-privs                               # drop all capabilities
    --no-eval                                # no shell evaluation of env vars
    --net --network none                     # loopback only
    --bind <work>:/work:ro
    --bind <out>:/out
    --pwd /work
    --env PYTHONDONTWRITEBYTECODE=1 --env PYTHONUNBUFFERED=1 --env PYTHONHASHSEED=0
    --env HYPOTHESIS_STORAGE_DIRECTORY=/tmp/.hypothesis
    <sif>
    sh -c '<wrapper>' sandbox-wrapper <command...>
```

The wrapper sets `HOME=/tmp` (Apptainer refuses to override HOME through
`--env`), then the limits, then runs the program and writes
`/out/.sandbox_exit` as the Docker wrapper does, with `-` for the oom counter:

```sh
export HOME=/tmp; ulimit -v <memory in KiB>; ulimit -f <file_size_limit in 512-byte blocks>;
"$@"; rc=$?; echo "$rc -" > /out/.sandbox_exit; exit "$rc"
```

The limits are set inside the container because the Apptainer starter is a Go
program that reserves a lot of address space and would itself fail under
`ulimit -v`. The unit sizes of dash's `ulimit` (Debian's `/bin/sh`) are
checked by the existing file-size test.

### Docker's guarantees and how each is met

| Guarantee | Docker | Apptainer | Same? |
|---|---|---|---|
| No network | `--network none` | `--net --network none` | yes |
| Non-root | `--user uid:gid` | runs as the calling user (setuid starter drops privileges) | yes |
| No capabilities, no new privileges | `--cap-drop ALL`, `no-new-privileges` | `--no-privs`; Apptainer always sets NO_NEW_PRIVS | yes |
| Read-only root | `--read-only` | SIF squashfs is read-only | yes |
| Code read-only at /work | ro bind | ro bind | yes |
| Writable /out | bind | bind | yes |
| Small /tmp | tmpfs, `size=tmpfs_size`, noexec | session tmpfs, 64 MiB fixed by admin; probe checks it equals `tmpfs_size` | size yes; **not noexec** |
| File-size limit | `--ulimit fsize` | `ulimit -f` | yes |
| Memory limit | cgroup, whole container, RSS | `ulimit -v`, **per process, address space** | **no** (see Gaps) |
| CPU limit | `--cpus` | none; bounded by the timeout and the Slurm job's CPUs | **no** |
| Process limit | `--pids-limit` | none; bounded by the timeout | **no** |
| Time limit kills everything | `docker kill` + `rm -f` | kill the process group; the PID namespace dies with its init (section 4) | yes, if verified |
| Zombie reaping | `--init` (tini) | Apptainer's init shim under `--pid` | yes |
| Clean env, same vars | explicit `--env` | `--cleanenv` + same `--env`; Apptainer adds its own `APPTAINER_*`/`LD_LIBRARY_PATH` | nearly (a test lists the exact set) |
| Host files hidden | only the two binds | `--containall` + `--no-mount bind-paths,home,cwd` | yes; tests check /fs and $HOME |
| Never pulls an image | `--pull never` | runs a local SIF file only | yes |
| Cleanup | `rm -f` | no container objects; temp dirs removed; processes killed | yes |

## 4. Run lifecycle

1. Write the files to a temp dir, as now.
2. `Popen(command, start_new_session=True)`. The run gets its own process
   group. Output is read with the existing `_CappedReader`.
3. Wait for up to `timeout_s`. On timeout, `os.killpg(pgid, SIGKILL)`.
   - That kills `timeout`, the starter and every container process that is
     still in the group.
   - A program that calls `setsid()` leaves the group but stays in the PID
     namespace. When the namespace's init dies, the kernel kills everything
     in it. A test covers exactly this escape.
4. The outer `timeout --signal=KILL` is only a guard for when the harness
   itself dies (crash, Ctrl-C). Nothing then outlives `timeout_s + 30`.
5. Classification uses the same `classify()`, fed with
   `{"ExitCode": rc, "OOMKilled": False, "Error": ...}`:
   - If `/out/.sandbox_exit` is missing and we did not time out, the wrapper
     never ran. Apptainer itself failed (e.g. exit 255 with `FATAL:`), so the
     run is `infra_error` with cause `apptainer_start`.
   - Exit 137 without a timeout stays `infra_error` (`unexplained_sigkill`),
     as with Docker.
6. `sweep()` returns 0. There are no persistent containers to remove, and
   leftovers from a crash are handled by the guard in step 4.
7. `existing_image_id()` hashes the SIF if it exists and never builds.

## 5. Memory exhaustion and the evaluator (needs your decision)

With Docker, a run over the memory limit is OOM-killed as a whole. The status
is `oom`, and the evaluator (evaluator.py:324) turns `timeout`/`oom` into
`failed` with no per-test cases.

With `ulimit -v`, allocation fails inside the program. What we see depends on
where it fails:

- inside a test: pytest records a failed test and exits 1 with a report. That
  is already `failed`, with per-test detail.
- in pytest's own code: INTERNALERROR, exit 3. The evaluator calls this
  `infra_error` (`pytest_harness`), **so the program's fault is not counted
  against it.**
- at start-up or in a subprocess: nonzero exit and no report. The evaluator
  calls this `infra_error` (`missing_report`). **Same problem.**

**Recommendation (A):** in the Apptainer runner, a run with a nonzero exit
whose stderr or stdout contains `MemoryError` gets status `oom`. The evaluator
then gives `failed` with no cases, which is exactly what Docker gives for any
memory overrun. The evaluator doesn't change.

- The cost: a run where only one test hits MemoryError also loses its
  per-test detail. That again matches Docker, where the whole run is killed.
- The rule only ever moves a run toward "the program's fault". A program
  can't use it to hide its own failure.

**Alternative (B):** leave such runs as `nonzero_exit` and accept rare
`infra_error`s for memory overruns.

Separately, `ulimit -v` limits address space, which is larger than RSS. It
needs a measurement before implementing (section 8, item 3).

## 6. Gaps that remain (accepted, documented in the module header)

- **Memory is per process.** A program that starts N subprocesses can use
  N × `memory`. The Slurm job's memory cgroup is the backstop. If it is hit,
  the job's OOM killer may kill the harness itself, and `collect` resumes on
  the next run.
- **No CPU limit.** Parallel runs share the job's CPUs, so
  `sandbox_workers` must stay at or below the job's CPUs minus what Ollama
  needs. Otherwise slow runs time out. I'll handle this in nexus.yaml (stage
  2).
- **No process limit.** A fork bomb runs until the timeout and can exhaust
  the user's process quota on the node for up to `timeout_s`. As you said,
  `ulimit -u` would count all of your processes on the node, Ollama's threads
  included. In setuid mode there is no user namespace that would make it
  per-container.
- **/tmp is not noexec.** It is 64 MiB of tmpfs and is gone after the run.
- **Results are not comparable with laptop (Docker) results.** The memory
  semantics differ. The keys already keep them apart.

## 7. Code layout

- `sandbox/runner.py`:
  - Factor the runtime-specific parts behind a small interface:
    `ensure_image`, `image_id`, `existing_image_id`, `run`, `sweep`,
    `create_command`.
  - Add `make_runner(cfg: ExperimentConfig, owner) -> SandboxRunner` that
    picks the runtime from `cfg.execution`.
  - The Docker code moves, but its commands don't change.
- `sandbox/apptainer.py` (new): `ApptainerRunner`. It shares
  `_CappedReader`, `_write_files`, `_read_tree`, `classify` and
  `STATUS_FILE` with the Docker runner.
- Call sites switch to `make_runner`: `__main__.py:74`, `collect.py:101`
  and `collect.py:153`, and the evaluator docstring.
- `config.py`: the two `ExecutionConfig` fields and their checks.
- `docker/sandbox/sandbox.def`. Rename `docker/` to `images/`? No: that
  would change `build_context` and with it every key.

## 8. To verify on a compute node, in order (via srun)

1. `apptainer build` of `sandbox.def` works unprivileged (proot).
   - Fallback: install the pinned pure-Python wheels into a directory with
     `pip install --target`, and copy it in with `%files` (no `%post`).
2. Startup time per `apptainer exec`. Expected well under 1 s in setuid mode.
3. Address space of `python -m pytest` with Hypothesis loaded under
   `ulimit -v 512m`.
   - If it doesn't start, a pure `ulimit -v = memory` is unusable. I'll
     come back to you with numbers rather than pick a multiplier myself.
4. The `setsid()` escape is killed at timeout. Checked with `pgrep -u $USER`
   for a marker process afterwards.
5. `/tmp` is the 64 MiB session tmpfs, and `/fs`, `$HOME`, `/etc/hosts` from
   the host and `/etc/localtime` are not visible. Also, `/proc/self/mounts`
   shows no host paths.
6. The exact environment inside the container.
7. Whether the Slurm job cgroup has a `pids.max` (just to document it).

## 9. Tests (`tests/sandbox/test_runner.py`, plus `test_apptainer.py` if it gets long)

- **Unit tests** (always run):
  - every flag in `create_command`
  - the memory and file-size unit conversions
  - the runtime selection and config checks
  - the image id is the file's sha256
  - the def file and the Dockerfile match
  - `MemoryError` → `oom`
  - a missing status file → `infra_error`
- **Integration tests**, marked `apptainer` (conftest skips them when the
  `apptainer` CLI is missing):
  - The existing Docker tests that test behavior, not Docker, become
    parametrized over the available runtimes: success, exit codes, syntax
    error, pytest report, timeout, output before timeout, network,
    read-only filesystem, unprivileged, tmpfs and file size, output cap,
    hash seed, symlinks, status file hidden, reference task passes.
  - Apptainer-only:
    - memory overrun → `oom`
    - host paths invisible
    - exact environment
    - `setsid()` escape killed at timeout
    - background processes die at exit
    - missing SIF → `SandboxError`, a broken SIF → `infra_error`
    - the probe catches a wrong `tmpfs_size`
  - Docker-only, unchanged: pids limit, OOM flag fallback, sweep.

## 10. Questions for you

1. Memory overruns: (A) `MemoryError` → `oom`, recommended, or (B) leave
   them as `nonzero_exit`?
2. Image id: plain `sha256:<hex>` as you said, or `apptainer:sha256:<hex>`
   so logs show the runtime? I lean towards the prefix, because it costs
   nothing.
3. `tmpfs_size` ≠ 64m with Apptainer: fail at start-up (recommended), or warn
   and continue?
4. This checkout is on `main` (PR #4 is merged), not `writer-check-batches`.
   Which branch should this work go on? I'd suggest a new branch off `main`,
   e.g. `apptainer-sandbox`.

### Kill strategies in userns mode (`runs/measure/measure5.py`, tron35)

| Strategy | normal program | ignores SIGTERM | `setsid()` child |
|---|---|---|---|
| SIGKILL the run's process group | helper left | helper left | helper left |
| SIGTERM, wait 2 s, SIGKILL | clean | helper left | clean |
| record the process tree, then SIGKILL group + tree | clean | clean | clean |
| harness crash (only the outer `timeout` fires) | helper left | helper left | helper left |

The starter puts `squashfuse_ll` in a process group of its own. A leftover
is re-parented to PID 1 and still holds the SIF open.

## Implemented (2026-10-29)

What changed from sections 1 to 6:

- **User-namespace mode (`--userns`) with `ulimit -p` = `sandbox.pids_limit`.**
  This is a per-run process limit, as with Docker's `--pids-limit`, so fork
  bombs are contained and can't starve other runs. It replaces the
  "user count + 256" idea.
- **Timeout kills the recorded process tree.** At the timeout the runner
  records the run's process tree, then SIGKILLs the process group and every
  process in the tree.
- **`sweep()` cleans up after a crash.** It kills `squashfuse_ll` processes
  that hold this SIF open and whose parent is not Apptainer's `starter`.
- **Extra isolation flags.**
  - `--no-mount bind-paths,home,cwd,sys`: no host `/sys`.
  - An empty directory is mounted read-only over `/dev/shm`.
- **Environment matches Docker's.** The wrapper removes `APPTAINER_*`,
  `SINGULARITY_*`, `LD_LIBRARY_PATH`, `PS1` and `PROMPT_COMMAND`.
- **Memory: `ulimit -v`.** `MemoryError` → `oom` only when the exit code
  isn't 1. The output reader keeps the last 4 KiB, so the message is seen
  even after a long, capped output.
- **Start-up probe.** Run at every start-up, it checks:
  - uid and uid_map
  - capabilities and no_new_privs
  - interfaces
  - host paths
  - the `/tmp` size = `tmpfs_size`
  - `/dev/shm` and `/sys`
  - the three limits
  - the environment

  Any failure is a `SandboxError`.
- **New `infra_error` causes.**
  - `apptainer_start`: no status file.
  - `status_mismatch`: the status file disagrees with the exit code, e.g.
    a program that forged a status file and killed the wrapper.
  - `image_changed`: the SIF changed since start-up.
- **Image id:** `apptainer:sha256:<hex>`. The def file uses
  `python@sha256:<digest>`.

Remaining gaps: no CPU limit, memory is per process, and `/tmp` is not
noexec.
