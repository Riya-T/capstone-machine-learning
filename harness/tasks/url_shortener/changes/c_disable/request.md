Let links in `shortener.py` be switched off without deleting them, for
example while a campaign is paused.

- Add `class LinkDisabled(ShortenerError)` to `shortener.py`.
- Add `Shortener.disable(code)`, `Shortener.enable(code)` and
  `Shortener.is_enabled(code) -> bool`. All three raise `KeyError` for a code
  that does not exist. New links are enabled. Disabling a disabled link, or
  enabling an enabled one, does nothing.
- `visit` on a disabled link raises `LinkDisabled` and records no hit. In
  `visit`, `KeyError` is checked before `LinkDisabled`.
- Every other method treats a disabled link like any other: `get_target`,
  `get_hits` and `set_target` keep working, and the code still appears in
  `get_codes` and `get_most_visited`.
- Disabling and enabling change neither the link's target nor its hits.

All existing behavior must keep working.
