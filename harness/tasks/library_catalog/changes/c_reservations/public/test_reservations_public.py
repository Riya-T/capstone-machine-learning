from library import LibraryCatalog


def test_waitlisted_borrower_receives_returned_book():
    catalog = LibraryCatalog()
    catalog.add_book("333", "Algorithms", "Sedgewick")
    assert catalog.checkout("333", "alice") is True
    assert catalog.checkout("333", "bob") is False
    assert catalog.return_book("333", "alice") is True
    assert catalog.checkout("333", "bob") is False
    assert catalog.books["333"].available_copies == 0


def test_reservations_are_fifo():
    catalog = LibraryCatalog()
    catalog.add_book("333", "Algorithms", "Sedgewick")
    catalog.checkout("333", "alice")
    catalog.checkout("333", "bob")
    catalog.checkout("333", "carol")
    catalog.return_book("333", "alice")
    assert catalog.loans["333"] == ["bob"]
    assert catalog.reservations["333"] == ["carol"]
