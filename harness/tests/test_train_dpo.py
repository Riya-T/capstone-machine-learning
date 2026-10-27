"""Tests DPO preference loading and chat formatting.

Usage:
    uv run pytest tests/test_train_dpo.py
"""

import json

import pytest

from harness.train_dpo import chat_format, load_preferences


def test_load_preferences_extracts_dpo_columns_and_ignores_metadata(tmp_path):
    source = tmp_path / "preferences.jsonl"
    source.write_text(
        json.dumps(
            {
                "prompt": "write code",
                "chosen": "better code",
                "rejected": "worse code",
                "chosen_scores": [[1.5]],
            }
        )
        + "\n"
    )

    assert load_preferences(source) == [
        {"prompt": "write code", "chosen": "better code", "rejected": "worse code"}
    ]


@pytest.mark.parametrize(
    "line",
    [
        "{not json}",
        "[]",
        '{"prompt":"p","chosen":"c","rejected":""}',
        '{"prompt":"p","chosen":"same","rejected":"same"}',
    ],
)
def test_load_preferences_rejects_invalid_rows(tmp_path, line):
    source = tmp_path / "preferences.jsonl"
    source.write_text(line + "\n")

    with pytest.raises(ValueError):
        load_preferences(source)


def test_chat_format_adds_model_chat_template_to_writer_prompt():
    class Tokenizer:
        chat_template = "present"

        def apply_chat_template(self, messages, *, tokenize, add_generation_prompt):
            assert messages == [{"role": "user", "content": "write code"}]
            assert tokenize is False
            assert add_generation_prompt is True
            return "<assistant-prefix>"

    rows = [{"prompt": "write code", "chosen": "good", "rejected": "bad"}]
    assert chat_format(rows, Tokenizer()) == [
        {"prompt": "<assistant-prefix>", "chosen": "good", "rejected": "bad"}
    ]
