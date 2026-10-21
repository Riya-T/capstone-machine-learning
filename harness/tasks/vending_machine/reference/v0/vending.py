"""Vending machine: slots with a price and a stock, coins a customer has put in,
and purchases paid from that credit.

Correct solution for vending_machine before any change (the initial spec).
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vending import VendingMachine
    machine = VendingMachine()
    machine.add_slot("A1", 150)
    machine.restock("A1", 5)
    machine.insert_coins(200)
    machine.buy("A1")
"""


class VendingError(Exception):
    pass


class SoldOut(VendingError):
    pass


class NotEnoughCredit(VendingError):
    pass


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class VendingMachine:
    def __init__(self):
        self._prices = {}  # slot id -> price in cents, in the order slots were added
        self._stock = {}  # slot id -> number of items in the slot
        self._credit = 0  # cents inserted and not yet spent or returned

    def add_slot(self, slot_id, price):
        if not isinstance(slot_id, str) or not slot_id:
            raise ValueError("slot_id must be a non-empty str")
        check_positive(price, "price")
        if slot_id in self._prices:
            raise VendingError(f"slot {slot_id!r} already exists")
        self._prices[slot_id] = price
        self._stock[slot_id] = 0

    def restock(self, slot_id, count):
        self._require(slot_id)
        check_positive(count, "count")
        self._stock[slot_id] += count

    def insert_coins(self, amount):
        check_positive(amount, "amount")
        self._credit += amount

    def buy(self, slot_id):
        self._require(slot_id)
        if self._stock[slot_id] == 0:
            raise SoldOut(f"slot {slot_id!r} is empty")
        price = self._prices[slot_id]
        if self._credit < price:
            raise NotEnoughCredit(f"slot {slot_id!r} costs {price}, credit is {self._credit}")
        self._stock[slot_id] -= 1
        self._credit -= price

    def take_change(self):
        change = self._credit
        self._credit = 0
        return change

    def get_credit(self):
        return self._credit

    def get_stock(self, slot_id):
        self._require(slot_id)
        return self._stock[slot_id]

    def get_slots(self):
        return list(self._prices)

    def _require(self, slot_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(slot_id, str) or slot_id not in self._prices:
            raise KeyError(slot_id)
