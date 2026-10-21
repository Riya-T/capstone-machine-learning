"""Wiki with page versions and an adjustable number of kept revisions.

Planted bug (after c_version_check and c_retention): the limits work, but
an edit that leaves the text unchanged is accepted again.
Never shown to the writer or the editor; validate-tasks checks that the
tests catch it.

Usage:
    from wiki import Wiki
    wiki = Wiki(keep=3)
    wiki.create_page("home", "ann", "Welcome", keep=10)
    wiki.edit_page("home", "bob", "Welcome!", expected_version=1)
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


def check_number(number):
    if not isinstance(number, int) or number < 1:
        raise ValueError(f"revision number must be an int >= 1, got {number!r}")


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

    def latest(self):
        return self.texts[len(self.writers)]

    def check_version(self, page, expected_version):
        if expected_version is not None and expected_version != self.version:
            raise VersionConflict(
                f"page {page!r} is at version {self.version}, not {expected_version}"
            )


class Wiki:
    def __init__(self, keep=5):
        check_keep(keep)
        self._keep = keep
        self._pages = {}  # page name -> _Page, in creation order

    def create_page(self, page, author, text, keep=None):
        check_name(page, "page")
        check_name(author, "author")
        check_text(text)
        if keep is not None:
            check_keep(keep)
        if page in self._pages:
            raise WikiError(f"page {page!r} already exists")
        record = _Page(self._keep if keep is None else keep)
        record.add(author, text)
        self._pages[page] = record

    def edit_page(self, page, author, text, expected_version=None):
        record = self._require(page)
        check_name(author, "author")
        check_text(text)
        record.check_version(page, expected_version)
        record.add(author, text)

    def get_text(self, page):
        return self._require(page).latest()

    def get_revision(self, page, number):
        record = self._require(page)
        check_number(number)
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

    def _require(self, page):
        # Non-str names are never stored, so they count as missing too.
        if not isinstance(page, str) or page not in self._pages:
            raise KeyError(page)
        return self._pages[page]
