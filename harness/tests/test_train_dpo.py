"""Tests DPO training: preference loading, chat formatting, tokenizing, the
training order, the loss, which tokens are scored, and that a training step
changes only the LoRA adapters while the reference model stays fixed.

The tests under "Torch" need the training extras and are skipped without
them (CI doesn't install them). They run on a tiny random Qwen2 model on the
CPU, so no GPU or model download is needed.

Usage:
    uv run pytest tests/test_train_dpo.py
    # with torch, on a compute node, in a throwaway CPU-only venv:
    #   export UV_CACHE_DIR=/tmp/$USER-uvcache V=/tmp/$USER-train
    #   uv venv --python 3.11 $V
    #   VIRTUAL_ENV=$V uv pip install torch --index-url https://download.pytorch.org/whl/cpu
    #   VIRTUAL_ENV=$V uv pip install -e . pytest "transformers>=4.46,<5" "peft>=0.14,<1"
    #   $V/bin/pytest tests/test_train_dpo.py
"""

import json
import math
import random

import pytest

from harness.train_dpo import chat_format, epoch_order, load_preferences, tokenize


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


class _Tokenizer:
    """One token per character; the end-of-turn token is 0."""

    eos_token_id = 0

    def __call__(self, text, *, add_special_tokens):
        assert add_special_tokens is False
        return {"input_ids": [ord(ch) for ch in text]}


def test_tokenize_appends_end_of_turn_to_both_completions_only():
    rows = [{"prompt": "ab", "chosen": "xy", "rejected": "z"}]

    assert tokenize(rows, _Tokenizer(), max_length=5) == [
        {"prompt": [97, 98], "chosen": [120, 121, 0], "rejected": [122, 0]}
    ]


def test_tokenize_refuses_pairs_where_either_completion_is_too_long():
    rows = [{"prompt": "ab", "chosen": "x", "rejected": "xyz"}]

    with pytest.raises(ValueError, match="1 examples exceed --max-length 5: pair 0 rejected"):
        tokenize(rows, _Tokenizer(), max_length=5)


def test_epoch_order_matches_the_order_dpo3_was_trained_in():
    # Computed with the loop that was inline in train() before it became
    # epoch_order, so trained checkpoints stay reproducible from their seed.
    assert epoch_order(6, 2, random.Random(42)) == [5, 0, 4, 2, 1, 3, 1, 5, 0, 2, 3, 4]
    assert epoch_order(6, 1.5, random.Random(7)) == [2, 1, 3, 5, 0, 4, 4, 0, 2]


def test_epoch_order_shuffles_every_pair_once_per_whole_epoch():
    order = epoch_order(10, 2.5, random.Random(0))

    assert sorted(order[:10]) == list(range(10))
    assert sorted(order[10:20]) == list(range(10))
    assert len(order[20:]) == 5 and len(set(order[20:])) == 5
    assert order[:10] != order[10:20]


# --- Torch -------------------------------------------------------------------

VOCAB = 32


@pytest.fixture
def torch():
    return pytest.importorskip("torch")


@pytest.fixture
def tiny_model(torch):
    """A random two-layer Qwen2 model: the same architecture as the writer."""
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(0)
    config = transformers.Qwen2Config(
        vocab_size=VOCAB,
        hidden_size=16,
        intermediate_size=32,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        max_position_embeddings=64,
    )
    return transformers.Qwen2ForCausalLM(config).eval()


@pytest.fixture
def lora_model(tiny_model):
    """The tiny model with LoRA on every linear layer, as train() sets it up."""
    peft = pytest.importorskip("peft")
    config = peft.LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0, target_modules="all-linear", task_type="CAUSAL_LM"
    )
    return peft.get_peft_model(tiny_model, config)


PAIRS = [
    {"prompt": [1, 2, 3], "chosen": [4, 5, 6, 0], "rejected": [7, 8, 0]},
    {"prompt": [9, 10], "chosen": [11, 12, 0], "rejected": [13, 14, 15, 0]},
    {"prompt": [3, 1, 4, 1], "chosen": [5, 9, 0], "rejected": [2, 6, 0]},
]


def _train(torch, model, order, *, accumulation=1, lr=1e-2):
    from harness.train_dpo import optimizer_steps, reference_logps

    reference = reference_logps(model, PAIRS)
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
    schedule = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
    entries = list(
        optimizer_steps(
            model,
            PAIRS,
            reference,
            order,
            optimizer,
            schedule,
            beta=0.1,
            accumulation=accumulation,
            max_grad_norm=1.0,
        )
    )
    return reference, entries


def test_dpo_loss_is_log_2_when_policy_equals_reference(torch):
    from harness.train_dpo import dpo_loss

    logp = torch.tensor([-12.0, -3.5])
    loss, margin = dpo_loss(logp, logp - 1, logp, logp - 1, beta=0.1)

    assert torch.allclose(margin, torch.zeros(2))
    assert torch.allclose(loss, torch.full((2,), math.log(2)))


