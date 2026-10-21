"""Wiki: pages whose every write becomes a numbered revision.

Planted bug (initial version): creating a page that already exists
silently replaces it instead of raising WikiError.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from wiki import Wiki
    wiki = Wiki()
    wiki.create_page("home", "ann", "Welcome")
    wiki.edit_page("home", "bob", "Welcome!")
"""

KEEP = 5  # revisions kept per page


class WikiError(Exception):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_text(text):
    if not isinstance(text, str):
        raise ValueError(f"text must be a str, got {text!r}")


class _Page:
    def __init__(self):
        self.writers = []  # author of every revision ever made, oldest first
        self.texts = {}  # revision number -> text, for kept revisions only

    def add(self, author, text):
        self.writers.append(author)
        number = len(self.writers)
        self.texts[number] = text
        self.texts.pop(number - KEEP, None)

    def latest(self):
        return self.texts[len(self.writers)]


class Wiki:
    def __init__(self):
        self._pages = {}  # page name -> _Page, in creation order

    def create_page(self, page, author, text):
        check_name(page, "page")
        check_name(author, "author")
        check_text(text)
        record = _Page()
        record.add(author, text)
        self._pages[page] = record

    def edit_page(self, page, author, text):
        record = self._require(page)
        check_name(author, "author")
        check_text(text)
        if text == record.latest():
            raise WikiError(f"page {page!r} already has this text")
        record.add(author, text)

    def get_text(self, page):
        return self._require(page).latest()

    def get_revision(self, page, number):
        record = self._require(page)
        if not isinstance(number, int) or number < 1:
            raise ValueError(f"revision number must be an int >= 1, got {number!r}")
        if number not in record.texts:
            raise IndexError(f"revision {number} of {page!r} is not available")
        return record.texts[number]

    def get_revision_count(self, page):
        return len(self._require(page).writers)

    def get_authors(self, page):
        return list(dict.fromkeys(self._require(page).writers))

    def get_pages(self):
        return list(self._pages)

    def _require(self, page):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(page, str) or page not in self._pages:
            raise KeyError(page)
        return self._pages[page]
