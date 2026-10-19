"""Task registry: loads task directories, enforces the task rules, and builds
the writer prompt.

A task directory holds a `task.yaml` manifest plus real files: the spec,
tests, reference solutions and planted bugs. Loading turns it into a frozen
`Task` in which every file is already read and every (sequence, step) has its
reference program and test sets resolved, so later stages never deal with the
manifest format.

What the writer may see is enforced by a type: `build_writer_prompt` accepts
only a `WriterView` (entry file names, spec, initial public checks). Later
changes, private tests and references are not reachable from it.

Usage:
    tasks = load_tasks(cfg.tasks)                    # {task_id: Task}; all rules checked
    task = tasks["record_store"]
    prompt = build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    step = task.sequence("s1").steps[0]              # reference and test sets for one step
    step.tests.public, step.tests.new_feature, step.tests.existing
"""

from __future__ import annotations

import ast
import hashlib
import string
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

from .config import ConfigError, InputPath, TasksConfig, parse_dataclass

MANIFEST = "task.yaml"
SCHEMA_VERSION = 1
# Placeholders the writer prompt template must use, all of them and no others.
TEMPLATE_FIELDS = frozenset({"entry_files", "spec", "public_checks"})
# Lines of a change request at least this long must not appear verbatim in
# writer-visible files (shorter lines are too generic to signal a leak).
_LEAK_LINE_MIN = 30
# Created by tools next to tests; never part of a task's content.
_IGNORED_NAMES = frozenset({"__pycache__", ".pytest_cache"})
_IGNORED_SUFFIXES = frozenset({".pyc"})

Split = Literal["train", "dev", "eval"]
InitialCategory = Literal["initial", "public"]
StepCategory = Literal["new_feature", "existing", "public"]


class TaskError(ValueError):
    """A task directory breaks the schema or the task rules."""


# --- manifest schema: what task.yaml says -----------------------------------
# Parsed with the same strict loader as configs: unknown keys, missing keys
# and wrong types are errors, and paths resolve relative to the task dir.


@dataclass(frozen=True)
class InitialBugSpec:
    path: InputPath
    must_fail: tuple[InitialCategory, ...]
    must_pass: tuple[InitialCategory, ...] = ()


@dataclass(frozen=True)
class StepBugSpec:
    path: InputPath
    must_fail: tuple[StepCategory, ...]
    must_pass: tuple[StepCategory, ...] = ()


@dataclass(frozen=True)
class ChangeSpec:
    id: str
    kind: str  # e.g. concurrency_control; lets evaluation hold out whole kinds
    request: InputPath
    new_feature_tests: tuple[InputPath, ...]
    public_checks: tuple[InputPath, ...] = ()
    # Node ids ("path::test_name") of earlier tests this change deliberately
    # makes obsolete; they are dropped from every later test set.
    supersedes: tuple[str, ...] = ()


@dataclass(frozen=True)
class StepSpec:
    change: str
    reference: InputPath | None = None  # overrides the shared `references` entry
    planted_bugs: tuple[StepBugSpec, ...] = ()


@dataclass(frozen=True)
class SequenceSpec:
    id: str
    steps: tuple[StepSpec, ...]


@dataclass(frozen=True)
class Manifest:
    schema_version: int
    id: str
    family: str  # close variants share a family; a family lives in one split
    split: Split
    entry_files: tuple[str, ...]
    spec: InputPath
    public_checks: tuple[InputPath, ...]
    private_tests: tuple[InputPath, ...]
    reference: InputPath
    changes: tuple[ChangeSpec, ...]
    sequences: tuple[SequenceSpec, ...]
    planted_bugs: tuple[InitialBugSpec, ...] = ()
    # Reference programs keyed by the set of applied changes: sorted change
    # ids joined by "+". Sequences reaching the same set share one entry.
    references: dict[str, InputPath] = field(default_factory=dict)


# --- loaded task: what the rest of the pipeline uses ------------------------

Program = Mapping[str, bytes]  # relative POSIX path -> exact file bytes


@dataclass(frozen=True)
class TaskFile:
    path: str  # relative to the task directory, POSIX separators
    content: bytes

    @property
    def text(self) -> str:
        return self.content.decode("utf-8")


