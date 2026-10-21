# Rate limiter

Write a module `limiter.py` that limits how many requests each client may
make per window of time. Time is a counter of whole ticks that the caller
advances explicitly; nothing happens on its own.

## Interface

```python
class LimiterError(Exception): ...


class RateLimited(LimiterError): ...


class RateLimiter:
    def __init__(self, window: int): ...
    def add_client(self, client_id: str, allowance: int) -> None: ...
    def tick(self, steps: int = 1) -> None: ...
    def request(self, client_id: str) -> int: ...
    def get_remaining(self, client_id: str) -> int: ...
    def get_time(self) -> int: ...
    def get_clients(self) -> list[str]: ...
```

All times, counts and allowances are whole numbers, as `int`.

## Time and windows

- A new limiter is at time 0. `tick(steps)` moves time forward by `steps`,
  which must be an `int` greater than 0, or `ValueError` is raised. `tick()`
  with no argument moves time forward by 1. `get_time()` returns the
  current time.
- `window` is the length of a window in ticks. It must be an `int` greater
  than 0, or `ValueError` is raised.
- Time is cut into windows of `window` ticks each: times 0 up to
  `window - 1` are the first window, `window` up to `2 * window - 1` the
  second, and so on. The *current window* is the one that contains the
  current time.

## Clients

- `add_client(client_id, allowance)` registers a client that may make up to
  `allowance` successful requests in any one window. An empty id raises
  `ValueError`; an `allowance` that is not an `int` greater than 0 raises
  `ValueError`; a client id that is already registered raises
  `LimiterError`. The `ValueError` checks come before the `LimiterError`
  check.
- `get_clients()` returns the ids of all clients, in the order they were
  added.
- Every other method that takes a client id raises `KeyError` when the id
  is not registered, including values that are not strings at all, such as
  `None` or `1`.

## Requests

- `request(client_id)` records one request for the client, made at the
  current time, and returns a receipt number. Receipt numbers count
  successful requests over the whole limiter, over all clients: the first
  successful request on a limiter returns 1, the next returns 2, and so on.
- If the client has already made `allowance` successful requests in the
  current window, `request` raises `RateLimited` instead. The request is
  not recorded and no receipt number is used up: the next successful
  request, by any client, still gets the next number.
- Requests made in an earlier window do not count against the current one.
- `get_remaining(client_id)` returns how many more requests the client may
  make in the current window: its allowance minus the successful requests
  it has made in the current window. It is never below 0.

When a call has several problems, the first of these is raised:

1. `KeyError` for a client that is not registered;
2. `RateLimited`.

A failed call has no effect: if a method raises, the time, every client's
remaining count and the next receipt number are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `add_client`, `bool` values
passed as numbers, what happens if a returned list is changed, the text of
error messages, saving the limiter to a file, and use from several threads.
