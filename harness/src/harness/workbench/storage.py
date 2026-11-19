"""Publish workbench files without requiring Windows hard-link permissions.

Usage: publish_new(Path("report/comparison.json"), encoded_json)
Existing evaluation publication stays unchanged; POSIX reuses its implementation.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from ..evaluation.records import EvaluationError
from ..evaluation.storage import check_existing
from ..evaluation.storage import publish_new as publish_posix


def publish_new(path, data):
    """Windows rename refuses an existing destination; never use os.replace.

    Source and destination are siblings, so publication stays on one filesystem.
    The temporary file is flushed and closed before the destination is exposed.
    """
    if os.name != "nt":
        return publish_posix(path, data)
    path = Path(path)
    if check_existing(path, data):
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".collection-pending-", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.rename(temporary, path)
        except FileExistsError:
            if not check_existing(path, data):
                raise EvaluationError("Output disappeared during publication") from None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
