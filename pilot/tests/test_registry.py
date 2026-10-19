"""Unit tests for pipeline.registry: task manifest rules (splits, families,
sequences, shared references, supersedes, leak checks), cumulative test sets,
task_version and prompt_version, and the writer prompt, including that later
changes and private tests never reach it. Uses small synthetic tasks plus the
real record_store task.

Usage:
    uv run pytest tests/test_registry.py
"""

import shutil
import string
from pathlib import Path

import pytest
import yaml

from pipeline.config import ConfigError, SequenceLengths, TasksConfig, load_config
from pipeline.registry import (
    TaskError,
    build_writer_prompt,
    load_task,
    load_tasks,
    load_template,
    prompt_version,
)

PILOT = Path(__file__).resolve().parents[1]
TEMPLATE = string.Template("files: $entry_files\nspec: $spec\nchecks: $public_checks")


def rules(tasks_dir: Path, include=("t",), sequences_per_task=2) -> TasksConfig:
    return TasksConfig(
        dir=tasks_dir,
        include=tuple(include),
        sequence_length=SequenceLengths(train=2, dev=2, eval=3),
        sequences_per_task=sequences_per_task,
    )


# --- synthetic tasks --------------------------------------------------------


def make_task(tasks_dir: Path, task_id: str = "t", edit=None, **manifest_overrides) -> Path:
    """Write a small valid task: changes ca and cb, sequences [ca, cb] and
    [cb, ca], and a shared reference for {ca, cb} used by both step 2s.
    `edit(root, manifest)` can change files or the manifest before writing."""
    root = tasks_dir / task_id
    files = {
        "spec.md": "Write m.py with a function f.",
        "public/test_pub.py": "def test_pub():\n    pass\n",
        "private/test_priv.py": "def test_priv():\n    pass\n\n\ndef test_old_rule():\n    pass\n",
        "ref/v0/m.py": "def f(): return 0\n",
        "ref/ca/m.py": "def f(): return 1\n",
        "ref/cb/m.py": "def f(): return 2\n",
        "ref/ca_cb/m.py": "def f(): return 3\n",
        "bugs/b0/m.py": "def f(): return -1\n",
    }
    for c in ("ca", "cb"):
        files[f"changes/{c}/request.md"] = f"Change {c}: make f return something new please."
        files[f"changes/{c}/test_{c}_pub.py"] = f"def test_{c}_pub():\n    pass\n"
        files[f"changes/{c}/test_{c}_new.py"] = f"def test_{c}_new():\n    pass\n"
    for rel, text in files.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)

    manifest = {
        "schema_version": 1,
        "id": task_id,
        "family": task_id,
        "split": "train",
        "entry_files": ["m.py"],
        "spec": "spec.md",
        "public_checks": ["public/test_pub.py"],
        "private_tests": ["private/test_priv.py"],
        "reference": "ref/v0",
        "planted_bugs": [{"path": "bugs/b0", "must_fail": ["initial"]}],
        "changes": [
            {
                "id": c,
                "kind": "k",
                "request": f"changes/{c}/request.md",
                "public_checks": [f"changes/{c}/test_{c}_pub.py"],
                "new_feature_tests": [f"changes/{c}/test_{c}_new.py"],
            }
            for c in ("ca", "cb")
        ],
        "references": {"ca": "ref/ca", "cb": "ref/cb", "ca+cb": "ref/ca_cb"},
        "sequences": [
            {"id": "s1", "steps": [{"change": "ca"}, {"change": "cb"}]},
            {"id": "s2", "steps": [{"change": "cb"}, {"change": "ca"}]},
        ],
    }
    manifest.update(manifest_overrides)
    if edit:
        edit(root, manifest)
    (root / "task.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))
    return root


def load(tasks_dir: Path, task_id: str = "t", **kw):
    return load_task(tasks_dir / task_id, rules(tasks_dir, include=(task_id,), **kw))


def test_synthetic_task_loads(tmp_path):
    make_task(tmp_path)
    task = load(tmp_path)
    assert [s.id for s in task.sequences] == ["s1", "s2"]
    assert task.reference == {"m.py": b"def f(): return 0\n"}


def test_sequences_reaching_the_same_change_set_share_a_reference(tmp_path):
    make_task(tmp_path)
    task = load(tmp_path)
    s1, s2 = task.sequence("s1").steps, task.sequence("s2").steps
    assert [s.reference_path for s in s1] == ["ref/ca", "ref/ca_cb"]
    assert [s.reference_path for s in s2] == ["ref/cb", "ref/ca_cb"]


def test_step_reference_overrides_the_shared_one(tmp_path):
    def edit(root, m):
        (root / "ref/cb_then_ca").mkdir()
        (root / "ref/cb_then_ca/m.py").write_text("def f(): return 4\n")
        m["sequences"][1]["steps"][1]["reference"] = "ref/cb_then_ca"

    make_task(tmp_path, edit=edit)
    task = load(tmp_path)
    assert task.sequence("s1").steps[1].reference_path == "ref/ca_cb"
    assert task.sequence("s2").steps[1].reference_path == "ref/cb_then_ca"


def test_check_sets_are_cumulative(tmp_path):
    make_task(tmp_path)
    step2 = load(tmp_path).sequence("s1").steps[1]
    paths = lambda cs: [f.path for f in cs.files]  # noqa: E731
    assert paths(step2.tests.public) == [
        "public/test_pub.py",
        "changes/ca/test_ca_pub.py",
        "changes/cb/test_cb_pub.py",
    ]
    assert paths(step2.tests.new_feature) == ["changes/cb/test_cb_new.py"]
    assert paths(step2.tests.existing) == ["private/test_priv.py", "changes/ca/test_ca_new.py"]


def test_supersedes_drops_a_test_from_this_step_on(tmp_path):
    def edit(root, m):
        m["changes"][1]["supersedes"] = ["private/test_priv.py::test_old_rule"]  # cb

    make_task(tmp_path, edit=edit)
    task = load(tmp_path)
    s1, s2 = task.sequence("s1").steps, task.sequence("s2").steps
    dropped = ("private/test_priv.py::test_old_rule",)
    assert [s.tests.existing.deselect for s in s1] == [(), dropped]  # cb is step 2
    assert [s.tests.existing.deselect for s in s2] == [dropped, dropped]  # cb is step 1
    # Deselections are kept only in sets that contain the file.
    assert s2[0].tests.public.deselect == ()


# --- rule violations --------------------------------------------------------


def _set(path_and_value):
    def edit(root, m):
        *keys, value = path_and_value
        target = m
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value

    return edit


def _outside_spec(root, m):
    (root.parent / "outside.md").write_text("exists, but outside the task")
    m["spec"] = "../outside.md"


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        (_set(("id", "other")), "must match the directory name"),
        (_set(("color", "red")), r"color: unknown key"),
        (_set(("split", "test")), r"split: must be one of"),
        (_set(("spec", "missing.md")), r"spec: path does not exist"),
        (_outside_spec, "outside the task directory"),
        (_set(("entry_files", ["../m.py"])), "must be a plain relative path"),
        (_set(("entry_files", ["m.py", "m.py"])), "without duplicates"),
        (_set(("reference", "ref")), r"reference: ref must contain exactly \['m.py'\]"),
        (_set(("changes", 1, "id", "ca")), "duplicate change ids"),
        (_set(("changes", 1, "new_feature_tests", [])), "needs at least one new_feature_tests"),
        (_set(("sequences", 0, "steps", 1, "change", "ca")), "a change appears twice"),
        (_set(("sequences", 0, "steps", 1, "change", "zz")), "unknown change 'zz'"),
        (_set(("sequences", 0, "steps", [{"change": "ca"}])), "train sequences have 2 steps"),
        (_set(("references", "ca+cb", None)), r"references\.ca\+cb: expected a path"),
        (_set(("planted_bugs", 0, "must_fail", ["existing"])), r"must_fail\[0\]: must be one of"),
        (_set(("planted_bugs", 0, "must_fail", [])), "has empty must_fail"),
        (_set(("planted_bugs", 0, "must_pass", ["initial"])), "in must_fail and must_pass"),
        (_set(("public_checks", ["spec.md"])), r"must be named test_\*\.py"),
    ],
)
def test_manifest_errors_are_reported(tmp_path, edit, message):
    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match=message):
        load(tmp_path)


