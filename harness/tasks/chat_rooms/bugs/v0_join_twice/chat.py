"""Chat rooms: users, the rooms they are members of, and each room's messages.

Planted bug (initial version): joining a room one is already a member of
is accepted and adds the user to the member list a second time, instead of
raising ChatError. The public checks never join twice, so only the hidden
initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from chat import ChatServer
    server = ChatServer()
    server.add_user("alice")
    server.join("alice", "general")
    server.post("alice", "general", "hello")
"""


class ChatError(Exception):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class ChatServer:
    def __init__(self):
        self._users = set()
        self._members = {}  # room -> list of usernames in join order, rooms in creation order
        self._messages = {}  # room -> list of (username, text), oldest first

    def add_user(self, username):
        check_text(username, "username")
        if username in self._users:
            raise ChatError(f"user {username!r} already exists")
        self._users.add(username)

    def join(self, username, room):
        self._require_user(username)
        check_text(room, "room")
        if room not in self._members:
            self._members[room] = []
            self._messages[room] = []
        self._members[room].append(username)

    def leave(self, username, room):
        self._require_user(username)
        self._require_room(room)
        self._require_member(username, room)
        self._members[room].remove(username)

    def post(self, username, room, text):
        self._require_user(username)
        self._require_room(room)
        check_text(text, "text")
        self._require_member(username, room)
        self._messages[room].append((username, text))

    def get_members(self, room):
        self._require_room(room)
        return list(self._members[room])

    def get_messages(self, room):
        self._require_room(room)
        return list(self._messages[room])

    def get_rooms(self):
        return list(self._members)

    def _require_user(self, username):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(username, str) or username not in self._users:
            raise KeyError(username)

    def _require_room(self, room):
        if not isinstance(room, str) or room not in self._members:
            raise KeyError(room)

    def _require_member(self, username, room):
        if username not in self._members[room]:
            raise ChatError(f"{username!r} is not in {room!r}")
