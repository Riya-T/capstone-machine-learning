"""Login sessions with account lockout and a limit on concurrent sign-ins.

Correct solution for login_sessions after c_lockout and c_capacity.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from sessions import SessionManager
    manager = SessionManager(max_signed_in=2)
    manager.register("alice", "hunter2")
    manager.sign_in("alice", "hunter2")
"""

MAX_FAILED_ATTEMPTS = 3


class SessionError(Exception):
    pass


class WrongPassword(SessionError):
    pass


class AccountLocked(SessionError):
    pass


class SessionLimitReached(SessionError):
    pass


def check_text(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_limit(limit):
    if limit is None:
        return
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise ValueError(f"max_signed_in must be None or an int >= 0, got {limit!r}")


class SessionManager:
    def __init__(self, max_signed_in=None):
        check_limit(max_signed_in)
        self._max_signed_in = max_signed_in
        self._passwords = {}  # username -> password, in registration order
        self._signed_in = set()
        self._failures = {}  # username -> wrong passwords in a row
        self._locked = set()

    def register(self, username, password):
        check_text(username, "username")
        check_text(password, "password")
        if username in self._passwords:
            raise SessionError(f"user {username!r} is already registered")
        self._passwords[username] = password
        self._failures[username] = 0

    def sign_in(self, username, password):
        self._require(username)
        if username in self._signed_in:
            raise SessionError(f"user {username!r} is already signed in")
        if username in self._locked:
            raise AccountLocked(f"user {username!r} is locked")
        if password != self._passwords[username]:
            self._record_failure(username)
            raise WrongPassword(f"wrong password for {username!r}")
        if self._max_signed_in is not None and len(self._signed_in) >= self._max_signed_in:
            raise SessionLimitReached(f"already {len(self._signed_in)} users signed in")
        self._failures[username] = 0
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

    def unlock(self, username):
        self._require(username)
        self._locked.discard(username)
        self._failures[username] = 0

    def is_locked(self, username):
        self._require(username)
        return username in self._locked

    def get_failed_attempts(self, username):
        self._require(username)
        return self._failures[username]

    def get_max_signed_in(self):
        return self._max_signed_in

    def set_max_signed_in(self, limit):
        check_limit(limit)
        if limit is not None and len(self._signed_in) > limit:
            raise SessionError(f"{len(self._signed_in)} users are signed in, more than {limit}")
        self._max_signed_in = limit

    def _record_failure(self, username):
        self._failures[username] += 1
        if self._failures[username] >= MAX_FAILED_ATTEMPTS:
            self._locked.add(username)

    def _require(self, username):
        # Non-str names are never stored, so they count as unknown too.
        if not isinstance(username, str) or username not in self._passwords:
            raise KeyError(username)
