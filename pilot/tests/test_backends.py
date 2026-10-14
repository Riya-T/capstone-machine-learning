"""Unit tests for pipeline.backends: the OpenAI-compatible backend against a
local stub HTTP server (request body, auth, retries, errors), the
deterministic mock, CachedBackend replay, and derive_seed.

Usage:
    uv run pytest tests/test_backends.py
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pipeline.backends import (
    BackendError,
    CachedBackend,
    InMemoryCallCache,
    MockBackend,
    OpenAICompatBackend,
    Usage,
    derive_seed,
    make_backend,
    usage_from_dict,
    usage_to_dict,
)
from pipeline.config import BackendConfig, ConfigError, load_config

PILOT = Path(__file__).resolve().parents[1]


# --- HTTP stub --------------------------------------------------------------


def completion(text="hello", finish_reason="stop", usage=None):
    return {
        "choices": [
            {"message": {"role": "assistant", "content": text}, "finish_reason": finish_reason}
        ],
        "usage": usage if usage is not None else {"prompt_tokens": 7, "completion_tokens": 2},
    }


class StubServer:
    """Answers POSTs from a script of (status, body) pairs and records each
    request it receives."""

    def __init__(self):
        self.script: list[tuple[int, object]] = []
        self.requests: list[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                stub.requests.append(
                    {
                        "path": self.path,
                        "headers": dict(self.headers),
                        "body": json.loads(self.rfile.read(length)),
                    }
                )
                status, body = stub.script.pop(0)
                raw = body if isinstance(body, bytes) else json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):  # keep test output quiet
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}/v1"
        # A short poll interval keeps shutdown() fast (the default is 0.5 s).
        threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        ).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stub():
    server = StubServer()
    yield server
    server.close()


def http_cfg(url, **overrides) -> BackendConfig:
    values = dict(
        kind="openai_compat",
        model="qwen",
        temperature=0.7,
        max_tokens=64,
        base_url=url,
        request_timeout_s=5.0,
        max_retries=2,
        retry_backoff_s=1.0,
    )
    values.update(overrides)
    return BackendConfig(**values)


def http_backend(url, seed=11, sleeps=None, **overrides):
    record = sleeps.append if sleeps is not None else (lambda s: None)
    return OpenAICompatBackend(http_cfg(url, **overrides), seed, sleep=record)


# --- OpenAI-compatible backend ----------------------------------------------


def test_sends_one_user_message_with_sampling_settings(stub):
    stub.script = [(200, completion("hi there"))]
    backend = http_backend(stub.url + "/")  # trailing slash is tolerated
    assert backend.generate("Write code") == "hi there"
    (request,) = stub.requests
    assert request["path"] == "/v1/chat/completions"
    assert request["body"] == {
        "model": "qwen",
        "messages": [{"role": "user", "content": "Write code"}],
        "temperature": 0.7,
        "max_tokens": 64,
        "seed": 11,
    }
    assert "Authorization" not in request["headers"]


def test_records_usage_and_finish_reason(stub):
    stub.script = [
        (200, completion("cut", "length", {"prompt_tokens": 9, "completion_tokens": 64}))
    ]
    backend = http_backend(stub.url)
    backend.generate("p")
    assert backend.last_usage == Usage(9, 64, "length")


def test_missing_usage_is_recorded_as_unknown(stub):
    body = completion()
    del body["usage"]
    stub.script = [(200, body)]
    backend = http_backend(stub.url)
    backend.generate("p")
    assert backend.last_usage == Usage(None, None, "stop")


def test_api_key_comes_from_the_named_environment_variable(stub, monkeypatch):
    monkeypatch.setenv("PILOT_TEST_KEY", "secret-123")
    stub.script = [(200, completion())]
    http_backend(stub.url, api_key_env="PILOT_TEST_KEY").generate("p")
    assert stub.requests[0]["headers"]["Authorization"] == "Bearer secret-123"


def test_missing_api_key_fails_when_the_backend_is_built(monkeypatch):
    monkeypatch.delenv("PILOT_TEST_KEY", raising=False)
    with pytest.raises(ConfigError, match="PILOT_TEST_KEY is not set"):
        http_backend("http://127.0.0.1:9/v1", api_key_env="PILOT_TEST_KEY")


@pytest.mark.parametrize("status", [429, 500, 503])
def test_transient_errors_are_retried_with_doubling_backoff(stub, status):
    stub.script = [
        (status, {"error": "busy"}),
        (status, {"error": "busy"}),
        (200, completion("ok")),
    ]
    sleeps = []
    assert http_backend(stub.url, sleeps=sleeps).generate("p") == "ok"
    assert sleeps == [1.0, 2.0]
    assert len(stub.requests) == 3


def test_retries_are_bounded(stub):
    stub.script = [(500, {"error": "down"})] * 3
    sleeps = []
    with pytest.raises(BackendError, match="HTTP 500"):
        http_backend(stub.url, sleeps=sleeps).generate("p")
    assert len(stub.requests) == 3  # one try + max_retries
    assert sleeps == [1.0, 2.0]  # no sleep after the last attempt


def test_client_errors_are_not_retried(stub):
    stub.script = [(400, {"error": "bad model name"})]
    with pytest.raises(BackendError, match="HTTP 400 .*bad model name"):
        http_backend(stub.url).generate("p")
    assert len(stub.requests) == 1


def test_unreachable_server_raises_backend_error():
    sleeps = []
    # Port 9 (discard) on localhost is closed: the connection is refused.
    with pytest.raises(BackendError, match="cannot reach"):
        http_backend("http://127.0.0.1:9/v1", sleeps=sleeps, max_retries=1).generate("p")
    assert sleeps == [1.0]


@pytest.mark.parametrize(
    "body",
    [b"not json", {"choices": []}, {"choices": [{"message": {"content": None}}]}],
)
def test_malformed_responses_raise_backend_error(stub, body):
    stub.script = [(200, body)]
    with pytest.raises(BackendError):
        http_backend(stub.url).generate("p")
    assert len(stub.requests) == 1


def test_http_identity_ignores_operational_settings():
    base = http_backend("http://h/v1").identity
    assert http_backend("http://h/v1", request_timeout_s=99.0, max_retries=0).identity == base
    assert http_backend("http://h/v1", seed=12).identity != base
    assert http_backend("http://h/v1", temperature=0.2).identity != base
    assert http_backend("http://h/v1", model="other").identity != base
    assert http_backend("http://other/v1").identity != base


# --- mock backend -----------------------------------------------------------


def write_fixtures(directory: Path, text: str) -> Path:
    path = directory / "fixtures.yaml"
    path.write_text(text)
    return path


def mock_cfg(fixtures: Path) -> BackendConfig:
    return BackendConfig(kind="mock", model="m", temperature=0.7, max_tokens=64, fixtures=fixtures)


RULES = """
rules:
  - match: 'change c_txn'
    responses:
      - text: txn-answer
  - match: 'variant: (modular|tangled)'
    responses:
      - text: rep-a
      - text: rep-b
      - file: answers/c.md
  - match: ''
    responses:
      - text: fallback
