Group the symbols in `portfolio.py` into sectors, so holdings can be looked
at one sector at a time.

- Add `Portfolio.set_sector(symbol, sector)`. The symbol follows the usual
  symbol rules (`ValueError` when invalid). The sector must be a non-empty
  string, or `ValueError` is raised; the symbol is checked first. A sector
  can be set for any symbol, whether or not shares in it are held, and
  setting it again replaces the earlier sector. Symbols start with no sector.
- Add `Portfolio.get_sector(symbol) -> str`: the symbol's sector. It raises
  `ValueError` for an invalid symbol, then `KeyError` for a symbol that has
  no sector.
- Add `Portfolio.get_sectors() -> list[str]`: every sector that is currently
  the sector of at least one symbol, in the order the sectors were first
  used. A sector no symbol points to any more is not listed.
- Add `Portfolio.get_sector_holdings(sector) -> list[str]`: the symbols in
  `get_holdings()` whose sector is `sector`, in the same order as
  `get_holdings()`. A sector that `get_sectors()` does not list raises
  `KeyError`. Symbols without a sector never appear.
- Setting a sector changes no cash, shares or trades.

All existing behavior must keep working.