@dataclass(frozen=True)
class CheckSet:
    """Test files run together as one category, minus deselected tests."""

    files: tuple[TaskFile, ...]
    # Whole test functions ("path::test_name") to leave out. The evaluator
    # must match these exactly; pytest's --deselect matches by prefix, which
    # would also drop e.g. "test_name_2".
    deselect: tuple[str, ...] = ()


@dataclass(frozen=True)
class StepTests:
    public: CheckSet  # editor-visible: initial + changes 1..k public checks
    new_feature: CheckSet  # change k's private tests
    existing: CheckSet  # initial private tests + changes 1..k-1 private tests


@dataclass(frozen=True)
class PlantedBug:
    path: str
    program: Program
    must_fail: frozenset[str]
    must_pass: frozenset[str]


@dataclass(frozen=True)
class Change:
    id: str
    kind: str
    request: str
    public_checks: tuple[TaskFile, ...]
    new_feature_tests: tuple[TaskFile, ...]
    supersedes: tuple[str, ...]


@dataclass(frozen=True)
class Step:
    number: int  # 1-based position in the sequence
    change: Change
    reference_path: str
    reference: Program
    planted_bugs: tuple[PlantedBug, ...]
    tests: StepTests


@dataclass(frozen=True)
class ChangeSequence:
    id: str
    steps: tuple[Step, ...]


@dataclass(frozen=True)
class WriterView:
    """Everything the writer may see about a task, and nothing else."""

    entry_files: tuple[str, ...]
    spec: str
    public_checks: tuple[TaskFile, ...]


@dataclass(frozen=True)
class Task:
    id: str
    family: str
    split: str
    root: Path
    entry_files: tuple[str, ...]
    spec: str
    public_checks: tuple[TaskFile, ...]
    private_tests: tuple[TaskFile, ...]
    reference: Program
    planted_bugs: tuple[PlantedBug, ...]
    changes: Mapping[str, Change]
    sequences: tuple[ChangeSequence, ...]
    # Hash of every file in the task directory. Keys editing checkpoints, so
    # any fix to tests, requests or references invalidates stale results.
    task_version: str

    def writer_view(self) -> WriterView:
        return WriterView(self.entry_files, self.spec, self.public_checks)

    def sequence(self, sequence_id: str) -> ChangeSequence:
        for sequence in self.sequences:
            if sequence.id == sequence_id:
                return sequence
        raise KeyError(sequence_id)


# --- writer prompt ----------------------------------------------------------


def load_template(path: Path, fields: frozenset[str] = TEMPLATE_FIELDS) -> string.Template:
    """Load a prompt template and check it uses exactly `fields` as
    placeholders (by default the writer's)."""
    template = string.Template(path.read_text(encoding="utf-8"))
    if not template.is_valid():
        raise ConfigError(f"{path}: invalid placeholder (write a literal $ as $$)")
    found = set(template.get_identifiers())
    if found != fields:
        raise ConfigError(
            f"{path}: placeholders must be exactly {sorted(fields)}, got {sorted(found)}"
        )
    return template


def build_writer_prompt(view: WriterView, template: string.Template) -> str:
    checks = "\n\n".join(
        f"### {PurePosixPath(f.path).name}\n\n```python\n{f.text.rstrip()}\n```"
        for f in view.public_checks
    )
    return template.substitute(
        entry_files=", ".join(view.entry_files), spec=view.spec.strip(), public_checks=checks
    )