"""


@pytest.fixture
def fixtures(tmp_path):
    (tmp_path / "answers").mkdir()
    (tmp_path / "answers" / "c.md").write_text("from a file\n")
    return write_fixtures(tmp_path, RULES)


def test_mock_first_matching_rule_wins(fixtures):
    backend = MockBackend(mock_cfg(fixtures), seed=0)
    assert backend.generate("apply change c_txn to variant: modular") == "txn-answer"
    assert backend.generate("anything else") == "fallback"


def test_mock_response_is_chosen_by_seed(fixtures):
    answers = [
        MockBackend(mock_cfg(fixtures), seed).generate("variant: tangled") for seed in range(4)
    ]
    assert answers == ["rep-a", "rep-b", "from a file\n", "rep-a"]


def test_mock_is_deterministic_and_records_prompts(fixtures):
    first = MockBackend(mock_cfg(fixtures), seed=5)
    second = MockBackend(mock_cfg(fixtures), seed=5)
    assert [first.generate(p) for p in ("a", "variant: modular")] == [
        second.generate(p) for p in ("a", "variant: modular")
    ]
    assert first.prompts == ["a", "variant: modular"]
    # seed 5 picks responses[5 % 3], the file "from a file": 3 words.
    assert first.last_usage == Usage(prompt_tokens=2, completion_tokens=3, finish_reason="stop")


def test_mock_without_a_matching_rule_raises(tmp_path):
    path = write_fixtures(
        tmp_path, "rules:\n  - match: '^only this$'\n    responses: [{text: x}]\n"
    )
    with pytest.raises(BackendError, match="no mock rule matches"):
        MockBackend(mock_cfg(path), seed=0).generate("something else")


@pytest.mark.parametrize(
    ("text", "message"),
    [
        (
            "rules:\n  - match: '('\n    responses: [{text: x}]\n",
            r"rules\[0\]\.match: invalid regex",
        ),
        ("rules:\n  - match: a\n    responses: []\n", "must not be empty"),
        ("rules:\n  - match: a\n    responses: [{}]\n", "exactly one of text, file"),
        ("rules:\n  - match: a\n    responses: [{text: x, file: f}]\n", "path does not exist"),
        ("rules:\n  - match: a\n    reply: x\n", r"rules\[0\]\.reply: unknown key"),
        ("rules:\n  - match: a\n    responses: [{file: missing.md}]\n", "path does not exist"),
    ],
)
def test_mock_fixture_errors(tmp_path, text, message):
    path = write_fixtures(tmp_path, text)
    with pytest.raises(ConfigError, match=message):
        MockBackend(mock_cfg(path), seed=0)


def test_mock_identity_tracks_fixture_contents_and_seed(fixtures):
    base = MockBackend(mock_cfg(fixtures), seed=0).identity
    assert MockBackend(mock_cfg(fixtures), seed=1).identity != base
    (fixtures.parent / "answers" / "c.md").write_text("edited\n")
    assert MockBackend(mock_cfg(fixtures), seed=0).identity != base


def test_make_backend_dispatches_on_kind(fixtures):
    assert isinstance(make_backend(mock_cfg(fixtures), 0), MockBackend)
    assert isinstance(make_backend(http_cfg("http://h/v1"), 0), OpenAICompatBackend)


def test_committed_mock_writer_answers_the_record_store_prompt():
    from pipeline.registry import build_writer_prompt, load_tasks, load_template

    cfg = load_config(PILOT / "configs" / "pilot_mock.yaml")
    task = load_tasks(cfg.tasks)["record_store"]
    prompt = build_writer_prompt(task.writer_view(), load_template(cfg.writer.prompt_template))
    answer = make_backend(cfg.writer.backend, seed=0).generate(prompt)
    assert answer.startswith("```python file=records.py\n")
    assert task.reference["records.py"].decode() in answer


# --- cache ------------------------------------------------------------------


class Counter:
    """A backend whose answers differ on every call, like a sampled model."""

    def __init__(self, identity="counter"):
        self._identity = identity
        self.calls = 0
        self.last_usage = None

    @property
    def identity(self):
        return self._identity

    def generate(self, prompt):
        self.calls += 1
        self.last_usage = Usage(self.calls, self.calls, "stop")
        return f"{prompt}#{self.calls}"


def test_rerun_replays_answers_without_model_calls():
    cache = InMemoryCallCache()
    first_inner = Counter()
    first = CachedBackend(first_inner, cache)
    answers = [first.generate(p) for p in ("a", "b")]
    usages = [first.last_usage]

    second_inner = Counter()
    second = CachedBackend(second_inner, cache)
    assert [second.generate(p) for p in ("a", "b")] == answers
    assert second.last_usage == Usage(2, 2, "stop") and usages == [Usage(2, 2, "stop")]
    assert second_inner.calls == 0 and second.model_calls == 0
    assert second.last_was_cached
    assert first.model_calls == 2 and not first.last_was_cached


def test_repeated_prompt_within_a_trial_is_two_separate_calls():
    cache = InMemoryCallCache()
    first = CachedBackend(Counter(), cache)
    assert [first.generate("same"), first.generate("same")] == ["same#1", "same#2"]
    replay = CachedBackend(Counter(), cache)
    assert [replay.generate("same"), replay.generate("same")] == ["same#1", "same#2"]


def test_resume_after_a_partial_trial_only_calls_for_new_steps():
    cache = InMemoryCallCache()
    crashed = CachedBackend(Counter(), cache)
    crashed.generate("turn 1")  # the trial dies after one call

    inner = Counter()
    resumed = CachedBackend(inner, cache)
    assert resumed.generate("turn 1") == "turn 1#1"  # replayed
    assert resumed.generate("turn 2") == "turn 2#1"  # new call
    assert inner.calls == 1


def test_different_identity_misses_the_cache():
    cache = InMemoryCallCache()
    CachedBackend(Counter("seed-1"), cache).generate("p")
    other = Counter("seed-2")
    CachedBackend(other, cache).generate("p")
    assert other.calls == 1


def test_failed_call_is_not_recorded():
    class Failing(Counter):
        def generate(self, prompt):
            raise BackendError("down")

    cache = InMemoryCallCache()
    backend = CachedBackend(Failing(), cache)
    with pytest.raises(BackendError):
        backend.generate("p")
    assert cache.calls == {}
    assert CachedBackend(Counter(), cache).generate("p") == "p#1"


def test_usage_round_trips_through_json():
    usage = Usage(3, 4, "length")
    assert usage_from_dict(json.loads(json.dumps(usage_to_dict(usage)))) == usage
    assert usage_from_dict(usage_to_dict(None)) is None


# --- seeds ------------------------------------------------------------------


def test_derive_seed_is_pinned_across_machines_and_processes():
    # A literal, so a change to the derivation (which would silently change
    # every rep's seed and orphan cached results) fails loudly here.
    assert derive_seed(20261014, "record_store", "abc", "s1", 0) == 1993081659


@given(st.integers(0, 2**32), st.lists(st.text() | st.integers(), max_size=4))
def test_derive_seed_is_a_valid_31_bit_seed(base, parts):
    seed = derive_seed(base, *parts)
    assert 0 <= seed < 2**31
    assert derive_seed(base, *parts) == seed


def test_derive_seed_separates_parts():
    seeds = {derive_seed(1, *p) for p in [("a", 0), ("a", 1), ("b", 0), ("a0",), ("a", "0")]}
    assert len(seeds) == 5