def test_missing_shared_reference_names_the_change_set(tmp_path):
    def edit(root, m):
        del m["references"]["ca+cb"]

    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match=r"s1 step 2: no reference; add `references\.ca\+cb`"):
        load(tmp_path)


def test_unused_shared_reference_is_an_error(tmp_path):
    make_task(tmp_path, edit=_set(("references", "cb+zz", "ref/cb")))
    with pytest.raises(TaskError, match=r"references never used by a step: \['cb\+zz'\]"):
        load(tmp_path)


def test_unused_change_is_an_error(tmp_path):
    def edit(root, m):
        m["sequences"] = [
            {"id": "s1", "steps": [{"change": "ca"}, {"change": "ca"}]},
        ]

    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match="expected 2, got 1"):
        load(tmp_path)

    def edit_two(root, m):
        (root / "changes/cc").mkdir()
        (root / "changes/cc/request.md").write_text("Something completely different here.")
        (root / "changes/cc/test_cc_new.py").write_text("def test_cc_new():\n    pass\n")
        m["changes"].append(
            {
                "id": "cc",
                "kind": "k",
                "request": "changes/cc/request.md",
                "new_feature_tests": ["changes/cc/test_cc_new.py"],
            }
        )

    make_task(tmp_path, edit=edit_two)
    with pytest.raises(TaskError, match=r"changes never used in a sequence: \['cc'\]"):
        load(tmp_path)


