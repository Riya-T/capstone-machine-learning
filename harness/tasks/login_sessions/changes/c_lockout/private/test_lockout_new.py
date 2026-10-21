"""Hidden tests for the c_lockout change (account lockout). Never shown to
the writer or the editor.

Usage (with sessions.py importable, e.g. in the sandbox):
    python -m pytest changes/c_lockout/private/test_lockout_new.py
"""

import pytest
from sessions import AccountLocked, SessionError, SessionManager, WrongPassword


@pytest.fixture
def manager():
    man = SessionManager()
    man.register("alice", "hunter2")
    man.register("bob", "secret")
    return man


def state(man):
    return (
        man.get_users(),
        man.get_signed_in(),
        [(man.is_locked(u), man.get_failed_attempts(u)) for u in man.get_users()],
    )


def fail(man, username, times):
    for _ in range(times):
        with pytest.raises(WrongPassword):
            man.sign_in(username, "wrong")


def test_new_users_start_unlocked_with_no_failures(manager):
    assert not manager.is_locked("alice")
    assert manager.get_failed_attempts("alice") == 0


def test_failed_attempts_count_up_to_the_lock(manager):
    fail(manager, "alice", 1)
    assert manager.get_failed_attempts("alice") == 1
    assert not manager.is_locked("alice")
    fail(manager, "alice", 1)
    assert manager.get_failed_attempts("alice") == 2
    assert not manager.is_locked("alice")
    manager.sign_in("alice", "hunter2")  # two failures are still fine
    assert manager.is_signed_in("alice")


def test_the_third_failure_locks_and_the_right_password_is_then_refused(manager):
    fail(manager, "alice", 3)
    assert manager.is_locked("alice")
    assert manager.get_failed_attempts("alice") == 3
    before = state(manager)
    with pytest.raises(AccountLocked):
        manager.sign_in("alice", "hunter2")
    with pytest.raises(AccountLocked):
        manager.sign_in("alice", "wrong")
    assert state(manager) == before  # a locked refusal is not a failed attempt


def test_a_success_resets_the_count(manager):
    fail(manager, "alice", 2)
    manager.sign_in("alice", "hunter2")
    assert manager.get_failed_attempts("alice") == 0
    manager.sign_out("alice")
    fail(manager, "alice", 2)
    assert manager.get_failed_attempts("alice") == 2
    assert not manager.is_locked("alice")


def test_failures_are_counted_per_user(manager):
    fail(manager, "alice", 3)
    fail(manager, "bob", 1)
    assert manager.is_locked("alice")
    assert not manager.is_locked("bob")
    assert manager.get_failed_attempts("bob") == 1
    manager.sign_in("bob", "secret")
    assert manager.get_signed_in() == ["bob"]


def test_unlock_resets_a_locked_account(manager):
    fail(manager, "alice", 3)
    manager.unlock("alice")
    assert not manager.is_locked("alice")
    assert manager.get_failed_attempts("alice") == 0
    fail(manager, "alice", 2)
    assert not manager.is_locked("alice")
    manager.sign_in("alice", "hunter2")
    assert manager.is_signed_in("alice")


def test_unlock_on_an_unlocked_account_only_resets_the_count(manager):
    fail(manager, "alice", 2)
    manager.unlock("alice")
    assert manager.get_failed_attempts("alice") == 0
    assert not manager.is_locked("alice")
    manager.unlock("bob")
    assert state(manager) == (["alice", "bob"], [], [(False, 0), (False, 0)])


@pytest.mark.parametrize("method", ["unlock", "is_locked", "get_failed_attempts"])
@pytest.mark.parametrize("username", ["carol", None, 3])
def test_lock_methods_reject_unregistered_users(manager, method, username):
    with pytest.raises(KeyError):
        getattr(manager, method)(username)


def test_already_signed_in_is_reported_before_locked(manager):
    manager.sign_in("bob", "secret")
    fail(manager, "alice", 3)
    # bob is signed in; alice is locked. Signing bob in again is the
    # already-signed-in error, not a lock or a password problem.
    try:
        manager.sign_in("bob", "wrong")
    except (WrongPassword, AccountLocked):
        pytest.fail("already signed in should come first")
    except SessionError:
        pass
    assert manager.get_failed_attempts("bob") == 0


def test_locked_is_reported_before_the_password_check(manager):
    fail(manager, "alice", 3)
    with pytest.raises(AccountLocked):
        manager.sign_in("alice", "wrong")
    assert manager.get_failed_attempts("alice") == 3


def test_unknown_user_is_reported_before_locked(manager):
    with pytest.raises(KeyError):
        manager.sign_in("carol", "wrong")


def test_locking_does_not_touch_signed_in_users(manager):
    manager.sign_in("bob", "secret")
    fail(manager, "alice", 3)
    assert manager.get_signed_in() == ["bob"]
    manager.unlock("alice")
    assert manager.get_signed_in() == ["bob"]
    with pytest.raises(SessionError):
        manager.sign_out("alice")


def test_account_locked_is_a_session_error_but_not_wrong_password():
    assert issubclass(AccountLocked, SessionError)
    assert not issubclass(AccountLocked, WrongPassword)
