Require every record's email to be unique in `records.py`.

- `add` raises `ValidationError` if another stored record already has the
  same email, and `update` raises it if the update would give the record the
  same email as a different record.
- Emails are compared case-insensitively, using `str.casefold`.
- Updating a record to its own current email, in any letter case, is allowed.
- Deleting a record frees its email for reuse.
- As before, a failed operation has no effect.

The earlier rule that two records may share an email no longer applies. All
other existing behavior must keep working.