def test_wrong_number_of_sequences(tmp_path):
    make_task(tmp_path)
    with pytest.raises(TaskError, match="sequences: expected 3, got 2"):
        load(tmp_path, sequences_per_task=3)


def test_eval_split_needs_longer_sequences(tmp_path):
    make_task(tmp_path, split="eval")
    with pytest.raises(TaskError, match="eval sequences have 3 steps, got 2"):
        load(tmp_path)


def test_symlinks_are_rejected(tmp_path):
    make_task(tmp_path, edit=lambda root, m: (root / "link.md").symlink_to(root / "spec.md"))
    with pytest.raises(TaskError, match="symlinks are not allowed: link.md"):
        load(tmp_path)


def test_test_file_names_must_be_unique(tmp_path):
    def edit(root, m):
        (root / "changes/ca/test_pub.py").write_text("def test_other():\n    pass\n")
        m["changes"][0]["public_checks"] = ["changes/ca/test_pub.py"]

    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match="share a file name"):
        load(tmp_path)


def test_syntax_error_in_a_test_file_is_reported(tmp_path):
    make_task(tmp_path, edit=lambda root, m: (root / "private/test_priv.py").write_text("def ("))
    with pytest.raises(TaskError, match="private/test_priv.py: syntax error"):
        load(tmp_path)


@pytest.mark.parametrize(
    ("node_id", "message"),
    [
        ("changes/cb/test_cb_new.py::test_cb_new", "one of this change's own tests"),
        ("private/test_priv.py::test_nope", "no test 'test_nope'"),
        ("private/test_priv.py", "is not path::test_name"),
    ],
)
def test_bad_supersedes(tmp_path, node_id, message):
    make_task(tmp_path, edit=lambda root, m: m["changes"][1].update(supersedes=[node_id]))
    with pytest.raises(TaskError, match=message):
        load(tmp_path)


