"""Gateway where clients can be banned and put in groups.

Planted bug (after c_ban and c_groups): groups were added correctly, but
ban no longer takes the client off the allow list.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from gateway import Gateway
    gateway = Gateway()
    gateway.register("alpha")
    gateway.create_group("staff")
    gateway.assign_group("alpha", "staff")
    gateway.allow_group("staff")
"""


class GatewayError(Exception):
    pass


class AccessDenied(GatewayError):
    pass


class ClientBanned(GatewayError):
    pass


def check_message(message):
    if not isinstance(message, str) or not message:
        raise ValueError(f"message must be a non-empty str, got {message!r}")


class Gateway:
    def __init__(self):
        self._messages = {}  # client id -> list of messages, in registration order
        self._allowed = set()
        self._banned = set()
        self._groups = {}  # group -> set of client ids, in creation order
        self._group_of = {}  # client id -> group

    def register(self, client_id):
        if not isinstance(client_id, str) or not client_id:
            raise ValueError("client_id must be a non-empty str")
        if client_id in self._messages:
            raise GatewayError(f"client {client_id!r} is already registered")
        self._messages[client_id] = []

    def allow(self, client_id):
        self._require(client_id)
        self._require_not_banned(client_id)
        self._allowed.add(client_id)

    def revoke(self, client_id):
        self._require(client_id)
        self._allowed.discard(client_id)

    def send(self, client_id, message):
        self._require(client_id)
        check_message(message)
        self._require_not_banned(client_id)
        if client_id not in self._allowed:
            raise AccessDenied(f"client {client_id!r} is not allowed to send")
        self._messages[client_id].append(message)

    def ban(self, client_id):
        self._require(client_id)
        self._banned.add(client_id)

    def unban(self, client_id):
        self._require(client_id)
        self._banned.discard(client_id)

    def is_banned(self, client_id):
        self._require(client_id)
        return client_id in self._banned

    def create_group(self, group):
        if not isinstance(group, str) or not group:
            raise ValueError("group must be a non-empty str")
        if group in self._groups:
            raise GatewayError(f"group {group!r} already exists")
        self._groups[group] = set()

    def assign_group(self, client_id, group):
        self._require(client_id)
        self._require_group(group)
        old = self._group_of.get(client_id)
        if old is not None:
            self._groups[old].discard(client_id)
        self._groups[group].add(client_id)
        self._group_of[client_id] = group

    def allow_group(self, group):
        members = self.get_members(group)
        for client_id in members:
            self._require_not_banned(client_id)
        for client_id in members:
            self.allow(client_id)

    def revoke_group(self, group):
        for client_id in self.get_members(group):
            self.revoke(client_id)

    def get_clients(self):
        return list(self._messages)

    def get_allowed(self):
        return [c for c in self._messages if c in self._allowed]

    def get_banned(self):
        return [c for c in self._messages if c in self._banned]

    def get_messages(self, client_id):
        self._require(client_id)
        return list(self._messages[client_id])

    def get_groups(self):
        return list(self._groups)

    def get_group(self, client_id):
        self._require(client_id)
        return self._group_of.get(client_id)

    def get_members(self, group):
        self._require_group(group)
        return [c for c in self._messages if c in self._groups[group]]

    def _require(self, client_id):
        # Non-str ids are never stored, so they count as "not registered" too.
        if not isinstance(client_id, str) or client_id not in self._messages:
            raise KeyError(client_id)

    def _require_group(self, group):
        if not isinstance(group, str) or group not in self._groups:
            raise KeyError(group)

    def _require_not_banned(self, client_id):
        if client_id in self._banned:
            raise ClientBanned(f"client {client_id!r} is banned")
