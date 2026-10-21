"""Wiki with page versions, an adjustable number of kept revisions, and
search over pages and contributions.

Planted bug (after c_search, c_version_check and c_retention): the limits
work, but find_pages matches any kept revision, not only the current text.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from wiki import Wiki
    wiki = Wiki(keep=3)
    wiki.create_page("home", "ann", "Welcome", keep=10)
    wiki.edit_page("home", "bob", "Welcome!", expected_version=1)
    wiki.find_pages("Welcome")
"""


class WikiError(Exception):
    pass


class VersionConflict(WikiError):
    pass


def check_name(value, what):
    if not isinstance(value, str) or not value:
        raise ValueError(f"{what} must be a non-empty str, got {value!r}")


def check_text(text):
    if not isinstance(text, str):
        raise ValueError(f"text must be a str, got {text!r}")


def check_keep(keep):
    if isinstance(keep, bool) or not isinstance(keep, int) or keep < 1:
        raise ValueError(f"keep must be an int >= 1, got {keep!r}")


class _Page:
    def __init__(self, keep):
        self.keep = keep
        self.version = 0  # becomes 1 with the first revision
        self.writers = []  # author of every revision ever made, oldest first
        self.texts = {}  # revision number -> text, for kept revisions only

    def add(self, author, text):
        self.writers.append(author)
        number = len(self.writers)
        self.texts[number] = text
        self.texts.pop(number - self.keep, None)
        self.version += 1
        return number

    def latest(self):
        return self.texts[len(self.writers)]


class Wiki:
    def __init__(self, keep=5):
        check_keep(keep)
        self._keep = keep
        self._pages = {}  # page name -> _Page, in creation order
        self._log = []  # (author, page, revision number) of every revision, in order

    def create_page(self, page, author, text, keep=None):
        check_name(page, "page")
        check_name(author, "author")
        check_text(text)
        if keep is not None:
            check_keep(keep)
        if page in self._pages:
            raise WikiError(f"page {page!r} already exists")
        record = _Page(self._keep if keep is None else keep)
        self._pages[page] = record
        self._write(page, record, author, text)

    def edit_page(self, page, author, text, expected_version=None):
        record = self._require(page)
        check_name(author, "author")
        check_text(text)
        if expected_version is not None and expected_version != record.version:
            raise VersionConflict(
                f"page {page!r} is at version {record.version}, not {expected_version}"
            )
        if text == record.latest():
            raise WikiError(f"page {page!r} already has this text")
        self._write(page, record, author, text)

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

    def get_version(self, page):
        return self._require(page).version

    def get_keep(self, page):
        return self._require(page).keep

    def find_pages(self, phrase):
        check_name(phrase, "phrase")
        return [
            name
            for name, record in self._pages.items()
            if any(phrase in text for text in record.texts.values())
        ]

    def get_contributions(self, author):
        return [(page, number) for who, page, number in self._log if who == author]

    def _write(self, page, record, author, text):
        number = record.add(author, text)
        self._log.append((author, page, number))

    def _require(self, page):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(page, str) or page not in self._pages:
            raise KeyError(page)
        return self._pages[page]
