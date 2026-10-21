"""Gateway: registered clients, an allow list, and the messages each sent.

Planted bug (initial version): get_allowed lists clients in the order they
were allowed, not the order they were registered. The public checks only
allow clients in registration order, so only the hidden initial tests
catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from gateway import Gateway
    gateway = Gateway()
    gateway.register("alpha")
    gateway.allow("alpha")
    gateway.send("alpha", "hello")
"""


class GatewayError(Exception):
    pass


class AccessDenied(GatewayError):
    pass


def check_message(message):
    if not isinstance(message, str) or not message:
        raise ValueError(f"message must be a non-empty str, got {message!r}")


class Gateway:
    def __init__(self):
        self._messages = {}  # client id -> list of messages, in registration order
        self._allowed = {}  # client id -> None, in the order allowed

    def register(self, client_id):
        if not isinstance(client_id, str) or not client_id:
            raise ValueError("client_id must be a non-empty str")
        if client_id in self._messages:
            raise GatewayError(f"client {client_id!r} is already registered")
        self._messages[client_id] = []

    def allow(self, client_id):
        self._require(client_id)
        self._allowed[client_id] = None

    def revoke(self, client_id):
        self._require(client_id)
        self._allowed.pop(client_id, None)

    def send(self, client_id, message):
        self._require(client_id)
        check_message(message)
        if client_id not in self._allowed:
            raise AccessDenied(f"client {client_id!r} is not allowed to send")
        self._messages[client_id].append(message)

    def get_clients(self):
        return list(self._messages)

    def get_allowed(self):
        return list(self._allowed)

    def get_messages(self, client_id):
        self._require(client_id)
        return list(self._messages[client_id])

    def _require(self, client_id):
        # Non-str ids are never stored, so they count as "not registered" too.
        if not isinstance(client_id, str) or client_id not in self._messages:
            raise KeyError(client_id)
