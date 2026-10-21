Sort movies into genres in `bookings.py`.

- `add_movie` takes a new keyword argument `genre="general"`. It must be a
  non-empty string; anything else raises `ValueError` and no movie is added.
  An invalid title is reported before an invalid genre, and an invalid genre
  before a title that was already added.
- Add `BoxOffice.get_genre(title) -> str`, which returns the movie's genre.
  It raises `KeyError` for a title that was not added.
- Add `BoxOffice.get_genres() -> list[str]`: every genre that at least one
  movie has, in the order the genre was first used.
- Add `BoxOffice.get_movies_in_genre(genre) -> list[str]`: the titles of the
  movies in that genre, in the order they were added. A genre no movie has
  gives an empty list.
- Add `BoxOffice.get_genre_seats_booked(genre) -> int`: the number of seats
  currently booked over all showings of all movies in that genre, counting
  only bookings that still stand. A genre no movie has gives 0.

All existing behavior must keep working.
