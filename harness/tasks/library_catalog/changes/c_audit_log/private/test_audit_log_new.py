import pytest

from library import LibraryCatalog


def test_addition_of_extra_copies_is_logged():
    catalog = LibraryCatalog()
    catalog.add_book("222", "Refactoring", "Fowler")
    catalog.add_book("222", "Refactoring", "Fowler", copies=3)
    assert catalog.audit_log == [
        "ADDED: 222 (+1)",
        "ADDED: 222 (+3)",
    ]


def test_invalid_add_does_not_log_or_change_existing_events():
    catalog = LibraryCatalog()
    catalog.add_book("222", "Refactoring", "Fowler")
    with pytest.raises(ValueError):
        catalog.add_book("222", "Refactoring", "Fowler", copies=0)
    assert catalog.audit_log == ["ADDED: 222 (+1)"]


def test_unavailable_checkout_and_unmatched_return_are_not_logged():
    catalog = LibraryCatalog()
    catalog.add_book("222", "Refactoring", "Fowler")
    assert catalog.checkout("222", "alice") is True
    assert catalog.checkout("222", "bob") is False
    assert catalog.return_book("222", "bob") is False
    assert catalog.audit_log == [
        "ADDED: 222 (+1)",
        "CHECKOUT: 222 by alice",
    ]


def test_events_remain_ordered_across_multiple_loans():
    catalog = LibraryCatalog()
    catalog.add_book("222", "Refactoring", "Fowler", copies=2)
    catalog.checkout("222", "alice")
    catalog.checkout("222", "bob")
    catalog.return_book("222", "alice")
    catalog.return_book("222", "bob")
    assert catalog.audit_log == [
        "ADDED: 222 (+2)",
        "CHECKOUT: 222 by alice",
        "CHECKOUT: 222 by bob",
        "RETURN: 222 by alice",
        "RETURN: 222 by bob",
    ]


def test_audit_log_starts_empty():
    assert LibraryCatalog().audit_log == []


def test_failed_operations_do_not_suppress_later_successful_events():
    catalog = LibraryCatalog()
    assert catalog.checkout("missing", "alice") is False
    catalog.add_book("222", "Refactoring", "Fowler")
    assert catalog.checkout("222", "alice") is True
    assert catalog.audit_log == [
        "ADDED: 222 (+1)",
        "CHECKOUT: 222 by alice",
    ]
