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
        self.audit_log = []

    def add_book(self, isbn: str, title: str, author: str, copies: int = 1):
        if isbn in self.books:
            self.books[isbn].total_copies += copies
            self.books[isbn].available_copies += copies
        else:
            self.books[isbn] = Book(isbn, title, author, copies)
        self.audit_log.append(f"ADDED: {isbn} (+{copies})")

    def checkout(self, isbn: str, borrower_id: str) -> bool:
        book = self.books.get(isbn)
        if book is None or borrower_id in self.loans.get(isbn, []):
            return False
        if book.available_copies <= 0:
            return False
        book.available_copies -= 1
        self.loans.setdefault(isbn, []).append(borrower_id)
        self.audit_log.append(f"CHECKOUT: {isbn} by {borrower_id}")
        return True

    def return_book(self, isbn: str, borrower_id: str) -> bool:
        active = self.loans.get(isbn, [])
        if borrower_id not in active:
            return False
        active.remove(borrower_id)
        self.books[isbn].available_copies += 1
        self.audit_log.append(f"RETURN: {isbn} by {borrower_id}")
        return True
