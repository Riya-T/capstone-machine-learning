import pytest

from library import LibraryCatalog


def test_adding_book_creates_expected_book_record():
    catalog = LibraryCatalog()
    catalog.add_book("978-1", "Clean Code", "Robert Martin", copies=2)
    book = catalog.books["978-1"]
    assert (book.isbn, book.title, book.author) == (
        "978-1",
        "Clean Code",
        "Robert Martin",
    )
    assert (book.total_copies, book.available_copies) == (2, 2)


def test_adding_existing_isbn_increases_both_copy_counts():
    catalog = LibraryCatalog()
    catalog.add_book("978-1", "Clean Code", "Robert Martin", copies=2)
    catalog.checkout("978-1", "alice")
    catalog.add_book("978-1", "Different title", "Different author", copies=3)
    book = catalog.books["978-1"]
    assert (book.total_copies, book.available_copies) == (5, 4)
    assert book.title == "Clean Code"
    assert book.author == "Robert Martin"


@pytest.mark.parametrize("copies", [0, -1, -5, 1.5, "2"])
def test_invalid_copy_count_is_rejected_without_changing_catalog(copies):
    catalog = LibraryCatalog()
    catalog.add_book("978-1", "Clean Code", "Robert Martin", copies=2)
    with pytest.raises(ValueError):
        catalog.add_book("978-1", "Replacement", "Other", copies=copies)
    book = catalog.books["978-1"]
    assert (book.total_copies, book.available_copies, book.title) == (
        2,
        2,
        "Clean Code",
    )


def test_checkout_reduces_available_count_and_records_loan():
    catalog = LibraryCatalog()
    catalog.add_book("978-2", "Design Patterns", "GoF")
    assert catalog.checkout("978-2", "alice") is True
    assert catalog.books["978-2"].available_copies == 0
    assert catalog.loans["978-2"] == ["alice"]


def test_unknown_or_unavailable_book_cannot_be_checked_out():
    catalog = LibraryCatalog()
    catalog.add_book("978-2", "Design Patterns", "GoF", copies=1)
    assert catalog.checkout("missing", "alice") is False
    assert catalog.checkout("978-2", "alice") is True
    assert catalog.checkout("978-2", "bob") is False
    assert catalog.books["978-2"].available_copies == 0


def test_return_requires_matching_isbn_and_borrower():
    catalog = LibraryCatalog()
    catalog.add_book("978-2", "Design Patterns", "GoF")
    catalog.checkout("978-2", "alice")
    assert catalog.return_book("missing", "alice") is False
    assert catalog.return_book("978-2", "bob") is False
    assert catalog.books["978-2"].available_copies == 0


def test_successful_return_restores_one_copy():
    catalog = LibraryCatalog()
    catalog.add_book("978-2", "Design Patterns", "GoF", copies=2)
    catalog.checkout("978-2", "alice")
    assert catalog.return_book("978-2", "alice") is True
    assert catalog.books["978-2"].available_copies == 2
    assert catalog.return_book("978-2", "alice") is False
    assert catalog.books["978-2"].available_copies == 2


def test_baseline_allows_same_borrower_to_borrow_multiple_copies():
    catalog = LibraryCatalog()
    catalog.add_book("978-2", "Design Patterns", "GoF", copies=2)
    assert catalog.checkout("978-2", "alice") is True
    assert catalog.checkout("978-2", "alice") is True
    assert catalog.books["978-2"].available_copies == 0


def test_catalog_instances_do_not_share_books_or_loans():
    first = LibraryCatalog()
    second = LibraryCatalog()
    first.add_book("978-3", "Algorithms", "Sedgewick")
    first.checkout("978-3", "alice")
    assert second.books == {}
    assert second.loans == {}


def test_new_book_defaults_to_one_copy():
    catalog = LibraryCatalog()
    catalog.add_book("978-4", "The Pragmatic Programmer", "Hunt")
    book = catalog.books["978-4"]
    assert book.total_copies == 1
    assert book.available_copies == 1


def test_copy_counts_are_independent_between_isbns():
    catalog = LibraryCatalog()
    catalog.add_book("978-4", "The Pragmatic Programmer", "Hunt", copies=2)
    catalog.add_book("978-5", "Grokking Algorithms", "Bhargava", copies=3)
    catalog.checkout("978-4", "alice")
    assert catalog.books["978-4"].available_copies == 1
    assert catalog.books["978-5"].available_copies == 3


def test_failed_return_does_not_remove_another_borrowers_loan():
    catalog = LibraryCatalog()
    catalog.add_book("978-5", "Grokking Algorithms", "Bhargava", copies=2)
    catalog.checkout("978-5", "alice")
    assert catalog.return_book("978-5", "bob") is False
    assert catalog.loans["978-5"] == ["alice"]
    assert catalog.books["978-5"].available_copies == 1


def test_returning_one_of_two_copies_releases_only_one_copy():
    catalog = LibraryCatalog()
    catalog.add_book("978-5", "Grokking Algorithms", "Bhargava", copies=3)
    catalog.checkout("978-5", "alice")
    catalog.checkout("978-5", "alice")
    assert catalog.return_book("978-5", "alice") is True
    assert catalog.books["978-5"].available_copies == 2
    assert catalog.loans["978-5"] == ["alice"]


def test_invalid_first_addition_does_not_create_book():
    catalog = LibraryCatalog()
    with pytest.raises(ValueError):
        catalog.add_book("978-6", "Invalid", "Author", copies=0)
    assert "978-6" not in catalog.books


def test_checkout_and_return_preserve_total_owned_copies():
    catalog = LibraryCatalog()
    catalog.add_book("978-7", "The Hobbit", "Tolkien", copies=3)
    catalog.checkout("978-7", "alice")
    catalog.return_book("978-7", "alice")
    book = catalog.books["978-7"]
    assert (book.total_copies, book.available_copies) == (3, 3)


def test_adding_copy_after_inventory_is_checked_out_increases_availability():
    catalog = LibraryCatalog()
    catalog.add_book("978-8", "Dune", "Herbert")
    catalog.checkout("978-8", "alice")
    catalog.add_book("978-8", "Dune", "Herbert")
    book = catalog.books["978-8"]
    assert (book.total_copies, book.available_copies) == (2, 1)


def test_returning_one_isbn_does_not_change_other_book_inventory():
    catalog = LibraryCatalog()
    catalog.add_book("978-8", "Dune", "Herbert")
    catalog.add_book("978-9", "Foundation", "Asimov")
    catalog.checkout("978-8", "alice")
    catalog.checkout("978-9", "bob")
    catalog.return_book("978-8", "alice")
    assert catalog.books["978-8"].available_copies == 1
    assert catalog.books["978-9"].available_copies == 0


def test_returning_borrower_does_not_change_other_active_loans():
    catalog = LibraryCatalog()
    catalog.add_book("978-8", "Dune", "Herbert", copies=2)
    catalog.checkout("978-8", "alice")
    catalog.checkout("978-8", "bob")
    catalog.return_book("978-8", "alice")
    assert catalog.loans["978-8"] == ["bob"]
