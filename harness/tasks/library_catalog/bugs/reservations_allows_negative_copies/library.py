class Book:
    def __init__(self, isbn: str, title: str, author: str, total_copies: int = 1):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.total_copies = total_copies
        self.available_copies = total_copies


class LibraryCatalog:
    def __init__(self):
        self.books = {}
        self.loans = {}
        self.reservations = {}

    def add_book(self, isbn: str, title: str, author: str, copies: int = 1):
        if isbn in self.books:
            self.books[isbn].total_copies += copies
            self.books[isbn].available_copies += copies
        else:
            self.books[isbn] = Book(isbn, title, author, copies)

    def checkout(self, isbn: str, borrower_id: str) -> bool:
        book = self.books.get(isbn)
        if book is None:
            return False
        active = self.loans.get(isbn, [])
        waiting = self.reservations.get(isbn, [])
        if borrower_id in active or borrower_id in waiting:
            return False
        if book.available_copies > 0:
            book.available_copies -= 1
            active.append(borrower_id)
            self.loans[isbn] = active
            return True
        waiting.append(borrower_id)
        self.reservations[isbn] = waiting
        return False

    def return_book(self, isbn: str, borrower_id: str) -> bool:
        active = self.loans.get(isbn, [])
        if borrower_id not in active:
            return False
        active.remove(borrower_id)
        waiting = self.reservations.get(isbn, [])
        if waiting:
            active.append(waiting.pop(0))
        else:
            self.books[isbn].available_copies += 1
        return True
