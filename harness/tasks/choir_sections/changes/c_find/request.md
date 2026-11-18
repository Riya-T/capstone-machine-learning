Let `choir.py` tell where a singer stands, for example to print a seating
card for each singer.

- Add `Choir.get_section_of(singer) -> str`: the name of the section the
  singer is in.
- Add `Choir.get_position(singer) -> int`: the singer's place in their
  section, counting from 1 for the first singer `get_singers` lists for
  that section.
- Both raise `KeyError` for a name that is not in the choir, for example
  a singer who has been removed.
- Both always reflect the calls made before: after `move_singer`,
  `move_all` or `merge_sections` they give the singer's new section and
  place, and when a singer ahead of them leaves the section, the place of
  everyone behind goes down by one.
- Neither method changes the choir.

All existing behavior must keep working.
