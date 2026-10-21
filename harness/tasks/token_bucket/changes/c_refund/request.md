Let a request be refunded in `limiter.py`, for example when the work it
asked for was never done.

- Add `RateLimiter.refund(receipt)`: undoes the successful request that
  returned this receipt number. From then on that request no longer counts
  against its client: if the request was made in the current window,
  `get_remaining` for that client goes up by 1 and the client may make one
  more request in this window. A request made in an earlier window can also
  be refunded.
- `refund` raises `KeyError` when no successful request has returned that
  receipt number, including values that are not integers at all, such as
  `None` or `"1"`. It raises `LimiterError` when the request has already
  been refunded. `KeyError` is checked first. In both cases nothing changes.
- Add `RateLimiter.get_receipts(client_id) -> list[int]`: the receipt
  numbers of the client's successful requests that have not been refunded,
  oldest first. It raises `KeyError` for a client that is not registered.
- A refund does not change the time, and the refunded receipt number is not
  reused: the next successful request still gets the next unused number.

All existing behavior must keep working.
