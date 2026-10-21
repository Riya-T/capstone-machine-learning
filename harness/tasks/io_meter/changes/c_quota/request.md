Add per-stream quotas to `meter.py`, so a stream can be capped at a total
number of bytes.

- `open_stream` takes a new keyword argument `quota=None`. `None` means no
  quota, as before. Otherwise it must be an `int` of 0 or more (not a
  `bool`); anything else raises `ValueError` and no stream is opened. If
  the id and the quota are both invalid, either `ValueError` may come
  first; `MeterError` for an id already open is still raised after both
  checks.
- A quota is the most bytes the stream may move in total, reads and writes
  added together. A `record_read` or `record_write` whose size would take
  that total above the quota raises `QuotaExceeded` and changes nothing.
  Reaching the quota exactly is allowed, and an operation of size 0 is
  always allowed.
- Add `class QuotaExceeded(MeterError)` to `meter.py`.
- Add `IOMeter.get_quota(stream_id) -> int | None`: the stream's quota, or
  `None` when it has none.
- Add `IOMeter.get_quota_left(stream_id) -> int | None`: the quota minus the
  bytes moved so far, or `None` when the stream has no quota.
- Add `IOMeter.set_quota(stream_id, quota)`, which replaces the quota
  (`None` removes it). It raises `KeyError` for a stream that is not open,
  then `ValueError` for an invalid quota, then `MeterError` when the bytes
  already moved are more than the new quota. In each case nothing changes.
- `get_quota` and `get_quota_left` raise `KeyError` for a stream that is
  not open.
- In `record_read` and `record_write`, `QuotaExceeded` is checked after
  `KeyError` and `ValueError`.

All existing behavior must keep working.