def test_supersedes_must_be_in_force_somewhere(tmp_path):
    # cc supersedes a test of cb, but cc only ever runs before cb.
    def edit(root, m):
        (root / "changes/cc").mkdir()
        (root / "changes/cc/request.md").write_text("Make f raise for negative inputs today.")
        (root / "changes/cc/test_cc_new.py").write_text("def test_cc_new():\n    pass\n")
        m["changes"].append(
            {
                "id": "cc",
                "kind": "k",
                "request": "changes/cc/request.md",
                "new_feature_tests": ["changes/cc/test_cc_new.py"],
                "supersedes": ["changes/cb/test_cb_new.py::test_cb_new"],
            }
        )
        m["sequences"] = [
            {"id": "s1", "steps": [{"change": "ca"}, {"change": "cc"}]},
            {"id": "s2", "steps": [{"change": "cc"}, {"change": "cb"}]},
        ]
        m["references"] = {"ca": "ref/ca", "cc": "ref/cb", "ca+cc": "ref/ca_cb", "cb+cc": "ref/v0"}

    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match="is never in force when this change is applied"):
        load(tmp_path)


@pytest.mark.parametrize(
    "leak",
    [
        "Also handle ca later.",  # a change id
        "See test_cb_new for details.",  # a change test name
        "Change cb: make f return something new please.",  # a request line
    ],
)
def test_leaks_into_writer_visible_files_are_rejected(tmp_path, leak):
    make_task(tmp_path, edit=lambda root, m: (root / "spec.md").write_text(leak))
    with pytest.raises(TaskError, match="writer-visible files mention"):
        load(tmp_path)


def test_leak_check_covers_public_checks_too(tmp_path):
    def edit(root, m):
        (root / "public/test_pub.py").write_text("def test_pub():\n    assert 'cb'\n")

    make_task(tmp_path, edit=edit)
    with pytest.raises(TaskError, match="mention 'cb' from change cb"):
        load(tmp_path)


# --- splits -----------------------------------------------------------------


def test_family_in_two_splits_is_rejected_even_if_not_included(tmp_path):
    make_task(tmp_path, "a", family="fam")
    make_task(tmp_path, "b", family="fam", split="eval")
    with pytest.raises(TaskError, match="family 'fam' spans several splits"):
        load_tasks(rules(tmp_path, include=("a",)))


def test_family_in_one_split_is_fine(tmp_path):
    make_task(tmp_path, "a", family="fam")
    make_task(tmp_path, "b", family="fam")
    assert set(load_tasks(rules(tmp_path, include=("a", "b")))) == {"a", "b"}


def test_included_task_must_exist(tmp_path):
    make_task(tmp_path, "a")
    with pytest.raises(TaskError, match=r"tasks not found .*\['nope'\]"):
        load_tasks(rules(tmp_path, include=("a", "nope")))


# --- versions ---------------------------------------------------------------


def test_task_version_tracks_every_file_but_ignores_caches(tmp_path):
    root = make_task(tmp_path)
    before = load(tmp_path).task_version
    (root / "__pycache__").mkdir()
    (root / "__pycache__/x.pyc").write_bytes(b"\0")
    assert load(tmp_path).task_version == before
    (root / "conftest.py").write_text("# helper not named in the manifest\n")
    assert load(tmp_path).task_version != before


# --- writer prompt template -------------------------------------------------


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("$spec $public_checks", r"got \['public_checks', 'spec'\]"),
        ("$entry_files $spec $public_checks $changes", "placeholders must be exactly"),
        ("$entry_files $spec $public_checks costs $5", "invalid placeholder"),
    ],
)
def test_template_placeholders_are_checked(tmp_path, text, message):
    path = tmp_path / "t.md"
    path.write_text(text)
    with pytest.raises(ConfigError, match=message):
        load_template(path)


def test_template_allows_escaped_dollar(tmp_path):
    path = tmp_path / "t.md"
    path.write_text("$entry_files $spec $public_checks costs $$5")
    load_template(path)


# --- the real record_store task ---------------------------------------------


@pytest.fixture(scope="module")
def pilot():
    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    return cfg, task, load_template(cfg.writer.prompt_template)


