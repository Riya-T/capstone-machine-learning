# Gateway

Write a module `gateway.py` that keeps the clients of a message gateway, an
allow list of the clients that may send, and the messages each client has
sent.

## Interface

```python
class GatewayError(Exception): ...


class AccessDenied(GatewayError): ...


class Gateway:
    def __init__(self): ...
    def register(self, client_id: str) -> None: ...
    def allow(self, client_id: str) -> None: ...
    def revoke(self, client_id: str) -> None: ...
    def send(self, client_id: str, message: str) -> None: ...
    def get_clients(self) -> list[str]: ...
    def get_allowed(self) -> list[str]: ...
    def get_messages(self, client_id: str) -> list[str]: ...
```

## Clients

- `register(client_id)` adds a client. An empty id raises `ValueError`, and
  registering an id that is already registered raises `GatewayError`. A new
  client is not on the allow list and has sent nothing.
- `get_clients()` returns the ids of all registered clients, in the order
  they were registered.
- Every other method raises `KeyError` when given a client id that is not
  registered, including values that are not strings at all, such as `None`
  or `1`.

## Allow list

- `allow(client_id)` puts the client on the allow list. `revoke(client_id)`
  takes it off. Both first check that the client is registered and raise
  `KeyError` if not. After that check, allowing a registered client that is
  already allowed, or revoking a registered client that is not allowed,
  does nothing.
- `get_allowed()` returns the same ids as `get_clients()`, in the same
  order, but keeps only those that are on the allow list right now. The
  order in which clients were allowed does not matter. For example, after registering `"a"`, `"b"` and `"c"` and then allowing
  `"c"` and then `"a"`, `get_allowed()` returns `["a", "c"]`.

## Messages

- `send(client_id, message)` records the message for the client. The
  message must be a non-empty `str`, or `ValueError` is raised. A client
  that is not on the allow list cannot send: `AccessDenied` is raised.
- `get_messages(client_id)` returns the messages the client has sent, oldest
  first. Revoking a client keeps the messages it sent before.

When `send` has several problems, the first of these is raised:

1. `KeyError` for a client that is not registered;
2. `ValueError` for an invalid message;
3. `AccessDenied`.

A failed call has no effect: if a method raises, the clients, the allow list
and every message list are unchanged.

## Unspecified behavior

Behavior not described here is unspecified, and no test depends on it. This
includes ids that are not strings passed to `register`, what happens if a
returned list is changed, the text of error messages, saving the gateway to
a file, and use from several threads.
