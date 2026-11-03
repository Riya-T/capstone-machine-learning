Group the symbols in `portfolio.py` into sectors, so holdings can be looked
at one sector at a time.

- Add `Portfolio.set_sector(symbol, sector)`. The symbol follows the usual
  symbol rules (`ValueError` when invalid). An empty string or `None` as the
  sector raises `ValueError`. A sector can be set for any symbol, whether or
  not shares in it are held, and setting it again replaces the earlier
  sector. Symbols start with no sector.
- Add `Portfolio.get_sector(symbol) -> str`: the symbol's sector. It raises
  `ValueError` for an invalid symbol, and `KeyError` for a valid symbol that
  has no sector.
- Add `Portfolio.get_sectors() -> list[str]`: every sector that is currently
  the sector of at least one symbol, in the order the sectors were first
  used. A sector no symbol points to any more is not listed. For example,
  after `set_sector("ACME", "industrials")` and then
  `set_sector("ACME", "tech")`, with no other sectors set, `get_sectors()`
  is `["tech"]` and `get_sector_holdings("industrials")` raises `KeyError`.
- Add `Portfolio.get_sector_holdings(sector) -> list[str]`: the symbols in
  `get_holdings()` whose sector is `sector`, in the same order as
  `get_holdings()`, whatever order their sectors were set in. For example,
  if ACME was bought before BOLT, and then `set_sector("BOLT", "tech")`
  was called before `set_sector("ACME", "tech")`,
  `get_sector_holdings("tech")` is `["ACME", "BOLT"]`. A sector that
  `get_sectors()` does not list raises `KeyError`. Symbols without a sector
  never appear.
- Setting a sector changes no cash, shares or trades.

All existing behavior must keep working.
