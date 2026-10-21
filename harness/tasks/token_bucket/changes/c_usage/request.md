Add usage queries to `limiter.py`, so operators can see when each client
made its requests.

- Add `RateLimiter.get_request_times(client_id) -> list[int]`: the time of
  every successful request the client has made, oldest first. Two requests
  made at the same time both appear.
- Add `RateLimiter.get_usage(client_id, start, end) -> int`: the number of
  successful requests the client made at a time `t` with
  `start <= t < end`.
- Add `RateLimiter.get_active_clients(start, end) -> list[str]`: the ids of
  the clients that made at least one successful request at a time `t` with
  `start <= t < end`, in the order the clients were added.
- `start` and `end` must each be an `int` that is 0 or more (not a `bool`),
  and `start` must not be greater than `end`; otherwise `ValueError` is
  raised. A range with `start == end` contains no times. `KeyError` for a
  client that is not registered is raised before any `ValueError`.
- Only successful requests appear in these queries. A `request` call that
  raised is never counted, whatever the reason it raised.

All existing behavior must keep working.
