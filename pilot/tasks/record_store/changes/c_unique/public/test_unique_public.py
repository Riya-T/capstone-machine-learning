"""Public checks for the c_unique change (unique emails). Shown to the
editor, never to the writer.

Usage (with records.py importable, e.g. in the task sandbox):
    python -m pytest changes/c_unique/public/test_unique_public.py
"""

import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}


def test_duplicate_email_is_rejected(tmp_path):
    store = RecordStore(tmp_path / "db")
    store.add(ADA)
    with pytest.raises(ValidationError):
        store.add({**ADA, "name": "Other Ada", "email": "ADA@example.com"})
