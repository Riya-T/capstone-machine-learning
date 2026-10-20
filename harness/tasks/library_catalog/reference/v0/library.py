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

    def add_book(self, isbn: str, title: str, author: str, copies: int = 1):
        if not isinstance(copies, int) or copies <= 0:
            raise ValueError("Copies must be a positive integer")
        if isbn in self.books:
            book = self.books[isbn]
            book.total_copies += copies
            book.available_copies += copies
        else:
            self.books[isbn] = Book(isbn, title, author, copies)

    def checkout(self, isbn: str, borrower_id: str) -> bool:
        book = self.books.get(isbn)
        if book is None or book.available_copies <= 0:
            return False
        book.available_copies -= 1
        self.loans.setdefault(isbn, []).append(borrower_id)
        return True

    def return_book(self, isbn: str, borrower_id: str) -> bool:
        borrowers = self.loans.get(isbn, [])
        if borrower_id not in borrowers:
            return False
        borrowers.remove(borrower_id)
        self.books[isbn].available_copies += 1
        return True
