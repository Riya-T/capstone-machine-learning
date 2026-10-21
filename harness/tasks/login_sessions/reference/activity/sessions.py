"""Login sessions with an activity log of sign-ins, sign-outs and failures.

Correct solution for login_sessions after c_activity.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from sessions import SessionManager
    manager = SessionManager()
    manager.register("alice", "hunter2")
    manager.sign_in("alice", "hunter2")
    manager.get_activity("alice")  # ["sign_in"]
"""

EVENT_KINDS = ("sign_in", "sign_out", "failed_sign_in")


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
        self._activity = {}  # username -> list of event names, oldest first

    def register(self, username, password):
        check_text(username, "username")
        check_text(password, "password")
        if username in self._passwords:
            raise SessionError(f"user {username!r} is already registered")
        self._passwords[username] = password
        self._activity[username] = []

    def sign_in(self, username, password):
        self._require(username)
        if username in self._signed_in:
            raise SessionError(f"user {username!r} is already signed in")
        if password != self._passwords[username]:
            self._activity[username].append("failed_sign_in")
            raise WrongPassword(f"wrong password for {username!r}")
        self._signed_in.add(username)
        self._activity[username].append("sign_in")

    def sign_out(self, username):
        self._require(username)
        if username not in self._signed_in:
            raise SessionError(f"user {username!r} is not signed in")
        self._signed_in.remove(username)
        self._activity[username].append("sign_out")

    def is_signed_in(self, username):
        self._require(username)
        return username in self._signed_in

    def get_users(self):
        return list(self._passwords)

    def get_signed_in(self):
        return [u for u in self._passwords if u in self._signed_in]

    def get_activity(self, username, kind=None):
        self._require(username)
        if kind is not None and kind not in EVENT_KINDS:
            raise ValueError(f"unknown event kind {kind!r}")
        events = self._activity[username]
        if kind is None:
            return list(events)
        return [e for e in events if e == kind]

    def get_users_by_activity(self):
        # sorted is stable, so equal counts keep registration order.
        return sorted(self._passwords, key=lambda u: -len(self._activity[u]))

    def _require(self, username):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(username, str) or username not in self._passwords:
            raise KeyError(username)
