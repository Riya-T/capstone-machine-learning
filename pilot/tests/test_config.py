import copy
import random
import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from pipeline.config import ConfigError, ExperimentConfig, load_config, stable_hash

from .helpers import minimal, write

CONFIGS_DIR = Path(__file__).resolve().parents[1] / "configs"


def load(tmp_path: Path, data: dict) -> ExperimentConfig:
    return load_config(write(tmp_path, data))


# --- loading and conversion -------------------------------------------------


def test_loads_and_converts_types(tmp_path):
    cfg = load(tmp_path, minimal())
    assert cfg.tasks.include == ("a",)
    assert cfg.sandbox.cpus == 1.0 and isinstance(cfg.sandbox.cpus, float)
    assert cfg.editor.view_transform == "none"  # default applied
    assert cfg.writer.backend.base_url is None


def test_paths_resolve_relative_to_config_file(tmp_path, monkeypatch):
    monkeypatch.chdir("/")  # the working directory must not matter
    cfg = load(tmp_path / "configs", minimal())
    assert cfg.tasks.dir == (tmp_path / "configs" / "tasks").resolve()
    assert cfg.runs_dir == (tmp_path / "configs" / "runs").resolve()


def test_output_path_may_be_missing_but_input_path_must_exist(tmp_path):
    data = minimal()
    data["runs_dir"] = "not/yet/created"
    load(tmp_path, data)  # fine
    data["tasks"]["dir"] = "missing"
    with pytest.raises(ConfigError, match=r"tasks\.dir: path does not exist"):
        load(tmp_path, data)


# --- strictness -------------------------------------------------------------


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["editor"].pop("reps"), r"editor\.reps: missing required key"),
        (lambda d: d["editor"].update(rep=3), r"editor\.rep: unknown key"),
        (lambda d: d.update(seed="1"), r"seed: expected an integer"),
        (lambda d: d.update(seed=True), r"seed: expected an integer"),
        (lambda d: d.update(allow_dirty=1), r"allow_dirty: expected true/false"),
        (lambda d: d["scorer"].update(pairing_mode="best"), r"scorer\.pairing_mode: must be"),
        (lambda d: d["tasks"].update(include="a"), r"tasks\.include: expected a list"),
        (lambda d: d["tasks"].update(include=["a", "a"]), r"tasks: include: contains dup"),
        (lambda d: d["editor"]["budget"].update(max_turns=0), r"editor\.budget: max_turns"),
        (lambda d: d["writer"]["backend"].update(temperature=-1), r"writer\.backend: temp"),
        (lambda d: d["scorer"].update(reps=[]), r"scorer: reps: must be a non-empty"),
        (lambda d: d.update(schema_version=2), r"schema_version: expected 1"),
        (lambda d: d.update(base_dir="/x"), r"base_dir: unknown key"),
        (lambda d: d["editor"]["backend"].update(max_retries=-1), r"max_retries: must be >= 0"),
        (
            lambda d: d["tasks"]["sequence_length"].update(eval=0),
            r"tasks\.sequence_length: eval: must be > 0",
        ),
        (lambda d: d["writer"].pop("prompt_template"), r"writer\.prompt_template: missing"),
    ],
)
def test_invalid_configs_raise_with_location(tmp_path, mutate, message):
    data = minimal()
    mutate(data)
    with pytest.raises(ConfigError, match=message):
        load(tmp_path, data)


def test_openai_compat_requires_base_url(tmp_path):
    data = minimal()
    data["editor"]["backend"]["kind"] = "openai_compat"
    with pytest.raises(ConfigError, match=r"editor\.backend: base_url: required"):
        load(tmp_path, data)
    data["editor"]["backend"]["base_url"] = "http://localhost:8000/v1"
    with pytest.raises(
        ConfigError, match=r"editor\.backend: fixtures: only valid when kind is mock"
    ):
        load(tmp_path, data)
    del data["editor"]["backend"]["fixtures"]
    assert load(tmp_path, data).editor.backend.base_url == "http://localhost:8000/v1"


def test_mock_requires_fixtures(tmp_path):
    data = minimal()
    del data["writer"]["backend"]["fixtures"]
    with pytest.raises(ConfigError, match=r"writer\.backend: fixtures: required when kind is mock"):
        load(tmp_path, data)


def test_optional_fields_accept_null(tmp_path):
    data = minimal()
    data["scorer"]["per_task_cap"] = None
    data["scorer"]["reps"] = [0]
    cfg = load(tmp_path, data)
    assert cfg.scorer.per_task_cap is None
    assert cfg.scorer.reps == (0,)


def test_config_is_immutable(tmp_path):
    cfg = load(tmp_path, minimal())
    with pytest.raises(AttributeError):
        cfg.seed = 2  # type: ignore[misc]


# --- extends ----------------------------------------------------------------


