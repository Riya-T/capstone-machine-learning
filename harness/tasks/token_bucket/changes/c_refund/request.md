Let a request be refunded in `limiter.py`, for example when the work it
asked for was never done.

- Add `RateLimiter.refund(receipt)`: undoes the successful request that
  returned this receipt number. From then on that request no longer counts
  against its client: if the request was made in the current window,
  `get_remaining` for that client goes up by 1 and the client may make one
  more request in this window. A request made in an earlier window can also
  be refunded; that leaves `get_remaining` unchanged, because the request
  never counted against the current window.
- `refund` raises `KeyError` when no successful request has returned that
  receipt number, including values that are not integers at all, such as
  `None` or `"1"`. It raises `LimiterError` when the request has already
  been refunded. In both cases nothing changes.
- Add `RateLimiter.get_receipts(client_id) -> list[int]`: the receipt
  numbers of the client's successful requests that have not been refunded,
  oldest first, from every window so far. It raises `KeyError` for a client
  that is not registered.
- A refund does not change the time, and the refunded receipt number is not
  reused: the next successful request still gets the next unused number.

For example, with `RateLimiter(window=5)` and `add_client("alice", 2)`:
`request("alice")` returns 1 and `request("alice")` returns 2, both at
time 0. After `tick(5)`, `get_receipts("alice")` is `[1, 2]` and
`get_remaining("alice")` is 2. After `refund(1)`, `get_receipts("alice")`
is `[2]` and `get_remaining("alice")` is still 2.

All existing behavior must keep working.
