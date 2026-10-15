"""Model backends behind one interface: generate(prompt) -> text.

- OpenAICompatBackend talks to any OpenAI-compatible chat endpoint (llama.cpp,
  Ollama, vLLM or a hosted API).
- MockBackend answers from a fixture file, deterministically; integration
  tests use it.
- CachedBackend wraps either one and records every call, so a rerun replays
  recorded answers instead of calling the model again.

A backend is built for one seed (`make_backend(cfg, seed)`), so sampling
settings never travel through `generate`. After each call, `last_usage` holds
the token counts for that call.

Usage:
    seed = derive_seed(cfg.seed, task.id, "writer", sample_idx)
    backend = CachedBackend(make_backend(cfg.writer.backend, seed), store)
    text = backend.generate(prompt)
    backend.last_usage, backend.model_calls          # tokens; calls that reached the model
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal, Protocol

import yaml

from .config import BackendConfig, ConfigError, InputPath, parse_dataclass


class BackendError(RuntimeError):
    """A model call failed. Callers record it as an infrastructure error,
    never as a failure of the program being written or edited."""


@dataclass(frozen=True)
class Usage:
    prompt_tokens: int | None
    completion_tokens: int | None
    # "stop" for a normal end; "length" means max_tokens cut the output off.
    finish_reason: str | None


class Backend(Protocol):
    last_usage: Usage | None

    @property
    def identity(self) -> str:
        """Hash of everything that determines this backend's outputs, seed
        included. Two backends with equal identities give the same answer to
        the same prompt (as far as the model is deterministic)."""
        ...

    def generate(self, prompt: str) -> str: ...


def make_backend(cfg: BackendConfig, seed: int) -> Backend:
    if cfg.kind == "openai_compat":
        return OpenAICompatBackend(cfg, seed)
    if cfg.kind == "mock":
        return MockBackend(cfg, seed)
    raise ValueError(f"unknown backend kind {cfg.kind!r}")


def derive_seed(base_seed: int, *parts: object) -> int:
    """A seed for one call site, e.g. derive_seed(cfg.seed, task, candidate,
    sequence, rep). Built from sha256, not hash(), because Python randomizes
    str hashes per process; the result must be the same on every machine."""
    text = json.dumps([base_seed, *parts], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:4], "big") & 0x7FFFFFFF


def _hash_json(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- OpenAI-compatible HTTP -------------------------------------------------


class OpenAICompatBackend:
    def __init__(
        self,
        cfg: BackendConfig,
        seed: int,
        *,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        assert cfg.base_url is not None  # enforced by BackendConfig
        self.cfg = cfg
        self.seed = seed
        self.last_usage: Usage | None = None
        self._sleep = sleep  # injectable so tests don't wait out the backoff
        self._url = cfg.base_url.rstrip("/") + "/chat/completions"
        self._api_key = None
        if cfg.api_key_env:
            self._api_key = os.environ.get(cfg.api_key_env)
            if not self._api_key:
                # Fail when the backend is built, not hours into a run.
                raise ConfigError(f"environment variable {cfg.api_key_env} is not set")

    @property
    def identity(self) -> str:
        # Operational settings (timeouts, retries, which env var holds the
        # key) don't change answers, so they stay out; base_url stays in
        # because the same model name on another server may be a different
        # build or quantization.
        c = self.cfg
        return _hash_json(
            {
                "kind": c.kind,
                "base_url": c.base_url,
                "model": c.model,
                "temperature": c.temperature,
                "max_tokens": c.max_tokens,
                "seed": self.seed,
            }
        )

    def generate(self, prompt: str) -> str:
        body = {
            "model": self.cfg.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_tokens,
            "seed": self.seed,
        }
        reply = self._post(body)
        try:
            choice = reply["choices"][0]
            text = choice["message"]["content"]
            if not isinstance(text, str):
                raise TypeError("content is not a string")
        except (KeyError, IndexError, TypeError) as exc:
            raise BackendError(f"unexpected response shape from {self._url}: {exc}") from None
        usage = reply.get("usage") or {}
        self.last_usage = Usage(
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            finish_reason=choice.get("finish_reason"),
        )
        return text

    def _post(self, body: dict) -> dict:
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        attempts = self.cfg.max_retries + 1
        for attempt in range(attempts):
            request = urllib.request.Request(self._url, data=data, headers=headers, method="POST")
            try:
                with urllib.request.urlopen(request, timeout=self.cfg.request_timeout_s) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", "replace")[:500]
                error = BackendError(f"HTTP {exc.code} from {self._url}: {detail}")
                # 4xx other than 429 means the request itself is wrong;
                # repeating it can't help.
                if exc.code != 429 and exc.code < 500:
                    raise error from None
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                error = BackendError(f"cannot reach {self._url}: {exc}")
            except json.JSONDecodeError as exc:
                raise BackendError(f"response from {self._url} is not JSON: {exc}") from None
            if attempt + 1 < attempts:
                self._sleep(self.cfg.retry_backoff_s * 2**attempt)
        raise error


# --- deterministic mock -----------------------------------------------------


@dataclass(frozen=True)
class MockResponse:
    text: str | None = None
    file: InputPath | None = None  # relative to the fixture file
    # "length" simulates an answer cut off at max_tokens.
    finish_reason: Literal["stop", "length"] = "stop"


@dataclass(frozen=True)
class MockRule:
    match: str  # regular expression, searched anywhere in the prompt
    responses: tuple[MockResponse, ...]


@dataclass(frozen=True)
class MockFixtures:
    rules: tuple[MockRule, ...]


class MockBackend:
    """Answers from fixture rules, with no randomness.

    The first rule whose regex matches the prompt wins, and the answer is
    `responses[seed % len(responses)]`. Repetitions get different seeds, so
    a rule with several responses scripts repetitions that disagree, which is
    how tests produce inconsistent results on purpose. A prompt that matches
    no rule raises: a mock that silently answered something would hide
    mistakes in the fixtures.
    """

    def __init__(self, cfg: BackendConfig, seed: int) -> None:
        assert cfg.fixtures is not None  # enforced by BackendConfig
        self.cfg = cfg
        self.seed = seed
        self.last_usage: Usage | None = None
        self.prompts: list[str] = []  # every prompt received, for leak tests
        self._rules = _load_mock_rules(cfg.fixtures)

    @property
    def identity(self) -> str:
        # Hash the loaded rules, not the fixture path, so editing a fixture or
        # a response file it points to invalidates cached answers.
        return _hash_json({"kind": "mock", "rules": self._rules, "seed": self.seed})

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        for pattern, responses in self._rules:
            if re.search(pattern, prompt):
                text, finish_reason = responses[self.seed % len(responses)]
                # Word counts stand in for tokens: deterministic and roughly
                # proportional, which is all tests of usage accounting need.
                self.last_usage = Usage(len(prompt.split()), len(text.split()), finish_reason)
                return text
        raise BackendError(f"no mock rule matches the prompt starting {prompt[:80]!r}")


def _load_mock_rules(path: Path) -> list[tuple[str, list[tuple[str, str]]]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        fixtures = parse_dataclass(MockFixtures, data, base_dir=path.parent)
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from None
    rules = []
    for i, rule in enumerate(fixtures.rules):
        where = f"{path}: rules[{i}]"
        try:
            re.compile(rule.match)
        except re.error as exc:
            raise ConfigError(f"{where}.match: invalid regex: {exc}") from None
        if not rule.responses:
            raise ConfigError(f"{where}.responses: must not be empty")
        answers = []
        for response in rule.responses:
            if (response.text is None) == (response.file is None):
                raise ConfigError(f"{where}: each response needs exactly one of text, file")
            text = (
                response.text
                if response.text is not None
                else response.file.read_text(encoding="utf-8")
            )
            answers.append((text, response.finish_reason))
        rules.append((rule.match, answers))
    return rules


# --- call cache -------------------------------------------------------------


@dataclass(frozen=True)
class CachedCall:
    text: str
    usage: Usage | None


class CallCache(Protocol):
    """Where CachedBackend keeps answers. The store implements this on
    SQLite; tests use InMemoryCallCache."""

    def get(self, key: str) -> CachedCall | None: ...

    def put(self, key: str, call: CachedCall) -> None: ...


class InMemoryCallCache:
    def __init__(self) -> None:
        self.calls: dict[str, CachedCall] = {}

    def get(self, key: str) -> CachedCall | None:
        return self.calls.get(key)

    def put(self, key: str, call: CachedCall) -> None:
        self.calls[key] = call


class CachedBackend:
    """Replays recorded answers; calls the wrapped backend only on a miss.

    Use one instance per trial (one writer sample, or one editing trial).
    The key includes the position of the call within that trial, not just
    the prompt: a sampled model can answer the same prompt differently the
    second time, and a replay must reproduce the original sequence of
    answers, not repeat the first one.
    """

    def __init__(self, inner: Backend, cache: CallCache, start_index: int = 0) -> None:
        """start_index: the position of the first call. A trial resumed at a
        later step starts at the number of calls its earlier steps made, so
        the resumed calls line up with the recorded ones."""
        self.inner = inner
        self.cache = cache
        self.last_usage: Usage | None = None
        self.last_was_cached = False
        self.last_key: str | None = None  # model_calls key of the latest answer
        self.model_calls = 0  # calls that reached the wrapped backend
        self._index = start_index

    @property
    def identity(self) -> str:
        return self.inner.identity

    def key(self, prompt: str, index: int) -> str:
        return _hash_json([self.inner.identity, index, prompt])

    def generate(self, prompt: str) -> str:
        key = self.key(prompt, self._index)
        self.last_key = key
        hit = self.cache.get(key)
        if hit is None:
            # If the wrapped call raises, nothing is recorded and the index
            # doesn't advance; the trial is retried later from the start.
            text = self.inner.generate(prompt)
            hit = CachedCall(text, self.inner.last_usage)
            self.cache.put(key, hit)
            self.model_calls += 1
            self.last_was_cached = False
        else:
            self.last_was_cached = True
        self._index += 1
        self.last_usage = hit.usage
        return hit.text


def usage_to_dict(usage: Usage | None) -> dict | None:
    """For storing usage as JSON."""
    return None if usage is None else asdict(usage)


def usage_from_dict(data: dict | None) -> Usage | None:
    return None if data is None else Usage(**data)