def test_dpo_loss_matches_the_sigmoid_formula_and_rewards_preferring_chosen(torch):
    from harness.train_dpo import dpo_loss

    policy_chosen = torch.tensor(-10.0, requires_grad=True)
    policy_rejected = torch.tensor(-20.0, requires_grad=True)
    loss, margin = dpo_loss(policy_chosen, policy_rejected, -12.0, -15.0, beta=0.5)
    loss.backward()

    # beta * ((-10 - -12) - (-20 - -15)) = 0.5 * (2 + 5)
    assert margin.item() == pytest.approx(3.5)
    assert loss.item() == pytest.approx(math.log1p(math.exp(-3.5)))
    # Lowering the loss means raising the chosen and lowering the rejected.
    assert policy_chosen.grad < 0 < policy_rejected.grad


def test_completion_logp_scores_only_the_completion_tokens(torch, tiny_model):
    from harness.train_dpo import completion_logp

    prompt, completion = [1, 2, 3, 4], [5, 6, 7, 0]
    ids = torch.tensor([prompt + completion])
    with torch.no_grad():
        logp = torch.log_softmax(tiny_model(input_ids=ids).logits[0].float(), dim=-1)
        # Position t predicts token t + 1: the last prompt position predicts
        # the first completion token, and no prompt token is scored.
        expected = sum(logp[len(prompt) - 1 + j, token] for j, token in enumerate(completion))
        whole = completion_logp(tiny_model, prompt, completion)
        chunked = completion_logp(tiny_model, prompt, completion, chunk=3)

    assert whole.item() == pytest.approx(expected.item(), abs=1e-5)
    assert chunked.item() == pytest.approx(whole.item(), abs=1e-5)


def test_completion_logp_goes_through_peft_to_the_adapted_model(torch, lora_model):
    from harness.train_dpo import completion_logp

    with torch.no_grad():
        for name, param in lora_model.named_parameters():
            if "lora_B" in name:
                param.fill_(0.1)
        adapted = completion_logp(lora_model, [1, 2], [3, 4, 0])
        with lora_model.disable_adapter():
            base = completion_logp(lora_model, [1, 2], [3, 4, 0])

    assert adapted.item() != pytest.approx(base.item(), abs=1e-4)


def test_training_changes_only_the_lora_adapters(torch, lora_model):
    before = {name: p.detach().clone() for name, p in lora_model.named_parameters()}
    trainable = {name for name, p in lora_model.named_parameters() if p.requires_grad}

    _train(torch, lora_model, order=[0, 1, 2, 0, 1, 2])

    assert trainable and all("lora_" in name for name in trainable)
    for name, param in lora_model.named_parameters():
        if name in trainable:
            continue
        assert torch.equal(param, before[name]), f"base weight {name} changed"
    # lora_B starts at zero, so every adapter is a no-op until trained.
    changed_b = [
        name
        for name in trainable
        if "lora_B" in name and not torch.equal(lora_model.get_parameter(name), before[name])
    ]
    assert changed_b, "no adapter was trained"


def test_reference_is_the_untrained_model_and_ignores_trained_adapters(torch, lora_model):
    from harness.train_dpo import completion_logp, reference_logps

    reference, _ = _train(torch, lora_model, order=[0, 1, 2] * 3)
    flat = [logp for pair in reference for logp in pair]

    after = [logp for pair in reference_logps(lora_model, PAIRS) for logp in pair]
    assert after == pytest.approx(flat, abs=1e-5)
    with torch.no_grad():
        trained = completion_logp(lora_model, PAIRS[0]["prompt"], PAIRS[0]["chosen"]).item()
    assert trained != pytest.approx(flat[0], abs=1e-4), "the adapters were not trained"


def test_training_raises_the_reward_margin_on_the_training_pairs(torch, lora_model):
    _, entries = _train(torch, lora_model, order=[0, 1, 2] * 10, accumulation=3)

    assert entries[0]["loss"] == pytest.approx(math.log(2), abs=1e-4)
    assert entries[-1]["loss"] < entries[0]["loss"]
    assert entries[-1]["reward_margin"] > 0
    assert entries[-1]["reward_accuracy"] == 1.0


def test_one_log_entry_per_optimizer_step_including_a_partial_last_step(torch, lora_model):
    _, entries = _train(torch, lora_model, order=[0, 1, 2, 0, 1], accumulation=2)

    assert [e["step"] for e in entries] == [1, 2, 3]
    assert {e["steps"] for e in entries} == {3}
    assert [e["epoch"] for e in entries] == [round(2 / 3, 3), round(4 / 3, 3), round(5 / 3, 3)]
    assert set(entries[0]) == {
        "step",
        "steps",
        "epoch",
        "loss",
        "reward_margin",
        "reward_accuracy",
        "grad_norm",
        "learning_rate",
    }
