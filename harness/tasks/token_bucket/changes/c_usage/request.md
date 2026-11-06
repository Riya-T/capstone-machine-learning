Add usage queries to `limiter.py`, so operators can see when each client
made its requests.

- Add `RateLimiter.get_request_times(client_id) -> list[int]`: the time of
  every successful request the client has made, oldest first. Two requests
  made at the same time both appear.
- Add `RateLimiter.get_usage(client_id, start, end) -> int`: the number of
  successful requests the client made at a time `t` with
  `start <= t < end`.
- Add `RateLimiter.get_active_clients(start, end) -> list[str]`: the same
  ids as `get_clients()`, in the same order, keeping only the clients that
  made at least one successful request at a time `t` with
  `start <= t < end`. For example, if `alice`, `bob` and `carol` were added
  in that order and only `carol` and then `alice` made requests in the
  range, the result is `["alice", "carol"]`.
- `get_request_times` and `get_usage` raise `KeyError` for a client id
  that is not registered, and so for `None`, `1` or any other value that
  is not a string. They never return `[]` or 0 for such a client.
- `start` and `end` must each be an `int` that is 0 or more, and `start`
  must not be greater than `end`; otherwise `ValueError` is raised. A range
  with `start == end` contains no times. Which error `get_usage` raises
  for a client that is not registered when the range is also invalid is
  unspecified.
- Only successful requests appear in these queries. A `request` call that
  raised is never counted, whatever the reason it raised.

All existing behavior must keep working.
