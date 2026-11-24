"""Tests for harness.datasets and the scripts' --dataset option: what a
dataset records, that its files are never replaced, that every dataset in
harness/data/ still matches its manifest, and filter_pairs writing a
dataset end to end.

Usage:
    uv run pytest tests/test_datasets.py
"""

import json
from pathlib import Path

import pytest

import harness.datasets as ds
from harness.datasets import (
    DatasetError,
    add_file,
    datasets,
    merge_pairs,
    save_output,
    validate_pairs,
    verify,
)

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("folder", datasets(), ids=lambda p: p.name)
def test_every_dataset_in_the_repository_matches_its_manifest(folder):
    assert verify(folder) == []


@pytest.fixture
def data(tmp_path, monkeypatch):
    folder = tmp_path / "data"
    monkeypatch.setattr(ds, "DATA_DIR", folder)
    return folder


def test_add_file_writes_the_file_and_records_it(data):
    content = b'{"a": 1}\n\n{"a": 2}\n'
    path = add_file("train-v2", "pairs.jsonl", content, command=["scripts/x.py", "--flag"])

    assert path == data / "train-v2" / "pairs.jsonl" and path.read_bytes() == content
    manifest = json.loads((data / "train-v2" / "MANIFEST.json").read_text())
    assert manifest["dataset"] == "train-v2"
    (entry,) = manifest["files"]
    assert entry["name"] == "pairs.jsonl"
    assert entry["bytes"] == len(content)
    assert entry["rows"] == 2  # blank lines don't count
    assert entry["command"] == "python scripts/x.py --flag"
    assert entry["created"].endswith("Z")
    assert len(entry["git_commit"]) == 40
    assert verify(data / "train-v2") == []


def test_more_files_can_be_added_but_none_replaced(data):
    add_file("v1", "a.jsonl", b"{}\n", command=[])
    add_file("v1", "b.json", b"{}", command=[])
    add_file("v1", "a.jsonl", b"{}\n", command=[])  # the same content again: nothing changes

    manifest = json.loads((data / "v1" / "MANIFEST.json").read_text())
    assert [e["name"] for e in manifest["files"]] == ["a.jsonl", "b.json"]
    assert manifest["files"][1]["rows"] is None
    with pytest.raises(DatasetError, match="never replaced"):
        add_file("v1", "a.jsonl", b'{"changed": 1}\n', command=[])
    assert (data / "v1" / "a.jsonl").read_bytes() == b"{}\n"


@pytest.mark.parametrize(
    ("dataset", "filename", "message"),
    [
        ("Train V2", "a.jsonl", "dataset 'Train V2'"),
        ("v1", "../escape.jsonl", "file name"),
        ("v1", "MANIFEST.json", "file name"),
    ],
)
def test_bad_names_are_refused(data, dataset, filename, message):
    with pytest.raises(DatasetError, match=message):
        add_file(dataset, filename, b"{}\n", command=[])
    assert not data.exists()


def test_large_files_are_refused(data, monkeypatch):
    monkeypatch.setattr(ds, "MAX_BYTES", 10)

    with pytest.raises(DatasetError, match="too big for git"):
        add_file("v1", "store.jsonl", b"x" * 11, command=[])


def test_the_recorded_command_hides_the_repository_and_home_paths(data, monkeypatch):
    monkeypatch.setattr(ds.Path, "home", lambda: Path("/home/someone"))
    argv = [f"{ds.HARNESS}/scripts/filter_pairs.py", "/home/someone/pairs.jsonl", "--dataset"]
    add_file("v1", "a.jsonl", b"{}\n", command=argv)

    (entry,) = json.loads((data / "v1" / "MANIFEST.json").read_text())["files"]
    assert entry["command"] == "python scripts/filter_pairs.py ~/pairs.jsonl --dataset"


def test_save_output_writes_to_exactly_one_place(data, tmp_path):
    out = tmp_path / "scratch" / "pairs.jsonl"
    assert save_output("{}\n", out=out, dataset=None, filename="pairs.jsonl") == out
    assert out.read_text() == "{}\n" and not data.exists()

    for out_, dataset in ((None, None), (out, "v1")):
        with pytest.raises(DatasetError, match="not both"):
            save_output("{}\n", out=out_, dataset=dataset, filename="pairs.jsonl")


