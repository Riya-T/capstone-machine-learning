"""Merge a PEFT LoRA adapter into its base model, one weight file at a time.

Ollama no longer loads LoRA adapters, so a trained writer is served as a
merged model. PEFT's merge_and_unload needs the whole model in memory (about
16 GB in bf16 for a 7B model); this adds W += (alpha / r) * B @ A to each
targeted weight shard by shard, so it needs only about one shard of memory.
The output is a Hugging Face model directory (bf16 safetensors, config and
tokenizer) for llama.cpp's GGUF converter (see "Serving the trained writer"
in the README).

Usage (from harness/):
    .venv/bin/python scripts/merge_lora.py BASE_DIR ADAPTER_DIR OUT_DIR
"""

import argparse
import json
import shutil
from pathlib import Path

PREFIX = "base_model.model."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("base", type=Path)
    parser.add_argument("adapter", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument(
        "--dtype",
        choices=["base", "float16"],
        default="base",
        help="type of the merged weights (the others keep theirs); float16 keeps more of "
        "the small LoRA update than bf16",
    )
    args = parser.parse_args()

    import torch
    from safetensors import safe_open
    from safetensors.torch import save_file

    config = json.loads((args.adapter / "adapter_config.json").read_text())
    if config.get("use_dora") or config.get("use_rslora"):
        raise SystemExit("DoRA and rsLoRA adapters are not supported")
    scale = config["lora_alpha"] / config["r"]

    lora = {}
    with safe_open(args.adapter / "adapter_model.safetensors", "pt") as f:
        for key in f.keys():  # noqa: SIM118 (a safetensors handle, not a dict)
            name, part = key.removeprefix(PREFIX).rsplit(".lora_", 1)
            lora.setdefault(name + ".weight", {})[part.split(".")[0]] = f.get_tensor(key)
    if any(set(parts) != {"A", "B"} for parts in lora.values()):
        raise SystemExit("adapter has unpaired lora_A/lora_B weights")

    args.out.mkdir(parents=True, exist_ok=True)
    index = json.loads((args.base / "model.safetensors.index.json").read_text())
    merged = set()
    for shard in sorted(set(index["weight_map"].values())):
        tensors = {}
        with safe_open(args.base / shard, "pt") as f:
            for key in f.keys():  # noqa: SIM118
                weight = f.get_tensor(key)
                if key in lora:
                    dtype = torch.float16 if args.dtype == "float16" else weight.dtype
                    a, b = lora[key]["A"].float(), lora[key]["B"].float()
                    weight = (weight.float() + scale * (b @ a)).to(dtype)
                    merged.add(key)
                tensors[key] = weight.contiguous()
        save_file(tensors, args.out / shard, metadata={"format": "pt"})
        print(f"{shard}: {len(tensors)} tensors", flush=True)
    missing = set(lora) - merged
    if missing:
        raise SystemExit(f"{len(missing)} adapter weights have no base weight, e.g. {min(missing)}")
    shutil.copy(args.base / "model.safetensors.index.json", args.out)
    for path in args.base.iterdir():
        if path.suffix in (".json", ".txt") and not path.name.startswith("model."):
            shutil.copy(path, args.out)
    print(f"merged {len(merged)} weights (scale {scale}) into {args.out}")


if __name__ == "__main__":
    main()
