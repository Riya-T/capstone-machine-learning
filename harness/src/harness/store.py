"""Results store: one SQLite database plus program files saved by content hash.

Each result is saved as soon as it exists, under a key built from
everything that produced it. A rerun finds its earlier results and skips
them, so nothing is recomputed and no model call is repeated; a crash loses
at most the step in progress.

Files under runs_dir:
    harness.sqlite       all results and every model call
    blobs/<sha256>.json  programs, as {path: base64 bytes}
    <run_id>/run.json    git commit, dirty flag and full config of each run

Rows are never overwritten. Saving the same result again does nothing;
saving a different result under an existing key is an error, because it
means an input changed without changing the key. Measurements (time,
tokens) don't count as part of the result. The one exception: a step that
ended in infra_error may be replaced by its retry.

Usage:
    with Store(cfg.runs_dir) as store:
        run_id = store.start_run(cfg)                # logs git commit and full config
        blob = store.put_blob(files)                 # saves a program, returns its hash
        store.record_candidate(Candidate(...))
        point = resume_point(store.trial_steps(trial), length)  # where a trial continues
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import secrets
import sqlite3
import subprocess
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import asdict, dataclass, fields
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

from .collection.editor import PROTOCOL_VERSION as EDITOR_PROTOCOL_VERSION
from .config import ExperimentConfig, canonical
from .models.backends import CachedCall, usage_from_dict, usage_to_dict

SCHEMA_VERSION = 3  # 2: checkpoints.infra_cause, candidates.call_key; 3: checkpoints.end_reason

Status = Literal[
    "success", "fail_new", "fail_existing", "fail_both", "budget_exhausted", "infra_error"
]
FAILED: frozenset[str] = frozenset({"fail_new", "fail_existing", "fail_both", "budget_exhausted"})


class StoreError(RuntimeError):
    pass


# Columns that describe how a result was obtained rather than what it is.
# They are not compared when the same key is recorded again.
_NOT_COMPARED = (
    "wall_s",
    "tokens_in",
    "tokens_out",
    "n_calls",
    "run_id",
    "failure_cause",
    "created_at",
)


# --- keys -------------------------------------------------------------------


def _hash_json(value: Any) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _input_file_hashes(section: Any, base_dir: Path) -> dict[str, str]:
    """sha256 of every existing file a config section points to (prompt
    templates, mock fixtures), keyed by field location. A config hash covers
    paths, not contents; this makes editing a file change the key too."""
    found: dict[str, str] = {}

    def walk(obj: Any, where: str) -> None:
        if isinstance(obj, Path):
            if obj.is_file():
                found[where] = hashlib.sha256(obj.read_bytes()).hexdigest()
        elif hasattr(obj, "__dataclass_fields__"):
            for f in fields(obj):
                walk(getattr(obj, f.name), f"{where}.{f.name}")

    walk(section, "")
    return found


def _without(section: dict, *fields: str) -> dict:
    return {k: v for k, v in section.items() if k not in fields}


def writer_cfg_hash(cfg: ExperimentConfig) -> str:
    """Keys writer samples: the writer section plus the contents of the files
    it names (prompt template, mock fixtures).

    samples_per_task is left out: sample i is the same whatever the total
    (its seed depends only on i), so raising the count keeps every sample
    already collected and only adds new ones.
    """
    return _hash_json(
        {
            "writer": _without(canonical(cfg.writer, cfg.base_dir), "samples_per_task"),
            "files": _input_file_hashes(cfg.writer, cfg.base_dir),
        }
    )


def editor_cfg_hash(cfg: ExperimentConfig, image_id: str) -> str:
    """Keys editing results: the editor section, the contents of the files it
    names, and the sandbox (settings and image), because the image and its
    limits decide which tests pass as much as the editor does.

    reps is left out, like samples_per_task for the writer: rep k is the same
    trial whatever the number of reps, so adding reps keeps existing trials.
    """
    return _hash_json(
        {
            "editor": _without(canonical(cfg.editor, cfg.base_dir), "reps"),
            # Behavior of the editor code itself (see editor.PROTOCOL_VERSION).
            "editor_protocol": EDITOR_PROTOCOL_VERSION,
            "files": _input_file_hashes(cfg.editor, cfg.base_dir),
            "sandbox": sandbox_cfg_hash(cfg, image_id),
        }
    )


def sandbox_cfg_hash(cfg: ExperimentConfig, image_id: str) -> str:
    """Keys initial checks, which depend on the sandbox but not the editor.

    `image_id` is the image's content id from the runner's image_id: the
    Docker image id, or apptainer:sha256:<hex> of the SIF file. The config
    names the image only by tag, and rebuilding the image under the same
    tag must not reuse results from the old image.
    """
    return _hash_json({"sandbox": canonical(cfg.sandbox, cfg.base_dir), "image_id": image_id})


# --- records ----------------------------------------------------------------


@dataclass(frozen=True)
class CandidateKey:
    task_id: str
    prompt_version: str  # registry.prompt_version of the writer prompt
    writer_cfg_hash: str
    sample_idx: int


@dataclass(frozen=True)
class Candidate:
    key: CandidateKey
    # Hash of the parsed program (its blob). None when the output could not
    # be parsed; the raw text stays in model_calls either way.
    candidate_id: str | None
    parse_error: str | None
    tokens_in: int | None
    tokens_out: int | None
    wall_s: float
    run_id: str
    # model_calls key of the writer answer, so the raw text can be found
    # again (e.g. to train on raw answers instead of re-rendered programs).
    call_key: str | None = None


@dataclass(frozen=True)
class InitialCheck:
    task_id: str
    task_version: str
    candidate_id: str
    sandbox_cfg_hash: str
    passed: bool
    report: dict  # per-category test results from the evaluator
    run_id: str


@dataclass(frozen=True)
class TrialKey:
    """One editing trial: a candidate taken through one change sequence once."""

    task_id: str
    task_version: str
    candidate_id: str
    sequence_id: str
    rep: int
    editor_cfg_hash: str


@dataclass(frozen=True)
class Checkpoint:
    trial: TrialKey
    step: int  # 1-based
    change_id: str
    status: Status
    output_blob: str | None  # program after the edit; None if the step crashed
    new_pass: int | None = None
    new_total: int | None = None
    existing_pass: int | None = None
    existing_total: int | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    n_calls: int | None = None
    wall_s: float | None = None
    diff_lines: int | None = None
    failure_cause: str | None = None  # filled in by human triage
    run_id: str = ""
    # For status infra_error: a short cause code (runner, evaluator or editor).
    infra_cause: str | None = None
    # Why the editor stopped: done, max_turns, max_total_tokens, wall_time,
    # prompt_too_large, or an error message.
    end_reason: str | None = None


@dataclass(frozen=True)
class ResumePoint:
    """Where a trial continues. `next_step` None means the trial is finished;
    otherwise run that step on `input_blob` (None = the original candidate)."""

    next_step: int | None
    input_blob: str | None


def resume_point(steps: list[Checkpoint], length: int) -> ResumePoint:
    """Trajectories stop at the first failure. Successful steps are kept and
    their output feeds the next step; an infra_error step is run again."""
    by_step = {c.step: c for c in steps}
    input_blob = None
    for step in range(1, length + 1):
        done = by_step.get(step)
        if done is None or done.status == "infra_error":
            return ResumePoint(step, input_blob)
        if done.status in FAILED:
            return ResumePoint(None, None)
        input_blob = done.output_blob
    return ResumePoint(None, None)


# --- the store --------------------------------------------------------------

_SCHEMA = """
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    git_commit TEXT NOT NULL,
    git_dirty INTEGER NOT NULL,
    config_hash TEXT NOT NULL,
    config_json TEXT NOT NULL,
    host TEXT NOT NULL
);
CREATE TABLE candidates (
    task_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    writer_cfg_hash TEXT NOT NULL,
    sample_idx INTEGER NOT NULL,
    candidate_id TEXT,
    call_key TEXT,
    parse_error TEXT,
    tokens_in INTEGER,
    tokens_out INTEGER,
    wall_s REAL NOT NULL,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    PRIMARY KEY (task_id, prompt_version, writer_cfg_hash, sample_idx)
);
CREATE TABLE initial_checks (
    task_id TEXT NOT NULL,
    task_version TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    sandbox_cfg_hash TEXT NOT NULL,
    passed INTEGER NOT NULL,
    report_json TEXT NOT NULL,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    PRIMARY KEY (task_id, task_version, candidate_id, sandbox_cfg_hash)
);
CREATE TABLE checkpoints (
    task_id TEXT NOT NULL,
    task_version TEXT NOT NULL,
    candidate_id TEXT NOT NULL,
    sequence_id TEXT NOT NULL,
    rep INTEGER NOT NULL,
    editor_cfg_hash TEXT NOT NULL,
    step INTEGER NOT NULL,
    change_id TEXT NOT NULL,
    status TEXT NOT NULL,
    output_blob TEXT,
    new_pass INTEGER,
    new_total INTEGER,
    existing_pass INTEGER,
    existing_total INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    n_calls INTEGER,
    wall_s REAL,
    diff_lines INTEGER,
    failure_cause TEXT,
    infra_cause TEXT,
    end_reason TEXT,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    PRIMARY KEY (task_id, task_version, candidate_id, sequence_id, rep, editor_cfg_hash, step)
);
CREATE TABLE model_calls (
    key TEXT PRIMARY KEY,
    response_text TEXT NOT NULL,
    usage_json TEXT,
    created_at TEXT NOT NULL
);
"""

# Columns of checkpoints that come from the trial key, in key order.
_TRIAL_COLUMNS = (
    "task_id",
    "task_version",
    "candidate_id",
    "sequence_id",
    "rep",
    "editor_cfg_hash",
)


class Store:
    def __init__(self, runs_dir: Path) -> None:
        self.runs_dir = Path(runs_dir)
        self.blob_dir = self.runs_dir / "blobs"
        self.blob_dir.mkdir(parents=True, exist_ok=True)
        # isolation_level=None: no implicit transactions; each write below
        # opens its own explicit one, so a crash never leaves half a step.
        self._db = sqlite3.connect(self.runs_dir / "harness.sqlite", isolation_level=None)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        version = self._db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            # executescript() commits any open transaction before it runs, so
            # the transaction goes inside the script: tables and version are
            # created together or not at all.
            self._db.executescript(
                f"BEGIN IMMEDIATE;{_SCHEMA}PRAGMA user_version={SCHEMA_VERSION};COMMIT;"
            )
        elif version != SCHEMA_VERSION:
            raise StoreError(
                f"{self.runs_dir}: store schema {version}, this code expects {SCHEMA_VERSION}"
            )

    def close(self) -> None:
        self._db.close()

    def __enter__(self) -> Store:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _transaction(self):
        return _Transaction(self._db)

    # -- runs --

    def start_run(self, cfg: ExperimentConfig, repo_dir: Path | None = None) -> str:
        """Record the code version and full config; returns the run id.

        The commit is that of the repository holding the pipeline code
        (`repo_dir` overrides it, for tests). The config itself is logged in
        full, so a config kept outside the repository is still recorded.
        """
        commit, dirty = git_state(repo_dir or Path(__file__).resolve().parent)
        if dirty and not cfg.allow_dirty:
            raise StoreError(
                "the git tree has uncommitted changes; commit them or set allow_dirty: true"
            )
        started = datetime.now(UTC)
        run_id = f"{started:%Y%m%dT%H%M%SZ}-{secrets.token_hex(3)}"
        config_json = json.dumps(cfg.to_dict(), sort_keys=True, indent=2)
        record = {
            "run_id": run_id,
            "started_at": started.isoformat(),
            "git_commit": commit,
            "git_dirty": dirty,
            "config_hash": cfg.config_hash,
            "host": platform.node(),
        }
        run_dir = self.runs_dir / run_id
        run_dir.mkdir()
        (run_dir / "run.json").write_text(
            json.dumps({**record, "config": cfg.to_dict()}, indent=2) + "\n", encoding="utf-8"
        )
        with self._transaction():
            self._db.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    record["started_at"],
                    commit,
                    int(dirty),
                    cfg.config_hash,
                    config_json,
                    record["host"],
                ),
            )
        return run_id

    def get_run(self, run_id: str) -> dict:
        row = self._db.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(run_id)
        data = dict(row)
        data["git_dirty"] = bool(data["git_dirty"])
        data["config"] = json.loads(data.pop("config_json"))
        return data

    # -- blobs --

    def put_blob(self, files: Mapping[str, bytes]) -> str:
        """Store a program; returns its content hash. Storing the same program
        twice writes nothing the second time."""
        data = _encode_program(files)
        digest = hashlib.sha256(data).hexdigest()
        path = self.blob_dir / f"{digest}.json"
        if not path.exists():
            tmp = path.with_name(f"{path.name}.{secrets.token_hex(4)}.tmp")
            tmp.write_bytes(data)
            os.replace(tmp, path)  # atomic: readers never see half a blob
        return digest

    def get_blob(self, digest: str) -> dict[str, bytes]:
        path = self.blob_dir / f"{digest}.json"
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            raise KeyError(digest) from None
        if hashlib.sha256(data).hexdigest() != digest:
            raise StoreError(f"blob {digest} is corrupt: its content no longer matches its name")
        return {p: base64.b64decode(b) for p, b in json.loads(data).items()}

    # -- candidates --

    def record_candidate(self, c: Candidate) -> None:
        row = {**asdict(c.key), **{k: v for k, v in asdict(c).items() if k != "key"}}
        self._insert_once("candidates", row, key=list(asdict(c.key)))

    def get_candidate(self, key: CandidateKey) -> Candidate | None:
        row = self._select_one("candidates", asdict(key))
        if row is None:
            return None
        values = _columns(row, exclude=asdict(key))
        return Candidate(key=key, **values)

    def candidates(self, task_id: str, prompt_version: str, writer_hash: str) -> list[Candidate]:
        rows = self._db.execute(
            "SELECT sample_idx FROM candidates WHERE task_id = ? AND prompt_version = ? "
            "AND writer_cfg_hash = ? ORDER BY sample_idx",
            (task_id, prompt_version, writer_hash),
        ).fetchall()
        return [
            self.get_candidate(CandidateKey(task_id, prompt_version, writer_hash, r[0]))
            for r in rows
        ]

    # -- initial checks --

    def record_initial_check(self, check: InitialCheck) -> None:
        row = asdict(check)
        row["passed"] = int(row["passed"])
        row["report_json"] = json.dumps(row.pop("report"), sort_keys=True)
        key = ["task_id", "task_version", "candidate_id", "sandbox_cfg_hash"]
        self._insert_once("initial_checks", row, key=key)

    def get_initial_check(
        self, task_id: str, task_version: str, candidate_id: str, sandbox_hash: str
    ) -> InitialCheck | None:
        row = self._select_one(
            "initial_checks",
            {
                "task_id": task_id,
                "task_version": task_version,
                "candidate_id": candidate_id,
                "sandbox_cfg_hash": sandbox_hash,
            },
        )
        if row is None:
            return None
        data = dict(row)
        data["passed"] = bool(data["passed"])
        data["report"] = json.loads(data.pop("report_json"))
        return InitialCheck(**data)

    # -- checkpoints --

    def record_checkpoint(self, c: Checkpoint) -> None:
        row = {**asdict(c.trial), **{k: v for k, v in asdict(c).items() if k != "trial"}}
        key = [*_TRIAL_COLUMNS, "step"]
        existing = self._select_one("checkpoints", {k: row[k] for k in key})
        if existing is not None and existing["status"] == "infra_error":
            # A crash between this delete and the insert below leaves the step
            # missing, which resume_point treats exactly like infra_error.
            with self._transaction():
                self._db.execute(
                    "DELETE FROM checkpoints WHERE " + " AND ".join(f"{k} = ?" for k in key),
                    [row[k] for k in key],
                )
        self._insert_once("checkpoints", row, key=key)

    def trial_steps(self, trial: TrialKey) -> list[Checkpoint]:
        rows = self._db.execute(
            "SELECT * FROM checkpoints WHERE "
            + " AND ".join(f"{k} = ?" for k in _TRIAL_COLUMNS)
            + " ORDER BY step",
            list(asdict(trial).values()),
        ).fetchall()
        return [Checkpoint(trial=trial, **_columns(r, exclude=_TRIAL_COLUMNS)) for r in rows]

    def all_checkpoints(self) -> Iterator[Checkpoint]:
        for r in self._db.execute(
            f"SELECT * FROM checkpoints ORDER BY {', '.join(_TRIAL_COLUMNS)}, step"
        ):
            trial = TrialKey(**{k: r[k] for k in _TRIAL_COLUMNS})
            yield Checkpoint(trial=trial, **_columns(r, exclude=_TRIAL_COLUMNS))

    def set_failure_cause(self, trial: TrialKey, step: int, cause: str) -> None:
        """Human triage label; the only field that may change after writing."""
        with self._transaction():
            cur = self._db.execute(
                "UPDATE checkpoints SET failure_cause = ? WHERE "
                + " AND ".join(f"{k} = ?" for k in (*_TRIAL_COLUMNS, "step")),
                [cause, *asdict(trial).values(), step],
            )
        if cur.rowcount != 1:
            raise KeyError((trial, step))

    # -- model call cache (implements backends.CallCache) --

    def get(self, key: str) -> CachedCall | None:
        row = self._db.execute(
            "SELECT response_text, usage_json FROM model_calls WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        usage = json.loads(row["usage_json"]) if row["usage_json"] else None
        return CachedCall(row["response_text"], usage_from_dict(usage))

    def put(self, key: str, call: CachedCall) -> None:
        usage = usage_to_dict(call.usage)
        row = {
            "key": key,
            "response_text": call.text,
            "usage_json": None if usage is None else json.dumps(usage, sort_keys=True),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._insert_once("model_calls", row, key=["key"])

    # -- helpers --

    def _select_one(self, table: str, where: dict[str, Any]) -> sqlite3.Row | None:
        return self._db.execute(
            f"SELECT * FROM {table} WHERE " + " AND ".join(f"{k} = ?" for k in where),
            list(where.values()),
        ).fetchone()

    def _insert_once(self, table: str, row: dict[str, Any], key: list[str]) -> None:
        """Insert a row; if its key exists, the stored row must be identical
        in every outcome column (all but _NOT_COMPARED), otherwise raise."""
        with self._transaction():
            existing = self._select_one(table, {k: row[k] for k in key})
            if existing is None:
                columns = ", ".join(row)
                marks = ", ".join("?" for _ in row)
                self._db.execute(
                    f"INSERT INTO {table} ({columns}) VALUES ({marks})", list(row.values())
                )
                return
        stored = {k: existing[k] for k in row if k not in _NOT_COMPARED}
        new = {k: v for k, v in row.items() if k not in _NOT_COMPARED}
        if stored != new:
            changed = sorted(k for k in new if stored[k] != new[k])
            raise StoreError(
                f"{table}: a different result is already stored for this key "
                f"(differs in {changed}); some input changed without changing the key"
            )


def _columns(row: sqlite3.Row, exclude: Iterable[str]) -> dict[str, Any]:
    """A row as {column: value}, minus some columns. (Iterating a
    sqlite3.Row yields values, not names, so `for k in row` would be wrong.)"""
    skip = set(exclude)
    return {k: v for k, v in dict(row).items() if k not in skip}


class _Transaction:
    """BEGIN IMMEDIATE ... COMMIT, rolled back on error. IMMEDIATE takes the
    write lock up front, so a read-then-insert can't race another writer."""

    def __init__(self, db: sqlite3.Connection) -> None:
        self.db = db

    def __enter__(self) -> None:
        self.db.execute("BEGIN IMMEDIATE")

    def __exit__(self, exc_type: object, *rest: object) -> None:
        self.db.execute("ROLLBACK" if exc_type else "COMMIT")


def _encode_program(files: Mapping[str, bytes]) -> bytes:
    """Canonical bytes for a program: sorted paths, base64 contents. The same
    files always give the same bytes, so the hash identifies the program."""
    payload = {path: base64.b64encode(files[path]).decode("ascii") for path in sorted(files)}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def git_state(directory: Path) -> tuple[str, bool]:
    """(commit hash, has uncommitted changes) for the repository holding
    `directory`. Untracked files count as changes: they can affect a run."""

    def git(*args: str) -> str:
        try:
            result = subprocess.run(
                ["git", *args], cwd=directory, capture_output=True, text=True, check=True
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise StoreError(f"cannot read git state in {directory}: {exc}") from None
        return result.stdout.strip()

    return git("rev-parse", "HEAD"), bool(git("status", "--porcelain"))