def test_verify_finds_changed_missing_and_unlisted_files(data):
    add_file("v1", "a.jsonl", b"{}\n", command=[])
    add_file("v1", "b.jsonl", b"{}\n", command=[])
    (data / "v1" / "a.jsonl").write_text('{"edited": 1}\n')
    (data / "v1" / "b.jsonl").unlink()
    (data / "v1" / "extra.jsonl").write_text("{}\n")

    assert verify(data / "v1") == [
        "v1/extra.jsonl: in the folder but not in MANIFEST.json",
        "v1/a.jsonl: changed since it was added",
        "v1/b.jsonl: missing",
    ]
    (data / "v2").mkdir()
    assert verify(data / "v2") == ["v2: no MANIFEST.json"]


def test_verify_command_exit_code(data, capsys):
    add_file("v1", "a.jsonl", b"{}\n", command=[])
    assert ds.main(["verify"]) == 0

    (data / "v1" / "a.jsonl").write_text("{}\n{}\n")
    assert ds.main(["verify"]) == 1
    assert "v1/a.jsonl: changed" in capsys.readouterr().err


def test_add_command_keeps_each_files_name(data, tmp_path):
    source = tmp_path / "pairs_cap8_all.jsonl"
    source.write_text("{}\n")

    assert ds.main(["add", "train-v1", str(source)]) == 0
    assert (data / "train-v1" / "pairs_cap8_all.jsonl").read_text() == "{}\n"


def _pair(task, chosen_wins):
    """A scorer row whose chosen program wins `chosen_wins` of 3 reps."""
    chosen = [[2, 2, 2]]
    rejected = [[1 if i < chosen_wins else 3 for i in range(3)]]
    return {
        "task_id": task,
        "prompt": "write it",
        "chosen": f"```python file=a.py\nx = {task!r}\n```",
        "rejected": f"```python file=a.py\ndef f():\n    return {task!r}\n```",
        "chosen_scores": chosen,
        "rejected_scores": rejected,
    }


def _merge_pair(task, chosen_id="chosen", rejected_id="rejected", source=True, version="v1"):
    row = _pair(task, 3)
    row.update(chosen_id=chosen_id, rejected_id=rejected_id)
    if source:
        settings = {"scorer": {"rule": "aggregate"}}
        row["source"] = {
            "settings_hash": ds.settings_hash(settings),
            "settings": settings,
            "task_version": version,
            "prompt_version": "prompt-v1",
        }
    return row


