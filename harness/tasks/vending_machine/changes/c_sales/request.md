Add sales reporting to `vending.py`, so the owner can see what the machine
has sold.

- Add `VendingMachine.get_sales(slot_id) -> int`: how many items have been
  bought from that slot so far. Only successful calls to `buy` count;
  restocking does not change it. Raises `KeyError` for a slot that does not
  exist.
- Add `VendingMachine.get_revenue() -> int`: the total cents paid for all
  items bought, over all slots, each at its slot's price. Coins that were
  inserted but not spent do not count, and `take_change` does not change it.
- Add `VendingMachine.get_sales_report() -> list[tuple[str, int]]`: every
  slot with its sales count as `(slot_id, sales)`, most sold first. Slots
  with the same count keep the order they were added in. A slot nothing has
  been bought from is listed with 0.
- A new machine has a revenue of 0, and every count is 0.

All existing behavior must keep working.