def prompt_version(prompt: str) -> str:
    """Keys writer samples. Hashing the rendered prompt covers the spec, the
    public checks and the template, and nothing hidden, so fixing private
    tests or later changes keeps existing candidates."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


# --- loading ----------------------------------------------------------------


def load_tasks(cfg: TasksConfig) -> dict[str, Task]:
    """Load the tasks listed in `cfg.include`.

    Split rules are checked across every task in the directory, not only the
    included ones: a family split across train and eval is leakage even if
    this run uses only one of its tasks.
    """
    splits = scan_splits(cfg.dir)
    missing = [task_id for task_id in cfg.include if task_id not in splits]
    if missing:
        raise TaskError(f"tasks not found in {cfg.dir}: {missing}")
    return {task_id: load_task(cfg.dir / task_id, cfg) for task_id in cfg.include}


def scan_splits(tasks_dir: Path) -> dict[str, tuple[str, str]]:
    """Map task id -> (family, split) for every task directory, and check that
    each family sits in exactly one split."""
    found: dict[str, tuple[str, str]] = {}
    for manifest in sorted(tasks_dir.glob(f"*/{MANIFEST}")):
        data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "family" not in data or "split" not in data:
            raise TaskError(f"{manifest}: needs `family` and `split`")
        found[manifest.parent.name] = (str(data["family"]), str(data["split"]))

    by_family: dict[str, dict[str, list[str]]] = {}
    for task_id, (family, split) in found.items():
        by_family.setdefault(family, {}).setdefault(split, []).append(task_id)
    for family, splits in sorted(by_family.items()):
        if len(splits) > 1:
            raise TaskError(f"family {family!r} spans several splits: {splits}")
    return found


def load_task(task_dir: Path, rules: TasksConfig) -> Task:
    root = task_dir.resolve()
    manifest_path = root / MANIFEST
    if not manifest_path.is_file():
        raise TaskError(f"{manifest_path}: not found")
    try:
        manifest = parse_dataclass(
            Manifest, yaml.safe_load(manifest_path.read_text(encoding="utf-8")), base_dir=root
        )
    except ConfigError as exc:
        raise TaskError(f"{manifest_path}: {exc}") from None
    try:
        return _Loader(root, manifest, rules).load()
    except TaskError as exc:
        raise TaskError(f"{manifest_path}: {exc}") from None


class _Loader:
    """Checks one manifest against the task rules and builds the Task."""

    def __init__(self, root: Path, manifest: Manifest, rules: TasksConfig) -> None:
        self.root = root
        self.m = manifest
        self.rules = rules

    def load(self) -> Task:
        m = self.m
        if m.schema_version != SCHEMA_VERSION:
            raise TaskError(f"schema_version: expected {SCHEMA_VERSION}")
        if m.id != self.root.name:
            raise TaskError(f"id {m.id!r} must match the directory name {self.root.name!r}")
        self._check_no_symlinks()
        self._check_entry_files()

        public = self._tests(m.public_checks, "public_checks")
        private = self._tests(m.private_tests, "private_tests")
        changes = {c.id: self._change(c) for c in m.changes}
        if len(changes) != len(m.changes):
            raise TaskError("changes: duplicate change ids")
        self._check_unique_test_names(public, private, changes)

        spec = self._text(m.spec, "spec")
        self._check_no_leaks(spec, public, changes)

        return Task(
            id=m.id,
            family=m.family,
            split=m.split,
            root=self.root,
            entry_files=m.entry_files,
            spec=spec,
            public_checks=public,
            private_tests=private,
            reference=self._program(m.reference, "reference"),
            planted_bugs=tuple(self._bug(b, "planted_bugs") for b in m.planted_bugs),
            changes=changes,
            sequences=self._sequences(changes, public, private),
            task_version=self._task_version(),
        )

    # -- sequences and test sets --

    def _sequences(
        self,
        changes: dict[str, Change],
        public: tuple[TaskFile, ...],
        private: tuple[TaskFile, ...],
    ) -> tuple[ChangeSequence, ...]:
        m, rules = self.m, self.rules
        if len(m.sequences) != rules.sequences_per_task:
            raise TaskError(
                f"sequences: expected {rules.sequences_per_task}, got {len(m.sequences)}"
            )
        if len({s.id for s in m.sequences}) != len(m.sequences):
            raise TaskError("sequences: duplicate sequence ids")
        length = getattr(rules.sequence_length, m.split)

        used_changes: set[str] = set()
        used_references: set[str] = set()
        applied_supersedes: set[str] = set()
        sequences = []
        for seq in m.sequences:
            where = f"sequences.{seq.id}"
            if len(seq.steps) != length:
                raise TaskError(
                    f"{where}: {m.split} sequences have {length} steps, got {len(seq.steps)}"
                )
            ids = [step.change for step in seq.steps]
            if len(set(ids)) != len(ids):
                raise TaskError(f"{where}: a change appears twice")

            visible, earlier, dropped = list(public), list(private), []
            steps = []
            for number, spec in enumerate(seq.steps, start=1):
                if spec.change not in changes:
                    raise TaskError(f"{where}: unknown change {spec.change!r}")
                change = changes[spec.change]
                for node_id in change.supersedes:
                    if _file_of(node_id) in {f.path for f in visible + earlier}:
                        applied_supersedes.add(f"{change.id}:{node_id}")
                dropped += change.supersedes
                visible += change.public_checks
                tests = StepTests(
                    public=_check_set(visible, dropped),
                    new_feature=CheckSet(change.new_feature_tests),
                    existing=_check_set(earlier, dropped),
                )
                earlier += change.new_feature_tests

                applied = "+".join(sorted(ids[:number]))
                if spec.reference is not None:
                    ref_path = spec.reference
                elif applied in m.references:
                    ref_path = m.references[applied]
                    used_references.add(applied)
                else:
                    raise TaskError(
                        f"{where} step {number}: no reference; add `references.{applied}` "
                        "or a step `reference`"
                    )
                steps.append(
                    Step(
                        number=number,
                        change=change,
                        reference_path=self._rel(ref_path),
                        reference=self._program(ref_path, f"{where} step {number} reference"),
                        planted_bugs=tuple(
                            self._bug(b, f"{where} step {number}") for b in spec.planted_bugs
                        ),
                        tests=tests,
                    )
                )
            used_changes.update(ids)
            sequences.append(ChangeSequence(seq.id, tuple(steps)))

        unused = sorted(set(changes) - used_changes)
        if unused:
            raise TaskError(f"changes never used in a sequence: {unused}")
        unused = sorted(set(m.references) - used_references)
        if unused:
            raise TaskError(f"references never used by a step: {unused}")
        for change in changes.values():
            for node_id in change.supersedes:
                if f"{change.id}:{node_id}" not in applied_supersedes:
                    raise TaskError(
                        f"changes.{change.id}.supersedes: {node_id} is never in force "
                        "when this change is applied"
                    )
        return tuple(sequences)

    # -- files --

    def _rel(self, path: Path) -> str:
        """Task-relative POSIX path; rejects paths that escape the task dir."""
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            raise TaskError(f"{path} is outside the task directory") from None

    def _file(self, path: Path, where: str) -> TaskFile:
        rel = self._rel(path)
        if not path.is_file():
            raise TaskError(f"{where}: {rel} is not a file")
        return TaskFile(rel, path.read_bytes())

    def _text(self, path: Path, where: str) -> str:
        try:
            return self._file(path, where).text
        except UnicodeDecodeError:
            raise TaskError(f"{where}: {self._rel(path)} is not UTF-8") from None

    def _tests(self, paths: tuple[Path, ...], where: str) -> tuple[TaskFile, ...]:
        files = tuple(self._file(p, where) for p in paths)
        for f in files:
            name = PurePosixPath(f.path).name
            if not (name.startswith("test_") and name.endswith(".py")):
                raise TaskError(f"{where}: {f.path} must be named test_*.py for pytest")
            _test_names(f)  # raises on a syntax error
        return files

    def _program(self, directory: Path, where: str) -> dict[str, bytes]:
        rel = self._rel(directory)
        if not directory.is_dir():
            raise TaskError(f"{where}: {rel} is not a directory")
        program = {
            p.relative_to(directory).as_posix(): p.read_bytes()
            for p in sorted(directory.rglob("*"))
            if p.is_file() and not _ignored(p.relative_to(directory))
        }
        if set(program) != set(self.m.entry_files):
            raise TaskError(
                f"{where}: {rel} must contain exactly {list(self.m.entry_files)}, "
                f"got {sorted(program)}"
            )
        return program

    def _bug(self, spec: InitialBugSpec | StepBugSpec, where: str) -> PlantedBug:
        must_fail, must_pass = frozenset(spec.must_fail), frozenset(spec.must_pass)
        if not must_fail:
            raise TaskError(f"{where}: planted bug {self._rel(spec.path)} has empty must_fail")
        if must_fail & must_pass:
            raise TaskError(f"{where}: {sorted(must_fail & must_pass)} in must_fail and must_pass")
        return PlantedBug(
            self._rel(spec.path), self._program(spec.path, where), must_fail, must_pass
        )

    def _change(self, spec: ChangeSpec) -> Change:
        where = f"changes.{spec.id}"
        if not spec.new_feature_tests:
            raise TaskError(f"{where}: needs at least one new_feature_tests file")
        change = Change(
            id=spec.id,
            kind=spec.kind,
            request=self._text(spec.request, where),
            public_checks=self._tests(spec.public_checks, where),
            new_feature_tests=self._tests(spec.new_feature_tests, where),
            supersedes=spec.supersedes,
        )
        own = {f.path for f in change.public_checks + change.new_feature_tests}
        for node_id in spec.supersedes:
            path, _, name = node_id.partition("::")
            if path in own:
                raise TaskError(f"{where}.supersedes: {node_id} is one of this change's own tests")
            target = (self.root / path).resolve()
            if not name or not target.is_file():
                raise TaskError(f"{where}.supersedes: {node_id} is not path::test_name")
            if name not in _test_names(self._file(target, where)):
                raise TaskError(f"{where}.supersedes: no test {name!r} in {path}")
        return change

    # -- rules --

    def _check_entry_files(self) -> None:
        files = self.m.entry_files
        if not files or len(set(files)) != len(files):
            raise TaskError("entry_files: must be a non-empty list without duplicates")
        for name in files:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name or str(p) != name:
                raise TaskError(f"entry_files: {name!r} must be a plain relative path")

    def _check_no_symlinks(self) -> None:
        # Resolving paths already rejects links that point outside the task;
        # banning links entirely keeps the hash and the sandbox copy simple.
        for p in self.root.rglob("*"):
            if p.is_symlink():
                raise TaskError(f"symlinks are not allowed: {self._rel(p)}")

    def _check_unique_test_names(
        self,
        public: tuple[TaskFile, ...],
        private: tuple[TaskFile, ...],
        changes: dict[str, Change],
    ) -> None:
        # Test files from different folders run together in one pytest call;
        # equal basenames make pytest's default import mode fail.
        files = list(public + private)
        for change in changes.values():
            files += change.public_checks + change.new_feature_tests
        seen: dict[str, str] = {}
        for f in files:
            name = PurePosixPath(f.path).name
            if name in seen and seen[name] != f.path:
                raise TaskError(f"test files {seen[name]} and {f.path} share a file name")
            seen[name] = f.path

    def _check_no_leaks(
        self, spec: str, public: tuple[TaskFile, ...], changes: dict[str, Change]
    ) -> None:
        """Catch authoring mistakes that put later changes into writer-visible
        files: change ids, change test names, or long request lines."""
        visible = "\n".join([spec, *(f.text for f in public)])
        for change in changes.values():
            needles = {change.id}
            for f in change.public_checks + change.new_feature_tests:
                needles |= {name.split("::")[-1] for name in _test_names(f)}
            needles |= {
                line.strip()
                for line in change.request.splitlines()
                if len(line.strip()) >= _LEAK_LINE_MIN
            }
            for needle in sorted(needles):
                if needle in visible:
                    raise TaskError(
                        f"writer-visible files mention {needle!r} from change {change.id}"
                    )

    def _task_version(self) -> str:
        # Every file counts, not only the ones the manifest names, so helper
        # files such as a conftest.py can't change silently.
        h = hashlib.sha256()
        files = [
            p
            for p in self.root.rglob("*")
            if p.is_file() and not _ignored(p.relative_to(self.root))
        ]
        for p in sorted(files, key=lambda p: p.relative_to(self.root).as_posix()):
            rel = p.relative_to(self.root).as_posix()
            h.update(rel.encode("utf-8") + b"\0" + hashlib.sha256(p.read_bytes()).digest())
        return h.hexdigest()


def _check_set(files: list[TaskFile], dropped: list[str]) -> CheckSet:
    """A CheckSet keeping only the deselections that name one of its files."""
    paths = {f.path for f in files}
    return CheckSet(tuple(files), tuple(n for n in dropped if _file_of(n) in paths))


def _file_of(node_id: str) -> str:
    return node_id.partition("::")[0]


def _test_names(f: TaskFile) -> set[str]:
    """Test functions pytest would collect: `test*` functions and `test*`
    methods of `Test*` classes ("Class::method")."""
    try:
        tree = ast.parse(f.content, filename=f.path)
    except SyntaxError as exc:
        raise TaskError(f"{f.path}: syntax error: {exc}") from None
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test"):
                names.add(node.name)
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            names |= {
                f"{node.name}::{item.name}"
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                and item.name.startswith("test")
            }
    return names


def _ignored(rel: Path) -> bool:
    return bool(_IGNORED_NAMES & set(rel.parts)) or rel.suffix in _IGNORED_SUFFIXES
