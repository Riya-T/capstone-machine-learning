"""Vending machine whose slots can be taken out of order.

Correct solution for vending_machine after c_outage.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vending import VendingMachine
    machine = VendingMachine()
    machine.add_slot("A1", 150)
    machine.restock("A1", 5)
    machine.disable_slot("A1")
"""


class VendingError(Exception):
    pass


class SoldOut(VendingError):
    pass


class NotEnoughCredit(VendingError):
    pass


class SlotDisabled(VendingError):
    pass


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


class VendingMachine:
    def __init__(self):
        self._prices = {}  # slot id -> price in cents, in the order slots were added
        self._stock = {}  # slot id -> number of items in the slot
        self._disabled = set()  # slot ids that are out of order
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
        self._require_working(slot_id)
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

    def disable_slot(self, slot_id):
        self._require(slot_id)
        self._disabled.add(slot_id)

    def enable_slot(self, slot_id):
        self._require(slot_id)
        self._disabled.discard(slot_id)

    def is_disabled(self, slot_id):
        self._require(slot_id)
        return slot_id in self._disabled

    def get_working_slots(self):
        return [slot_id for slot_id in self._prices if slot_id not in self._disabled]

    def _require(self, slot_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(slot_id, str) or slot_id not in self._prices:
            raise KeyError(slot_id)

    def _require_working(self, slot_id):
        if slot_id in self._disabled:
            raise SlotDisabled(f"slot {slot_id!r} is out of order")
