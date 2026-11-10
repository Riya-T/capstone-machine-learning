"""Tests loading and tokenizing the correctness-only baseline's programs.

Usage:
    uv run pytest tests/test_train_sft.py
"""

import json

import pytest

from harness.train_sft import load_programs, tokenize


def test_load_programs_extracts_prompt_and_completion_and_ignores_metadata(tmp_path):
    source = tmp_path / "programs.jsonl"
    source.write_text(
        json.dumps({"task_id": "t", "candidate_id": "c", "prompt": "write", "completion": "code"})
        + "\n\n"
    )

    assert load_programs(source) == [{"prompt": "write", "completion": "code"}]


@pytest.mark.parametrize(
    "text",
    ["", "{not json}\n", "[]\n", '{"prompt":"p","completion":""}\n', '{"prompt":"p"}\n'],
)
def test_load_programs_rejects_invalid_rows(tmp_path, text):
    source = tmp_path / "programs.jsonl"
    source.write_text(text)

    with pytest.raises(ValueError):
        load_programs(source)


class _Tokenizer:
    """One token per character; the end-of-turn token is 0."""

    eos_token_id = 0

    def __call__(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return {"input_ids": [ord(ch) for ch in text]}


def test_tokenize_appends_end_of_turn_to_completion_only():
    rows = [{"prompt": "ab", "completion": "xyz"}]

    assert tokenize(rows, _Tokenizer(), max_length=6) == [
        {"prompt": [97, 98], "completion": [120, 121, 122, 0]}
    ]


def test_tokenize_refuses_examples_longer_than_max_length():
    rows = [{"prompt": "ab", "completion": "xyz"}]

    with pytest.raises(ValueError, match="1 examples exceed --max-length 5"):
        tokenize(rows, _Tokenizer(), max_length=5)
