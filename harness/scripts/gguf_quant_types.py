"""Write a llama-quantize --tensor-type-file that repeats a GGUF's quant types.

Q4_K_M keeps some layers at Q6_K, and which ones has changed between
llama.cpp versions, so a current llama-quantize does not pick the same
layers as the official Qwen2.5-Coder-7B Q4_K_M GGUF that the base writer
runs on. This lists every quantized tensor of a reference GGUF as an
anchored `^name$=type` line, so the trained writer is quantized exactly like
the base writer. Needs llama.cpp's gguf-py on PYTHONPATH.

Usage:
    PYTHONPATH=llama.cpp/gguf-py python scripts/gguf_quant_types.py REF.gguf types.txt
"""

import argparse
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("reference", type=Path, help="GGUF whose quant types to copy")
    parser.add_argument("out", type=Path)
    args = parser.parse_args()

    from gguf import GGUFReader

    lines, counts = [], {}
    for tensor in GGUFReader(args.reference).tensors:
        kind = tensor.tensor_type.name
        if kind in ("F32", "F16", "BF16"):
            continue
        lines.append(f"^{re.escape(tensor.name)}$={kind.lower()}")
        counts[kind] = counts.get(kind, 0) + 1
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} tensors: {counts}")


if __name__ == "__main__":
    main()