def test_extends_deep_merges_and_child_wins(tmp_path):
    write(tmp_path, minimal(), "base.yaml")
    child = {"extends": "base.yaml", "editor": {"budget": {"max_turns": 5}}}
    cfg = load_config(write(tmp_path, child, "child.yaml"))
    assert cfg.editor.budget.max_turns == 5  # overridden
    assert cfg.editor.budget.max_total_tokens == 1000  # inherited from the same mapping
    assert cfg.editor.reps == 3  # inherited


def test_extends_replaces_lists_rather_than_appending(tmp_path):
    write(tmp_path, minimal(), "base.yaml")
    child = {"extends": "base.yaml", "tasks": {"include": ["b", "c"]}}
    assert load_config(write(tmp_path, child, "child.yaml")).tasks.include == ("b", "c")


def test_extends_chain_hashes_like_flat_file(tmp_path):
    flat = minimal()
    flat["seed"] = 7
    write(tmp_path, minimal(), "base.yaml")
    write(tmp_path, {"extends": "base.yaml", "name": "t"}, "mid.yaml")
    chained = load_config(write(tmp_path, {"extends": "mid.yaml", "seed": 7}, "leaf.yaml"))
    assert chained.config_hash == load_config(write(tmp_path, flat, "flat.yaml")).config_hash


def test_extends_cycle_raises(tmp_path):
    write(tmp_path, {"extends": "b.yaml"}, "a.yaml")
    write(tmp_path, {"extends": "a.yaml"}, "b.yaml")
    with pytest.raises(ConfigError, match="cycle detected: a.yaml -> b.yaml -> a.yaml"):
        load_config(tmp_path / "a.yaml")


def test_extends_must_stay_in_same_directory(tmp_path):
    write(tmp_path / "other", minimal(), "base.yaml")
    child = write(tmp_path, {"extends": "other/base.yaml"}, "child.yaml")
    with pytest.raises(ConfigError, match="same directory"):
        load_config(child)


# --- hashing ----------------------------------------------------------------


def test_hash_changes_with_any_value(tmp_path):
    base = load(tmp_path, minimal()).config_hash
    data = minimal()
    data["editor"]["backend"]["temperature"] = 0.6
    assert load(tmp_path, data).config_hash != base


def test_hash_ignores_int_vs_float_spelling(tmp_path):
    # `cpus: 1` and `cpus: 1.0` are the same setting and must not split results.
    a = minimal()
    b = minimal()
    b["sandbox"]["cpus"] = 1.0
    assert load(tmp_path / "a", a).config_hash == load(tmp_path / "b", b).config_hash


def test_hash_is_independent_of_checkout_location(tmp_path):
    first = write(tmp_path / "laptop" / "configs", minimal())
    shutil.copytree(tmp_path / "laptop", tmp_path / "workstation")
    second = tmp_path / "workstation" / "configs" / first.name
    assert load_config(first).config_hash == load_config(second).config_hash
    assert load_config(first).to_dict()["tasks"]["dir"] == "tasks"


def test_component_hash_isolates_sections(tmp_path):
    a = load(tmp_path / "a", minimal())
    data = minimal()
    data["editor"]["reps"] = 1
    b = load(tmp_path / "b", data)
    assert a.component_hash(a.writer) == b.component_hash(b.writer)
    assert a.component_hash(a.editor) != b.component_hash(b.editor)


def test_hash_is_independent_of_field_declaration_order():
    @dataclass(frozen=True)
    class Before:
        x: int
        y: str

    @dataclass(frozen=True)
    class After:  # same fields, reordered in the source
        y: str
        x: int

    base = Path("/")
    assert stable_hash(Before(1, "a"), base) == stable_hash(After("a", 1), base)


def _shuffled(value, rng: random.Random):
    """Same data with every mapping's key order permuted."""
    if isinstance(value, dict):
        keys = list(value)
        rng.shuffle(keys)
        return {k: _shuffled(value[k], rng) for k in keys}
    return value


@settings(max_examples=25, deadline=None)
@given(st.randoms(use_true_random=False))
def test_hash_is_independent_of_key_order(tmp_path_factory, rng):
    directory = tmp_path_factory.mktemp("order")
    reference = load(directory / "ref", minimal()).config_hash
    shuffled = _shuffled(copy.deepcopy(minimal()), rng)
    assert load(directory / "shuffled", shuffled).config_hash == reference


# --- committed configs ------------------------------------------------------


@pytest.mark.parametrize("name", ["pilot_mock.yaml", "pilot_local.yaml"])
def test_committed_configs_load(name):
    cfg = load_config(CONFIGS_DIR / name)
    assert cfg.allow_dirty is True
    assert cfg.editor.backend.temperature > 0  # reps must be able to differ
    assert cfg.scorer.rule == "weak_dominance"
    assert cfg.scorer.pairing_mode == "best_vs_worst"


def test_committed_configs_contain_no_secrets():
    for path in CONFIGS_DIR.glob("*.yaml"):
        text = path.read_text().lower()
        assert "api_key:" not in text and "sk-" not in text, path.name
