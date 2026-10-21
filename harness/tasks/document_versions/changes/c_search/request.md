Readers of the wiki in `wiki.py` want to find pages by their content, and
editors want to see what one person has written across the whole wiki.

- Add `Wiki.find_pages(phrase) -> list[str]`. It returns the pages whose
  current text contains `phrase` exactly (case matters), in the order the
  pages were created. Older revisions are not searched. The phrase must be
  a non-empty string, or `ValueError` is raised. A phrase that no page
  contains gives `[]`.
- Add `Wiki.get_contributions(author) -> list[tuple[str, int]]`. It returns
  a `(page, revision number)` pair for every revision the author wrote, on
  any page, in the order the revisions were written. Revisions that are no
  longer kept are included. An author who has written nothing gives `[]`;
  it is not an error.

All existing behavior must keep working.
