"""Login sessions: registered users and who is signed in right now.

Planted bug (initial version): signing in a user who is already signed in
is silently accepted instead of raising SessionError. The public checks
never sign in twice, so only the hidden initial tests catch it.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from sessions import SessionManager
    manager = SessionManager()
    manager.register("alice", "hunter2")
    manager.sign_in("alice", "hunter2")
"""


class SessionError(Exception):
    pass


class WrongPassword(SessionError):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


class SessionManager:
    def __init__(self):
        self._passwords = {}  # username -> password, in registration order
        self._signed_in = set()

    def register(self, username, password):
        check_text(username, "username")
        check_text(password, "password")
        if username in self._passwords:
            raise SessionError(f"user {username!r} is already registered")
        self._passwords[username] = password

    def sign_in(self, username, password):
        self._require(username)
        if password != self._passwords[username]:
            raise WrongPassword(f"wrong password for {username!r}")
        self._signed_in.add(username)

    def sign_out(self, username):
        self._require(username)
        if username not in self._signed_in:
            raise SessionError(f"user {username!r} is not signed in")
        self._signed_in.remove(username)

    def is_signed_in(self, username):
        self._require(username)
        return username in self._signed_in

    def get_users(self):
        return list(self._passwords)

    def get_signed_in(self):
        return [u for u in self._passwords if u in self._signed_in]

    def _require(self, username):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(username, str) or username not in self._passwords:
            raise KeyError(username)
