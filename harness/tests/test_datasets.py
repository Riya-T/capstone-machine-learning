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
from harness.datasets import DatasetError, add_file, datasets, save_output, verify

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
