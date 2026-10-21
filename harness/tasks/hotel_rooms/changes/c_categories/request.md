Give every room in `hotel.py` a category, such as `"single"` or `"suite"`,
so guests can book a room of a category instead of a particular room.

- `add_room` takes a new keyword argument `category="standard"`. It must be
  a non-empty string, or `ValueError` is raised and no room is added. If
  both the room name and the category are invalid, either `ValueError` may
  come first.
- Add `Hotel.get_category(room) -> str`, which returns the room's category.
  It raises `KeyError` for a room that does not exist.
- `get_rooms` takes a new keyword argument `category=None`. With `None` it
  returns every room as before; with a category it returns only the rooms
  of that category, in the order they were added, or `[]` if no room has it.
- Add `Hotel.get_categories() -> list[str]`: every category that at least
  one room has, in the order in which the categories were first used.
- Add `Hotel.book_any(category, guest, first_night, last_night) -> int`. It
  books the first room of that category (in the order rooms were added)
  that is free on every night of the range, exactly as `book` would, and
  returns the new booking id. The errors, in order: `KeyError` if no room
  has that category; `ValueError` for an invalid guest; `ValueError` for
  invalid nights; `RoomUnavailable` if no room of the category is free for
  the whole range. In each case nothing changes.

All existing behavior must keep working.
