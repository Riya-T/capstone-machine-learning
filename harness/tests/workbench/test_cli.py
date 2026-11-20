"""Exercise the public CLI with portable evidence and no execution services.

Usage: python -m pytest tests/workbench/test_cli.py
"""

import json

import yaml

from harness.__main__ import main
from harness.workbench.report import encoded
from tests.workbench.helpers import fixture


def test_compare_and_verify_work_offline_with_unchanged_input(tmp_path, monkeypatch, capsys):
    _, data = fixture(tmp_path)
    path = tmp_path / "saved.json"
    path.write_bytes(encoded(data))
    before = path.read_bytes()

    def forbidden(*a, **kw):
        raise AssertionError("Reporting must not call inference or a sandbox")

    monkeypatch.setattr("harness.collection.collect.collect", forbidden)
    monkeypatch.setattr("harness.sandbox.runner.make_runner", forbidden)
    args = [
        "collection-workbench",
        "compare",
        "--input",
        str(path),
        "--out",
        str(tmp_path / "bundle"),
        "--bootstrap-samples",
        "20",
    ]
    assert main(args) == 0
    assert json.loads(capsys.readouterr().out)["training_labels_created"] == 0
    assert main(["collection-workbench", "verify", "--report", str(tmp_path / "bundle")]) == 0
    assert json.loads(capsys.readouterr().out)["analysis_recomputed"]
    assert path.read_bytes() == before


def test_malformed_source_never_publishes_a_partial_report(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text('{"kind":"saved_collection","kind":"ambiguous"}')
    out = tmp_path / "not-created"
    assert main(["collection-workbench", "compare", "--input", str(path), "--out", str(out)]) == 2
    assert "Duplicate JSON key" in capsys.readouterr().err
    assert not out.exists()


def test_empty_manifest_and_unknown_fields_give_actionable_errors(tmp_path, capsys):
    path = tmp_path / "manifest.json"
    for content in ({"schema_version": 1, "methods": []}, {"schema_version": 1, "inference": True}):
        path.write_bytes(encoded(content))
        assert (
            main(
                [
                    "collection-workbench",
                    "build",
                    "--manifest",
                    str(path),
                    "--out",
                    str(tmp_path / "out"),
                ]
            )
            == 2
        )
        assert "Collection workbench:" in capsys.readouterr().err
        assert not (tmp_path / "out").exists()


def test_incomplete_collection_is_saved_but_cli_returns_checkpoint_status(tmp_path, capsys):
    _, data = fixture(tmp_path, infra=True)
    path = tmp_path / "saved.json"
    path.write_bytes(encoded(data))
    out = tmp_path / "incomplete"
    assert (
        main(
            [
                "collection-workbench",
                "compare",
                "--input",
                str(path),
                "--out",
                str(out),
                "--bootstrap-samples",
                "20",
            ]
        )
        == 3
    )
    assert not json.loads(capsys.readouterr().out)["collection_complete"]
    assert main(["collection-workbench", "verify", "--report", str(out)]) == 0


def test_build_exports_real_native_stores_from_a_relative_manifest(tmp_path, capsys):
    from tests.evaluation.helpers import IMAGE

    methods = []
    for method in ("base", "candidate"):
        cfg, _ = fixture(tmp_path / method, method=method)
        config_path = tmp_path / method / "saved.yaml"
        config_path.write_text(yaml.safe_dump(cfg.to_dict()), encoding="utf8")
        methods.append({"id": method, "config": f"{method}/saved.yaml"})
    manifest = tmp_path / "study.json"
    manifest.write_bytes(
        encoded(
            {
                "schema_version": 1,
                "purpose": "fixture",
                "image_id": IMAGE,
                "reference": "base",
                "methods": methods,
                "analysis": {"bootstrap_samples": 20},
            }
        )
    )
    out = tmp_path / "bundle"
    assert (
        main(["collection-workbench", "build", "--manifest", str(manifest), "--out", str(out)]) == 0
    )
    assert json.loads(capsys.readouterr().out)["collection_complete"]
    assert main(["collection-workbench", "verify", "--report", str(out)]) == 0


def test_export_cannot_publish_inside_its_source_store(tmp_path, capsys):
    from tests.evaluation.helpers import IMAGE

    cfg, _ = fixture(tmp_path)
    path = tmp_path / "saved.yaml"
    path.write_text(yaml.safe_dump(cfg.to_dict()), encoding="utf8")
    output = cfg.runs_dir / "export.json"
    assert (
        main(
            [
                "collection-workbench",
                "export",
                "--config",
                str(path),
                "--image-id",
                IMAGE,
                "--method",
                "base",
                "--purpose",
                "fixture",
                "--out",
                str(output),
            ]
        )
        == 2
    )
    assert "outside the source store" in capsys.readouterr().err
    assert not output.exists()


def test_investigation_commands_share_the_existing_review_and_checkpoint_workflows(
    tmp_path, capsys
):
    from harness.workbench.report import write_report
    from tests.workbench.test_checkpoints import example

    source = tmp_path / "source"
    write_report(example(tmp_path), source)
    assert (
        main(
            [
                "collection-workbench",
                "checkpoints",
                "--report",
                str(source),
                "--expect-seeds",
                "trained=42,43",
                "--out",
                str(tmp_path / "seeds"),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["collection-workbench", "verify", "--report", str(tmp_path / "seeds")]) == 0
    capsys.readouterr()
    assert (
        main(
            [
                "collection-workbench",
                "review",
                "init",
                "--report",
                str(source),
                "--out",
                str(tmp_path / "pack"),
            ]
        )
        == 0
    )
    capsys.readouterr()
    template = tmp_path / "pack/annotations.template.csv"
    assert (
        main(
            [
                "collection-workbench",
                "review",
                "compile",
                "--pack",
                str(tmp_path / "pack"),
                "--annotations",
                str(template),
                "--out",
                str(tmp_path / "reviewed"),
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main(["collection-workbench", "verify", "--report", str(tmp_path / "reviewed")]) == 0
    result = json.loads((tmp_path / "reviewed/analysis.json").read_bytes())
    assert result["training_labels"] is None
    assert result["case_counts"]["unreviewed"] > 0


def test_missing_expected_checkpoint_creates_a_diagnostic_and_exit_three(tmp_path, capsys):
    from harness.workbench.report import write_report
    from tests.workbench.test_checkpoints import example

    write_report(example(tmp_path), tmp_path / "source")
    assert (
        main(
            [
                "collection-workbench",
                "checkpoints",
                "--report",
                str(tmp_path / "source"),
                "--expect-seeds",
                "trained=42,43,44",
                "--out",
                str(tmp_path / "incomplete"),
            ]
        )
        == 3
    )
    assert not json.loads(capsys.readouterr().out)["analysis_complete"]
    assert (tmp_path / "incomplete/analysis.json").exists()
