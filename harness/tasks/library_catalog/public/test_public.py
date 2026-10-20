from library import LibraryCatalog


def test_add_book_and_checkout_available_copy():
    catalog = LibraryCatalog()
    catalog.add_book("123-456", "Python Programming", "Guido", copies=2)
    assert catalog.checkout("123-456", "user_1") is True
    assert catalog.books["123-456"].available_copies == 1


def test_unknown_book_cannot_be_checked_out():
    catalog = LibraryCatalog()
    assert catalog.checkout("missing", "user_1") is False


def test_return_succeeds_for_active_loan():
    catalog = LibraryCatalog()
    catalog.add_book("123-456", "Python Programming", "Guido")
    assert catalog.checkout("123-456", "user_1") is True
    assert catalog.return_book("123-456", "user_1") is True


def test_adding_copies_increases_inventory():
    catalog = LibraryCatalog()
    catalog.add_book("123-456", "Python Programming", "Guido", copies=2)
    catalog.add_book("123-456", "Python Programming", "Guido", copies=3)
    assert catalog.books["123-456"].total_copies == 5
