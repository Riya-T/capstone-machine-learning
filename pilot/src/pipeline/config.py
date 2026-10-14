"""Experiment configuration: YAML files -> frozen, validated dataclasses.

Every model name, endpoint, budget, seed, task list and path in the pipeline
comes from here. The loader is strict on purpose: an unknown key, a missing
key or a wrong type raises ConfigError, because a typo that silently fell
back to a default would change an experiment without anyone noticing.

The schema grows stage by stage; fields are added in the stage whose module
first needs them, so the config never references files that don't exist yet.

Usage:
    from pipeline.config import load_config
    cfg = load_config("configs/pilot_mock.yaml")     # follows `extends`, validates everything
    cfg.writer.backend.model, cfg.tasks.dir          # typed, frozen settings
    cfg.config_hash, cfg.component_hash(cfg.editor)  # for keying stored results
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import types
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Annotated, Any, Literal, Union, get_args, get_origin, get_type_hints

import yaml

SCHEMA_VERSION = 1


class ConfigError(ValueError):
    """Raised for any invalid configuration; the message names the offending key."""


class PathKind(Enum):
    INPUT = "input"  # must exist when the config is loaded
    OUTPUT = "output"  # created later by the pipeline; may not exist yet


# Paths are written relative to the config file and resolved to absolute
# paths on load. The Annotated tag tells the loader whether to require that
# the path already exists.
InputPath = Annotated[Path, PathKind.INPUT]
OutputPath = Annotated[Path, PathKind.OUTPUT]

# Fields carrying this metadata are set by the loader, never read from YAML,
# and excluded from hashes.
_INTERNAL = {"internal": True}


# --- schema -----------------------------------------------------------------


@dataclass(frozen=True)
class SequenceLengths:
    """Number of changes per sequence, by split. Proposal: training uses
    sequences of two changes; evaluation uses three."""

    train: int
    dev: int
    eval: int

    def __post_init__(self) -> None:
        for split in ("train", "dev", "eval"):
            _require_positive(getattr(self, split), split)


@dataclass(frozen=True)
class TasksConfig:
    dir: InputPath
    include: tuple[str, ...]
    sequence_length: SequenceLengths
    sequences_per_task: int  # proposal: two different change sequences

    def __post_init__(self) -> None:
        # Whether each listed task exists is checked by the registry.
        if len(set(self.include)) != len(self.include):
            raise ConfigError("include: contains duplicate task ids")
        _require_positive(self.sequences_per_task, "sequences_per_task")


@dataclass(frozen=True)
class BackendConfig:
    kind: Literal["openai_compat", "mock"]
    model: str
    temperature: float
    max_tokens: int
    # openai_compat only. The API key itself never appears in a config file
    # (configs are logged verbatim with every run); only the name of the
    # environment variable that holds it.
    base_url: str | None = None
    api_key_env: str | None = None
    request_timeout_s: float = 600.0
    # Retries cover transient failures only: connection errors, 429 and 5xx.
    # The wait doubles after each attempt: backoff, 2 * backoff, ...
    max_retries: int = 2
    retry_backoff_s: float = 2.0
    # mock only: YAML file of response rules (see backends.MockBackend).
    fixtures: InputPath | None = None

    def __post_init__(self) -> None:
        if self.kind == "openai_compat":
            if not self.base_url:
                raise ConfigError("base_url: required when kind is openai_compat")
            if self.fixtures is not None:
                raise ConfigError("fixtures: only valid when kind is mock")
        if self.kind == "mock" and self.fixtures is None:
            raise ConfigError("fixtures: required when kind is mock")
        if self.temperature < 0:
            raise ConfigError("temperature: must be >= 0")
        _require_positive(self.max_tokens, "max_tokens")
        _require_positive(self.request_timeout_s, "request_timeout_s")
        if self.max_retries < 0:
            raise ConfigError("max_retries: must be >= 0")
        if self.retry_backoff_s < 0:
            raise ConfigError("retry_backoff_s: must be >= 0")


@dataclass(frozen=True)
class WriterConfig:
    backend: BackendConfig
    samples_per_task: int  # proposal: up to 8 candidates per training task
    # string.Template file with exactly $entry_files, $spec and $public_checks.
    # The hash covers the path only; the store keys candidates by the template's
    # contents (see registry.prompt_version).
    prompt_template: InputPath

    def __post_init__(self) -> None:
        _require_positive(self.samples_per_task, "samples_per_task")


@dataclass(frozen=True)
class EditorBudget:
    max_turns: int
    max_total_tokens: int
    wall_time_s: float

    def __post_init__(self) -> None:
        _require_positive(self.max_turns, "max_turns")
        _require_positive(self.max_total_tokens, "max_total_tokens")
        _require_positive(self.wall_time_s, "wall_time_s")


@dataclass(frozen=True)
class EditorConfig:
    backend: BackendConfig
    # Provisional pending team sign-off; a new scaffold is a new Literal value.
    scaffold: Literal["turn_loop"]
    budget: EditorBudget
    reps: int  # repetitions per (candidate, sequence); proposal: 3
    # What the editor sees. "strip_comments" is the comment ablation; making
    # it part of the editor config puts it in the editor config hash, so
    # ablation results never collide with main results.
    view_transform: Literal["none", "strip_comments"] = "none"

    def __post_init__(self) -> None:
        _require_positive(self.reps, "reps")


@dataclass(frozen=True)
class SandboxConfig:
    # Image tag. Results are keyed by the image's content id, resolved by the
    # runner at start-up, so rebuilding under the same tag can't reuse stale
    # results.
    image: str
    timeout_s: float  # wall clock per run, container start-up included
    memory: str  # docker syntax, e.g. "512m"; swap is disabled
    cpus: float
    pids_limit: int
    tmpfs_size: str  # docker syntax, e.g. "64m"; the only writable scratch space
    output_cap_bytes: int  # stdout and stderr are each cut to this size
    file_size_limit_bytes: int = 16 * 1024 * 1024  # largest file a run may write
    # Directory with the Dockerfile; lets the runner build a missing image.
    build_context: InputPath | None = None

    def __post_init__(self) -> None:
        _require_positive(self.timeout_s, "timeout_s")
        _require_positive(self.cpus, "cpus")
        _require_positive(self.pids_limit, "pids_limit")
        _require_positive(self.output_cap_bytes, "output_cap_bytes")
        _require_positive(self.file_size_limit_bytes, "file_size_limit_bytes")


@dataclass(frozen=True)
class ScorerConfig:
    # Validated against the scorer's rule registry when the scorer is built,
    # not here, so adding a rule never requires touching the config schema.
    rule: str
    pairing_mode: Literal["all_pairs", "best_vs_worst"]
    per_task_cap: int | None = None  # max pairs per task; None = no cap
    # Ablations computed from stored results without new model calls:
    max_changes: int | None = None  # truncate trial scores to this many changes
    reps: tuple[int, ...] | None = None  # use only these rep indices

    def __post_init__(self) -> None:
        if self.per_task_cap is not None:
            _require_positive(self.per_task_cap, "per_task_cap")
        if self.max_changes is not None:
            _require_positive(self.max_changes, "max_changes")
        if self.reps is not None and (not self.reps or min(self.reps) < 0):
            raise ConfigError("reps: must be a non-empty list of rep indices >= 0")


@dataclass(frozen=True)
class ExperimentConfig:
    schema_version: int
    name: str
    seed: int  # base seed; per-call seeds are derived from it
    allow_dirty: bool  # allow runs from a git tree with uncommitted changes
    runs_dir: OutputPath
    tasks: TasksConfig
    writer: WriterConfig
    editor: EditorConfig
    sandbox: SandboxConfig
    scorer: ScorerConfig
    # Directory of the entry config file; paths are hashed relative to it so
    # the same experiment hashes identically on the laptop and on the 5090.
    base_dir: Path = field(default=Path("."), metadata=_INTERNAL)

    def __post_init__(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise ConfigError(
                f"schema_version: expected {SCHEMA_VERSION}, got {self.schema_version}"
            )

    def to_dict(self) -> dict[str, Any]:
        """The full resolved config as JSON-ready data, for run logs."""
        return canonical(self, self.base_dir)

    @property
    def config_hash(self) -> str:
        return stable_hash(self, self.base_dir)

    def component_hash(self, part: Any) -> str:
        """Hash one section (e.g. self.editor) so results keyed by it are only
        invalidated by changes to that section, not to unrelated ones."""
        return stable_hash(part, self.base_dir)


def _require_positive(value: float, where: str) -> None:
    if value <= 0:
        raise ConfigError(f"{where}: must be > 0, got {value}")


# --- loading ----------------------------------------------------------------


def load_config(path: str | os.PathLike[str]) -> ExperimentConfig:
    """Load an experiment config, following `extends` and resolving paths."""
    entry = Path(path).resolve()
    raw = _load_with_extends(entry, seen=())
    base_dir = entry.parent
    cfg = _build(ExperimentConfig, raw, where="", base_dir=base_dir)
    return dataclasses.replace(cfg, base_dir=base_dir)


def _load_with_extends(path: Path, seen: tuple[Path, ...]) -> dict[str, Any]:
    """Read a YAML mapping; if it has `extends: parent.yaml`, deep-merge it
    over the parent. The `extends` key is dropped, so two configs that resolve
    to the same values hash the same no matter how they were split into files.
    """
    if path in seen:
        chain = " -> ".join(p.name for p in (*seen, path))
        raise ConfigError(f"extends: cycle detected: {chain}")
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name}: top level must be a mapping")

    parent_name = data.pop("extends", None)
    if parent_name is None:
        return data
    if not isinstance(parent_name, str):
        raise ConfigError(f"{path.name}: extends must be a file name")
    parent = (path.parent / parent_name).resolve()
    # All paths resolve relative to the entry config's directory. Keeping a
    # whole extends chain in one directory means that rule never surprises.
    if parent.parent != path.parent:
        raise ConfigError(f"{path.name}: extends must name a file in the same directory")
    return _deep_merge(_load_with_extends(parent, (*seen, path)), data)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Mappings merge key by key; anything else (lists, scalars) is replaced."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def parse_dataclass(cls: type, data: Any, *, base_dir: Path, where: str = "") -> Any:
    """Build dataclass `cls` from YAML data with the same strict checks as
    configs. Relative paths resolve against `base_dir`. The registry uses
    this for task manifests."""
    return _build(cls, data, where, base_dir)


def _build(cls: type, data: Any, where: str, base_dir: Path) -> Any:
    """Construct dataclass `cls` from a mapping, checking keys and types."""
    if not isinstance(data, dict):
        raise ConfigError(f"{where or 'config'}: expected a mapping")
    hints = get_type_hints(cls, include_extras=True)
    fields = {f.name: f for f in dataclasses.fields(cls) if not f.metadata.get("internal")}

    unknown = sorted(set(data) - set(fields))
    if unknown:
        raise ConfigError(f"{_join(where, unknown[0])}: unknown key")

    kwargs = {}
    for name, f in fields.items():
        key = _join(where, name)
        if name in data:
            kwargs[name] = _convert(data[name], hints[name], key, base_dir)
        elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
            raise ConfigError(f"{key}: missing required key")
    try:
        return cls(**kwargs)
    except ConfigError as exc:
        # __post_init__ messages use the section's own name; prefix the
        # full location so errors in nested sections are easy to find.
        raise ConfigError(f"{where + ': ' if where else ''}{exc}") from None


def _convert(value: Any, tp: Any, where: str, base_dir: Path) -> Any:
    """Check `value` against type annotation `tp` and convert it."""
    origin = get_origin(tp)

    if origin is Annotated:
        inner, kind = get_args(tp)[:2]
        if inner is not Path:
            raise TypeError(f"unsupported annotated type at {where}")
        return _convert_path(value, kind, where, base_dir)

    if origin in (Union, types.UnionType):
        args = get_args(tp)
        if value is None and type(None) in args:
            return None
        (non_none,) = [a for a in args if a is not type(None)]  # only `X | None`
        return _convert(value, non_none, where, base_dir)

    if origin is Literal:
        allowed = get_args(tp)
        if value not in allowed:
            raise ConfigError(f"{where}: must be one of {list(allowed)}, got {value!r}")
        return value

    if origin is dict:
        key_type, value_type = get_args(tp)
        assert key_type is str, "only dict[str, X] is supported"
        if not isinstance(value, dict):
            raise ConfigError(f"{where}: expected a mapping")
        return {str(k): _convert(v, value_type, f"{where}.{k}", base_dir) for k, v in value.items()}

    if origin is tuple:
        item_type, ellipsis = get_args(tp)
        assert ellipsis is Ellipsis, "only tuple[X, ...] is supported"
        if not isinstance(value, list):
            raise ConfigError(f"{where}: expected a list")
        return tuple(_convert(v, item_type, f"{where}[{i}]", base_dir) for i, v in enumerate(value))

    if dataclasses.is_dataclass(tp):
        return _build(tp, value, where, base_dir)

    # bool is a subclass of int in Python, so `True` would pass an int check;
    # reject it explicitly for int and float fields.
    if tp is bool:
        if not isinstance(value, bool):
            raise ConfigError(f"{where}: expected true/false, got {value!r}")
        return value
    if tp is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ConfigError(f"{where}: expected an integer, got {value!r}")
        return value
    if tp is float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"{where}: expected a number, got {value!r}")
        return float(value)
    if tp is str:
        if not isinstance(value, str):
            raise ConfigError(f"{where}: expected a string, got {value!r}")
        return value

    raise TypeError(f"unsupported config field type {tp!r} at {where}")


def _convert_path(value: Any, kind: PathKind, where: str, base_dir: Path) -> Path:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{where}: expected a path string, got {value!r}")
    path = (base_dir / value).resolve()  # absolute values pass through unchanged
    if kind is PathKind.INPUT and not path.exists():
        raise ConfigError(f"{where}: path does not exist: {path}")
    return path


def _join(where: str, key: str) -> str:
    return f"{where}.{key}" if where else key


# --- hashing ----------------------------------------------------------------


def canonical(obj: Any, base_dir: Path) -> Any:
    """Convert config objects to plain JSON data.

    Paths become relative to `base_dir` (POSIX separators), so the result
    doesn't depend on where the repository is checked out.
    """
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: canonical(getattr(obj, f.name), base_dir)
            for f in dataclasses.fields(obj)
            if not f.metadata.get("internal")
        }
    if isinstance(obj, Path):
        return Path(os.path.relpath(obj, base_dir)).as_posix()
    if isinstance(obj, (tuple, list)):
        return [canonical(v, base_dir) for v in obj]
    if isinstance(obj, dict):
        return {str(k): canonical(v, base_dir) for k, v in obj.items()}
    return obj


def stable_hash(obj: Any, base_dir: Path) -> str:
    """sha256 of the canonical JSON form.

    YAML key order never reaches this point: `canonical` emits dataclass
    fields in declaration order. sort_keys guards the other direction, so
    reordering fields in this module (a harmless refactor) doesn't change
    every hash and orphan stored results.
    """
    text = json.dumps(
        canonical(obj, base_dir), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
