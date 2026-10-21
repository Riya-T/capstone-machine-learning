"""Chat rooms where messages have ids and can be deleted, and users can be
muted.

Planted bug (after c_delete and c_mute): muting was added correctly, but
the rewritten post forgets to return the new message's id, so callers get
None back and can no longer delete what they posted.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from chat import ChatServer
    server = ChatServer()
    server.add_user("alice")
    server.join("alice", "general")
    message_id = server.post("alice", "general", "hello")
    server.mute("alice")
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
        self._rooms_of = {}  # message id -> room, for every id ever given out
        self._messages = {}  # room -> list of (id, username, text) still present, oldest first
        self._next_id = 1

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
        message_id = self._next_id
        self._next_id += 1
        self._rooms_of[message_id] = room
        self._messages[room].append((message_id, username, text))

    def delete_message(self, message_id):
        if not isinstance(message_id, int) or message_id not in self._rooms_of:
            raise KeyError(message_id)
        room = self._rooms_of[message_id]
        for i, (mid, _, _) in enumerate(self._messages[room]):
            if mid == message_id:
                del self._messages[room][i]
                return
        raise ChatError(f"message {message_id} was already deleted")

    def get_members(self, room):
        self._require_room(room)
        return list(self._members[room])

    def get_messages(self, room):
        self._require_room(room)
        return [(user, text) for _, user, text in self._messages[room]]

    def get_message_ids(self, room):
        self._require_room(room)
        return [mid for mid, _, _ in self._messages[room]]

    def get_rooms(self):
        return list(self._members)

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
