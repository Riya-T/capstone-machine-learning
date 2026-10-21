"""Chat rooms with muting and ways to search the messages.

Correct solution for chat_rooms after c_mute and c_search.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from chat import ChatServer
    server = ChatServer()
    server.add_user("alice")
    server.join("alice", "general")
    server.post("alice", "general", "hello")
    server.get_messages("general", by="alice", containing="ell")
"""


class ChatError(Exception):
    pass


class UserMuted(ChatError):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class ChatServer:
    def __init__(self):
        self._users = set()
        self._muted = set()
        self._members = {}  # room -> list of usernames in join order, rooms in creation order
        self._messages = {}  # room -> list of (username, text), oldest first
        self._posts = []  # (username, room, text) over all rooms, oldest first

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
        if username in self._members[room]:
            raise ChatError(f"{username!r} is already in {room!r}")
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
        if username in self._muted:
            raise UserMuted(f"{username!r} is muted")
        self._messages[room].append((username, text))
        self._posts.append((username, room, text))

    def get_members(self, room):
        self._require_room(room)
        return list(self._members[room])

    def get_messages(self, room, by=None, containing=None):
        self._require_room(room)
        if by is not None:
            self._require_user(by)
        if containing is not None and not isinstance(containing, str):
            raise ValueError(f"containing must be None or a str, got {containing!r}")
        return [
            (user, text)
            for user, text in self._messages[room]
            if (by is None or user == by) and (containing is None or containing in text)
        ]

    def get_rooms(self):
        return list(self._members)

    def get_posts(self, username):
        self._require_user(username)
        return [(room, text) for user, room, text in self._posts if user == username]

    def mute(self, username):
        self._require_user(username)
        self._muted.add(username)

    def unmute(self, username):
        self._require_user(username)
        self._muted.discard(username)

    def is_muted(self, username):
        self._require_user(username)
        return username in self._muted

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
