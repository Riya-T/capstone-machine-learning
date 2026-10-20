from library import LibraryCatalog


def test_duplicate_active_loan_is_rejected_when_other_copies_remain():
    catalog = LibraryCatalog()
    catalog.add_book("978-013", "Python Cookbook", "Beazley", copies=3)
    assert catalog.checkout("978-013", "alice") is True
    assert catalog.checkout("978-013", "alice") is False
    assert catalog.books["978-013"].available_copies == 2


def test_distinct_borrowers_can_checkout_same_isbn():
    catalog = LibraryCatalog()
    catalog.add_book("978-013", "Python Cookbook", "Beazley", copies=2)
    assert catalog.checkout("978-013", "alice") is True
    assert catalog.checkout("978-013", "bob") is True
