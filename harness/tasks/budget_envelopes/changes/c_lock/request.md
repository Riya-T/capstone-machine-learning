Let envelopes in `envelopes.py` be locked, so the money in them stays put,
for example once the rent for the month is set aside.

- Add `class EnvelopeLocked(BudgetError)` to `envelopes.py`.
- Add `Budget.lock(name)`, `Budget.unlock(name)` and
  `Budget.is_locked(name) -> bool`. All three raise `KeyError` for an
  envelope that does not exist. New envelopes are unlocked. Locking a locked
  envelope, or unlocking an unlocked one, does nothing.
- While an envelope is locked, every call that would put money into it or
  take money out of it raises `EnvelopeLocked` and changes nothing. Today
  that is `allocate` and `spend`; any method added later that moves money
  must respect locks the same way. `get_balance` still works, and the
  envelope still appears in `get_envelopes`.
- `EnvelopeLocked` is checked after every `KeyError` and `ValueError` check
  and before `NotEnoughMoney`.
- Locking and unlocking change no balance and not the unassigned money.

All existing behavior must keep working.