def test_record_store_structure(pilot):
    _, task, _ = pilot
    assert (task.family, task.split) == ("record_store", "train")
    assert {c.kind for c in task.changes.values()} == {
        "concurrency_control",
        "atomicity",
        "validation_rule",
    }
    assert [[s.change.id for s in q.steps] for q in task.sequences] == [
        ["c_conflict", "c_txn"],
        ["c_unique", "c_conflict"],
    ]
    dropped = ("private/test_initial.py::test_duplicate_emails_are_allowed",)
    assert [s.tests.existing.deselect for s in task.sequence("s2").steps] == [dropped, dropped]
    assert all(s.tests.existing.deselect == () for s in task.sequence("s1").steps)


def test_writer_prompt_contains_only_spec_and_public_checks(pilot):
    _, task, template = pilot
    prompt = build_writer_prompt(task.writer_view(), template)
    assert task.spec.strip() in prompt
    assert task.public_checks[0].text.rstrip() in prompt

    hidden = [f.text for f in task.private_tests]
    for change in task.changes.values():
        assert change.id not in prompt
        hidden.append(change.request)
        hidden += [f.text for f in change.public_checks + change.new_feature_tests]
    for text in hidden:
        for line in text.splitlines():
            line = line.strip()
            # Skip lines short or generic enough to legitimately also appear
            # in the spec or the public checks (imports, fixtures, asserts).
            if (
                len(line) >= 25
                and line not in task.spec
                and all(line not in f.text for f in task.public_checks)
            ):
                assert line not in prompt, line
    for word in ("ConflictError", "get_version", "transaction", "casefold", "version"):
        assert word not in prompt


def test_writer_prompt_ignores_every_hidden_file(pilot, tmp_path):
    """Rewrite every file the writer must not see: the prompt and
    prompt_version stay identical while task_version changes."""
    cfg, task, template = pilot
    shutil.copytree(task.root, tmp_path / "record_store")
    copy_rules = rules(tmp_path, include=("record_store",))
    visible = {"spec.md", *(f.path for f in task.public_checks)}
    for path in (tmp_path / "record_store").rglob("*"):
        rel = path.relative_to(tmp_path / "record_store").as_posix()
        if path.is_file() and rel not in visible and path.suffix in {".py", ".md"}:
            path.write_text(path.read_text() + "\n# reviewer fix\n")
    changed = load_task(tmp_path / "record_store", copy_rules)

    before = build_writer_prompt(task.writer_view(), template)
    after = build_writer_prompt(changed.writer_view(), template)
    assert after == before
    assert prompt_version(after) == prompt_version(before)
    assert changed.task_version != task.task_version


def test_prompt_version_changes_with_spec_public_checks_or_template(pilot, tmp_path):
    _, task, template = pilot
    base = prompt_version(build_writer_prompt(task.writer_view(), template))

    shutil.copytree(task.root, tmp_path / "record_store")
    copy_rules = rules(tmp_path, include=("record_store",))
    spec = tmp_path / "record_store" / "spec.md"
    spec.write_text(spec.read_text() + "\nNames are stored as given.\n")
    edited = load_task(tmp_path / "record_store", copy_rules)
    assert prompt_version(build_writer_prompt(edited.writer_view(), template)) != base

    public = tmp_path / "record_store" / task.public_checks[0].path
    spec.write_text(task.spec)
    public.write_text(public.read_text() + "\n\ndef test_extra():\n    pass\n")
    edited = load_task(tmp_path / "record_store", copy_rules)
    assert prompt_version(build_writer_prompt(edited.writer_view(), template)) != base

    other = string.Template(template.template + "\nThink carefully.")
    assert prompt_version(build_writer_prompt(task.writer_view(), other)) != base


def test_prompt_is_deterministic(pilot):
    _, task, template = pilot
    first = build_writer_prompt(task.writer_view(), template)
    assert build_writer_prompt(task.writer_view(), template) == first
