from library import LibraryCatalog


def test_checkout_at_capacity_queues_borrower_once():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho", copies=1)
    assert catalog.checkout("444", "alice") is True
    assert catalog.checkout("444", "bob") is False
    assert catalog.checkout("444", "bob") is False
    assert catalog.reservations["444"] == ["bob"]


def test_return_assigns_copy_to_first_reservation_in_queue():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho", copies=1)
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    catalog.checkout("444", "carol")
    assert catalog.return_book("444", "alice") is True
    assert catalog.loans["444"] == ["bob"]
    assert catalog.reservations["444"] == ["carol"]
    assert catalog.books["444"].available_copies == 0


def test_second_return_promotes_next_borrower_without_freeing_copy():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho", copies=1)
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    catalog.checkout("444", "carol")
    catalog.return_book("444", "alice")
    assert catalog.return_book("444", "bob") is True
    assert catalog.loans["444"] == ["carol"]
    assert catalog.reservations["444"] == []
    assert catalog.books["444"].available_copies == 0


def test_unknown_book_and_failed_return_do_not_create_or_remove_reservations():
    catalog = LibraryCatalog()
    assert catalog.checkout("missing", "alice") is False
    catalog.add_book("444", "Compilers", "Aho")
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    assert catalog.return_book("444", "unknown") is False
    assert catalog.reservations["444"] == ["bob"]
    assert catalog.books["444"].available_copies == 0


def test_reservation_queues_are_independent_per_isbn():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.add_book("555", "Operating Systems", "Tanenbaum")
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    catalog.checkout("555", "carol")
    catalog.checkout("555", "dave")
    assert catalog.reservations["444"] == ["bob"]
    assert catalog.reservations["555"] == ["dave"]


def test_borrower_with_reservation_cannot_return_a_copy_they_do_not_have():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    assert catalog.return_book("444", "bob") is False
    assert catalog.reservations["444"] == ["bob"]
    assert catalog.books["444"].available_copies == 0


def test_return_without_waiters_makes_copy_available():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.checkout("444", "alice")
    assert catalog.return_book("444", "alice") is True
    assert catalog.books["444"].available_copies == 1
    assert catalog.checkout("444", "bob") is True


def test_returned_copy_goes_to_waitlist_even_when_other_loans_remain():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho", copies=2)
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    catalog.checkout("444", "carol")
    assert catalog.return_book("444", "alice") is True
    assert catalog.loans["444"] == ["bob", "carol"]
    assert catalog.books["444"].available_copies == 0


def test_waitlist_for_one_isbn_does_not_block_checkout_of_another():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.add_book("555", "Operating Systems", "Tanenbaum")
    catalog.checkout("444", "alice")
    assert catalog.checkout("444", "bob") is False
    assert catalog.checkout("555", "bob") is True


def test_return_promotes_only_borrower_waiting_for_that_isbn():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.add_book("555", "Operating Systems", "Tanenbaum")
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    catalog.checkout("555", "carol")
    catalog.checkout("555", "dave")
    assert catalog.return_book("444", "alice") is True
    assert catalog.loans["444"] == ["bob"]
    assert catalog.loans["555"] == ["carol"]
    assert catalog.reservations["555"] == ["dave"]


def test_waitlisted_borrower_is_not_assigned_until_an_active_loan_returns():
    catalog = LibraryCatalog()
    catalog.add_book("444", "Compilers", "Aho")
    catalog.checkout("444", "alice")
    catalog.checkout("444", "bob")
    assert catalog.checkout("444", "bob") is False
    assert catalog.loans["444"] == ["alice"]
    assert catalog.reservations["444"] == ["bob"]
