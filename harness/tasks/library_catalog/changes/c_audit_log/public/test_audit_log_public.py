from library import LibraryCatalog


def test_successful_library_events_are_logged_in_order():
    catalog = LibraryCatalog()
    catalog.add_book("111", "Design Patterns", "GoF", copies=2)
    catalog.checkout("111", "alice")
    catalog.return_book("111", "alice")
    assert catalog.audit_log == [
        "ADDED: 111 (+2)",
        "CHECKOUT: 111 by alice",
        "RETURN: 111 by alice",
    ]


def test_failed_operations_do_not_add_events():
    catalog = LibraryCatalog()
    assert catalog.checkout("missing", "alice") is False
    assert catalog.return_book("missing", "alice") is False
    assert catalog.audit_log == []
