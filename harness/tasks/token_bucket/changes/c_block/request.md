Let clients in `limiter.py` be blocked, for example while abuse is being
investigated.

- Add `RateLimiter.block(client_id)`, `RateLimiter.unblock(client_id)` and
  `RateLimiter.is_blocked(client_id) -> bool`. All three raise `KeyError`
  for a client that is not registered. New clients are not blocked.
  Blocking a blocked client, or unblocking one that is not blocked, does
  nothing.
- Add `class ClientBlocked(LimiterError)` to `limiter.py`.
- While a client is blocked, `request` raises `ClientBlocked` and changes
  nothing: the request is not recorded and no receipt number is used up.
- While a client is blocked, `get_remaining` returns 0.
- Unblocking restores the client's normal behavior. Successful requests made
  before the block still count in their window, so `get_remaining` goes back
  to what it would have been without the block.
- `ClientBlocked` is checked after `KeyError` and before `RateLimited`.
- Blocking and unblocking do not change the time or the receipt numbers.

All existing behavior must keep working.