def _write_pairs(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    return path


def test_validate_pairs_accepts_compatible_sources_and_reports_counts(tmp_path):
    first = _write_pairs(tmp_path / "first.jsonl", [_merge_pair("t1"), _merge_pair("t2")])
    second = _write_pairs(tmp_path / "second.jsonl", [_merge_pair("t1", "c2", "r2")])

    summary = validate_pairs([first, second])

    assert summary.pair_count == 3
    assert summary.per_task == {"t1": 2, "t2": 1}
    assert summary.settings_hash == ds.settings_hash({"scorer": {"rule": "aggregate"}})
    assert summary.legacy_rows == 0


def test_merge_pairs_preserves_rows_and_refuses_to_overwrite_an_input(tmp_path):
    first = _write_pairs(tmp_path / "first.jsonl", [_merge_pair("t1")])
    second = _write_pairs(tmp_path / "second.jsonl", [_merge_pair("t2")])
    out = tmp_path / "scratch" / "combined.jsonl"

    summary = merge_pairs([first, second], out)

    assert summary.pair_count == 2
    assert [json.loads(line)["task_id"] for line in out.read_text().splitlines()] == ["t1", "t2"]
    with pytest.raises(DatasetError, match="also one of the input"):
        merge_pairs([first], first)
    assert json.loads(first.read_text().splitlines()[0])["task_id"] == "t1"


def test_merge_pairs_keeps_outputs_out_of_the_tracked_data_directory(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(ds, "DATA_DIR", data_dir)
    source = _write_pairs(tmp_path / "source.jsonl", [_merge_pair("t1")])

    with pytest.raises(DatasetError, match="outside harness/data"):
        merge_pairs([source], data_dir / "combined.jsonl")
    assert not (data_dir / "combined.jsonl").exists()


def test_pair_validation_rejects_mixed_settings_and_tampered_source_settings(tmp_path):
    settings = {"scorer": {"rule": "strict"}}
    mismatch = _merge_pair("t2")
    mismatch["source"]["settings"] = settings
    mismatch["source"]["settings_hash"] = ds.settings_hash(settings)
    first = _write_pairs(tmp_path / "first.jsonl", [_merge_pair("t1")])
    second = _write_pairs(tmp_path / "second.jsonl", [mismatch])

    with pytest.raises(DatasetError, match="incompatible settings_hash"):
        validate_pairs([first, second])

    mismatch["source"]["settings_hash"] = "0" * 64
    tampered = _write_pairs(tmp_path / "tampered.jsonl", [mismatch])
    with pytest.raises(DatasetError, match="does not match source.settings"):
        validate_pairs([tampered])
    out = tmp_path / "failed-merge.jsonl"
    with pytest.raises(DatasetError, match="does not match source.settings"):
        merge_pairs([tampered], out)
    assert not out.exists()

    missing = _merge_pair("t3")
    del missing["source"]["settings"]
    missing_source = _write_pairs(tmp_path / "missing-settings.jsonl", [missing])
    with pytest.raises(DatasetError, match="source.settings must be a JSON object"):
        validate_pairs([missing_source])


@pytest.mark.parametrize(
    ("rows", "cap", "message"),
    [
        ([_merge_pair("t"), _merge_pair("t")], 8, "duplicate pair"),
        ([_merge_pair("t"), _merge_pair("t", "rejected", "chosen")], 8, "conflicting pair"),
        ([_merge_pair("t", "a", "b"), _merge_pair("t", "c", "d")], 1, "above the per-task cap"),
        ([_merge_pair("t", version="v1"), _merge_pair("t", "c", "d", version="v2")],
         8, "task/prompt version"),
    ],
)
def test_pair_validation_rejects_duplicate_conflicting_overcap_and_versioned_rows(
    tmp_path, rows, cap, message
):
    path = _write_pairs(tmp_path / "pairs.jsonl", rows)
    with pytest.raises(DatasetError, match=message):
        validate_pairs([path], per_task_cap=cap)


def test_legacy_rows_require_a_config_mapping(tmp_path):
    legacy = _write_pairs(tmp_path / "legacy.jsonl", [_merge_pair("t", source=False)])
    with pytest.raises(DatasetError, match="pass --legacy-config"):
        validate_pairs([legacy])

    cfg = ROOT / "configs" / "rtx5070_train.yaml"
    out = tmp_path / "combined.jsonl"
    summary = ds.main([
        "merge", "--out", str(out), "--legacy-config", str(cfg), str(legacy)
    ])
    assert summary == 0
    assert json.loads(out.read_text().splitlines()[0])["task_id"] == "t"


def test_pair_validation_reports_bad_json_and_invalid_pair_fields(tmp_path):
    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("{bad json}\n", encoding="utf-8")
    with pytest.raises(DatasetError, match="invalid JSON"):
        validate_pairs([malformed])

    invalid = _write_pairs(tmp_path / "invalid.jsonl", [{"task_id": "t"}])
    with pytest.raises(DatasetError, match="chosen_id"):
        validate_pairs([invalid])


def test_filter_pairs_writes_the_kept_pairs_and_its_input_into_the_dataset(data, tmp_path):
    from scripts.filter_pairs import main

    source = tmp_path / "preferences.jsonl"
    source.write_text("".join(json.dumps(r) + "\n" for r in [_pair("t1", 3), _pair("t2", 1)]))

    main([str(source), "--dataset", "train-v2", "--min-rep-wins", "2"])

    folder = data / "train-v2"
    assert (folder / "pairs_unfiltered.jsonl").read_bytes() == source.read_bytes()
    kept = [json.loads(line) for line in (folder / "pairs.jsonl").read_text().splitlines()]
    assert [r["task_id"] for r in kept] == ["t1"]
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    assert [(e["name"], e["rows"]) for e in manifest["files"]] == [
        ("pairs_unfiltered.jsonl", 2),
        ("pairs.jsonl", 1),
    ]
    assert verify(folder) == []


def test_filter_pairs_needs_an_output_file_or_a_dataset(tmp_path):
    from scripts.filter_pairs import main

    source = tmp_path / "preferences.jsonl"
    source.write_text("")
    with pytest.raises(SystemExit):
        main([str(source)])
    with pytest.raises(SystemExit):
        main([str(source), str(tmp_path / "out.jsonl"), "--dataset", "v1"])
