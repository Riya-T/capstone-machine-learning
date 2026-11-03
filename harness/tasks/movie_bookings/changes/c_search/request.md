Add ways to look up showings and bookings in `bookings.py`.

- Add `BoxOffice.find_showings(title=None, earliest=None, latest=None) ->
  list[str]`: the ids of every showing that passes all the filters given,
  earliest start first, with equal starts in the order the showings were
  added. With `title`, only showings of that movie count. With `earliest`,
  only showings starting at that minute or later count; with `latest`, only
  showings starting at that minute or earlier. With no filters, every
  showing is returned.
- `find_showings` raises `KeyError` for a title that was not added, and
  `ValueError` if `earliest` or `latest` is given but is not an `int` that is
  0 or more, or if `earliest` is greater than `latest`. When a call has
  several of these problems, which error it raises is unspecified.
- Add `BoxOffice.find_customer_bookings(customer) -> list[tuple[str, int]]`:
  the customer's bookings over every showing as `(showing_id, seats)`
  tuples, in the order they were made. For example, if `ann` books 1 seat
  of showing `"s2"`, then 4 seats of `"s1"`, then 2 more seats of `"s2"`,
  `find_customer_bookings("ann")` is `[("s2", 1), ("s1", 4), ("s2", 2)]`,
  whatever order the showings were added in or start at. A customer without
  bookings gives an empty list. An empty string or `None` as the customer
  raises `ValueError`.

All existing behavior must keep working.
