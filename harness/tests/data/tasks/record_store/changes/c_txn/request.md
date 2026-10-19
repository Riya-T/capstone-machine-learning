Add transactions to `records.py`.

Add a method `RecordStore.transaction()` used as a context manager:

```python
with store.transaction():
    store.add(...)
    store.update(...)
```

- Operations inside the block take effect immediately for this store object,
  so reads inside the block see earlier changes from the same block.
- Nothing is written to the file until the block exits. If the block exits
  normally, all of its changes are saved together.
- If an exception leaves the block, every change made inside the block is
  undone, the file is left as it was before the block, and the exception
  propagates unchanged.
- An operation that fails inside the block still has no effect of its own; if
  the exception is caught inside the block, the block continues.
- Calling `transaction()` while a transaction is already open on the same
  store raises `RuntimeError`.
- Whether ids handed out inside an undone transaction are reused is up to you.

All existing behavior must keep working.
