from library import LibraryCatalog


def test_multiple_distinct_borrowers_are_allowed_until_inventory_is_empty():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho", copies=2)
    assert catalog.checkout("978-032", "alice") is True
    assert catalog.checkout("978-032", "bob") is True
    assert catalog.checkout("978-032", "carol") is False
    assert catalog.books["978-032"].available_copies == 0


def test_same_borrower_cannot_checkout_a_second_copy():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho", copies=3)
    assert catalog.checkout("978-032", "alice") is True
    assert catalog.checkout("978-032", "alice") is False
    assert catalog.books["978-032"].available_copies == 2
    assert catalog.loans["978-032"] == ["alice"]


def test_return_clears_duplicate_loan_restriction():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho", copies=2)
    assert catalog.checkout("978-032", "alice") is True
    assert catalog.checkout("978-032", "alice") is False
    assert catalog.return_book("978-032", "alice") is True
    assert catalog.checkout("978-032", "alice") is True


def test_an_unavailable_book_does_not_create_an_active_loan():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho")
    catalog.checkout("978-032", "alice")
    assert catalog.checkout("978-032", "bob") is False
    assert catalog.return_book("978-032", "bob") is False


def test_same_borrower_may_hold_loans_for_different_isbns():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho")
    catalog.add_book("978-013", "Python Cookbook", "Beazley")
    assert catalog.checkout("978-032", "alice") is True
    assert catalog.checkout("978-013", "alice") is True


def test_duplicate_rejection_does_not_affect_another_borrowers_loan():
    catalog = LibraryCatalog()
    catalog.add_book("978-032", "Fluent Python", "Ramalho", copies=3)
    assert catalog.checkout("978-032", "alice") is True
    assert catalog.checkout("978-032", "bob") is True
    assert catalog.checkout("978-032", "alice") is False
    assert catalog.return_book("978-032", "bob") is True
    assert catalog.books["978-032"].available_copies == 2
