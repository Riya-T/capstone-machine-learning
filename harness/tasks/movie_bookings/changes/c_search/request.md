Add ways to look up showings and bookings in `bookings.py`.

- Add `BoxOffice.find_showings(title=None, earliest=None, latest=None) ->
  list[str]`: the ids of every showing that passes all the filters given,
  earliest start first, with equal starts in the order the showings were
  added. With `title`, only showings of that movie count. With `earliest`,
  only showings starting at that minute or later count; with `latest`, only
  showings starting at that minute or earlier. With no filters, every
  showing is returned.
- `find_showings` raises `KeyError` for a title that was not added, then
  `ValueError` if `earliest` or `latest` is given but is not an `int` that is
  0 or more (a `bool` does not count), then `ValueError` if `earliest` is
  greater than `latest`.
- Add `BoxOffice.find_customer_bookings(customer) -> list[tuple[str, int]]`:
  the customer's bookings over every showing as `(showing_id, seats)`
  tuples, in the order they were made. A customer without bookings gives an
  empty list. A customer that is not a non-empty string raises `ValueError`.

All existing behavior must keep working.
