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
        if isbn in self.books:
            self.books[isbn].total_copies += copies
            self.books[isbn].available_copies += copies
        else:
            self.books[isbn] = Book(isbn, title, author, copies)

    def checkout(self, isbn: str, borrower_id: str) -> bool:
        book = self.books.get(isbn)
        if book and book.available_copies > 0:
            book.available_copies -= 1
            self.loans.setdefault(isbn, []).append(borrower_id)
            return True
        return False

    def return_book(self, isbn: str, borrower_id: str) -> bool:
        if isbn in self.loans and borrower_id in self.loans[isbn]:
            self.loans[isbn].remove(borrower_id)
            # BUG: Inflates available copies by 2 on return instead of 1
            self.books[isbn].available_copies += 2
            return True
        return False