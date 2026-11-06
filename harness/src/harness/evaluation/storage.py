"""Publish immutable evaluation artifacts atomically, without replacing evidence.

Usage:
    publish_new(Path("results/snapshot.json"), encoded_json)
    # A failed write never publishes a truncated final filename.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .records import EvaluationError


def check_existing(path: Path, data: bytes) -> bool:
    if path.is_symlink():
        raise EvaluationError(f"Refusing symlinked output: {path}")
    if path.exists():
        if not path.is_file() or path.read_bytes() != data:
            raise EvaluationError(f"Refusing to overwrite {path}; use a new output directory")
        return True
    return False


def publish_new(path: Path, data: bytes) -> None:
    """Flush a sibling temporary file, then link it into place without overwrite."""
    path = Path(path)
    if check_existing(path, data):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".evaluation-pending-", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Hard-link creation is atomic and fails if any final path already exists.
            os.link(temporary, path)
        except FileExistsError:
            if not check_existing(path, data):
                raise EvaluationError(f"Output disappeared during publication: {path}") from None
        if os.name != "nt":
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
