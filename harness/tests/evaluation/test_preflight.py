"""Readiness checks never generate, build images, create stores or follow redirects.

Usage:
    uv run pytest tests/evaluation/test_preflight.py
"""

import json

import pytest

from harness.__main__ import main
from harness.evaluation.plan import prepare
from harness.evaluation.preflight import NoRedirect, check_preflight
from harness.evaluation.records import EvaluationError

from .test_plan import forbidden, write_plan


def test_default_check_is_read_only_and_never_probes(tmp_path, monkeypatch):
    prepared = prepare(write_plan(tmp_path))
    monkeypatch.setattr("harness.evaluation.preflight._docker", forbidden)
    monkeypatch.setattr("harness.evaluation.preflight._models", forbidden)
    result = check_preflight(prepared)
    assert not result["ready"] and result["unchecked"] > 0
    assert not result["inference_performed"]
    assert not prepared.root.exists()


def test_model_probes_only_get_local_lists_and_cache_each_server(tmp_path, monkeypatch):
    from dataclasses import replace

    path = write_plan(tmp_path)
    prepared = prepare(path)
    configs = tuple(
        replace(
            c,
            writer=replace(
                c.writer,
                backend=replace(
                    c.writer.backend,
                    kind="openai_compat",
                    base_url="http://127.0.0.1:8000/v1",
                    fixtures=None,
                ),
            ),
        )
        for c in prepared.configs
    )
    prepared = replace(prepared, configs=configs)
    seen = []
    monkeypatch.setattr(
        "harness.evaluation.preflight._models", lambda url: seen.append(url) or {"original"}
    )
    monkeypatch.setattr("harness.evaluation.preflight.shutil.which", lambda _: "/fake/docker")
    monkeypatch.setattr(
        "harness.evaluation.preflight._docker",
        lambda *args: (
            json.dumps({"OSType": "linux", "ServerVersion": "fixture"})
            if args[0] == "info"
            else "sha256:" + "1" * 64
        ),
    )
    result = check_preflight(prepared, probe=True)
    assert len(seen) == 1
    assert any(c["status"] == "fail" and c["check"] == "candidate/writer" for c in result["checks"])
    assert not prepared.root.exists()


def test_docker_probe_never_uses_mutating_commands(tmp_path, monkeypatch):
    prepared = prepare(write_plan(tmp_path))
    seen = []

    def inspect_only(*args):
        seen.append(args)
        assert args[:1] == ("info",) or args[:2] == ("image", "inspect")
        return (
            json.dumps({"OSType": "linux", "ServerVersion": "fixture"})
            if args[0] == "info"
            else "sha256:fixture"
        )

    monkeypatch.setattr("harness.evaluation.preflight.shutil.which", lambda _: "/fake/docker")
    monkeypatch.setattr("harness.evaluation.preflight._docker", inspect_only)
    result = check_preflight(prepared, probe=True)
    assert seen and not result["inference_performed"]


def test_model_redirects_are_rejected():
    with pytest.raises(EvaluationError, match="redirect"):
        NoRedirect().redirect_request(None, None, 302, "", {}, "https://outside.example/models")


@pytest.mark.parametrize("payload", [b'{"data":[{"id":"available"}]}', b'{"data":[null]}'])
def test_advertisement_probe_sends_only_a_get_request(payload):
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    from harness.evaluation.preflight import _models

    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.command, self.path, self.headers.get("Authorization")))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1"
        if b"null" in payload:
            with pytest.raises(EvaluationError, match="Malformed"):
                _models(url)
        else:
            assert _models(url) == {"available"}
        assert requests == [("GET", "/v1/models", None)]
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=2)


def test_cli_returns_not_ready_for_an_unprobed_plan(tmp_path, capsys):
    path = write_plan(tmp_path)
    assert main(["evaluation-preflight", "--plan", str(path)]) == 3
    assert not json.loads(capsys.readouterr().out)["ready"]
