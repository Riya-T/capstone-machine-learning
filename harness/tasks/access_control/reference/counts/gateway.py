"""Gateway with message statistics.

Correct solution for access_control after c_counts.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from gateway import Gateway
    gateway = Gateway()
    gateway.register("alpha")
    gateway.allow("alpha")
    gateway.send("alpha", "hello")
    gateway.get_ranking()
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
        self._allowed = set()

    def register(self, client_id):
        if not isinstance(client_id, str) or not client_id:
            raise ValueError("client_id must be a non-empty str")
        if client_id in self._messages:
            raise GatewayError(f"client {client_id!r} is already registered")
        self._messages[client_id] = []

    def allow(self, client_id):
        self._require(client_id)
        self._allowed.add(client_id)

    def revoke(self, client_id):
        self._require(client_id)
        self._allowed.discard(client_id)

    def send(self, client_id, message):
        self._require(client_id)
        check_message(message)
        if client_id not in self._allowed:
            raise AccessDenied(f"client {client_id!r} is not allowed to send")
        self._messages[client_id].append(message)

    def get_clients(self):
        return list(self._messages)

    def get_allowed(self):
        return [c for c in self._messages if c in self._allowed]

    def get_messages(self, client_id):
        self._require(client_id)
        return list(self._messages[client_id])

    def get_message_count(self, client_id):
        self._require(client_id)
        return len(self._messages[client_id])

    def get_character_count(self, client_id):
        self._require(client_id)
        return sum(len(m) for m in self._messages[client_id])

    def get_total_messages(self):
        return sum(len(msgs) for msgs in self._messages.values())

    def get_ranking(self):
        # sorted() is stable, so equal counts keep registration order.
        counts = [(c, len(msgs)) for c, msgs in self._messages.items()]
        return sorted(counts, key=lambda pair: -pair[1])

    def _require(self, client_id):
        # Non-str ids are never stored, so they count as "not registered" too.
        if not isinstance(client_id, str) or client_id not in self._messages:
            raise KeyError(client_id)
