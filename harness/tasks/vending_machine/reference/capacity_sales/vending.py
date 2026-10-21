"""Vending machine with slot capacities and a sales report.

Correct solution for vending_machine after c_capacity and c_sales.
Never shown to the writer or the editor; validate-tasks checks that it
passes every test it should.

Usage:
    from vending import VendingMachine
    machine = VendingMachine()
    machine.add_slot("A1", 150, capacity=8)
    machine.restock("A1", 5)
    machine.insert_coins(150)
    machine.buy("A1")
    machine.get_sales_report()
"""


class VendingError(Exception):
    pass


class SoldOut(VendingError):
    pass


class NotEnoughCredit(VendingError):
    pass


class SlotFull(VendingError):
    pass


def check_positive(value, what):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{what} must be a positive int, got {value!r}")


def check_capacity(capacity):
    if capacity is not None:
        check_positive(capacity, "capacity")


class VendingMachine:
    def __init__(self):
        self._prices = {}  # slot id -> price in cents, in the order slots were added
        self._stock = {}  # slot id -> number of items in the slot
        self._capacity = {}  # slot id -> capacity, or None for no limit
        self._sales = {}  # slot id -> items bought so far
        self._revenue = 0  # cents paid for purchases
        self._credit = 0  # cents inserted and not yet spent or returned

    def add_slot(self, slot_id, price, capacity=None):
        if not isinstance(slot_id, str) or not slot_id:
            raise ValueError("slot_id must be a non-empty str")
        check_positive(price, "price")
        check_capacity(capacity)
        if slot_id in self._prices:
            raise VendingError(f"slot {slot_id!r} already exists")
        self._prices[slot_id] = price
        self._stock[slot_id] = 0
        self._capacity[slot_id] = capacity
        self._sales[slot_id] = 0

    def restock(self, slot_id, count):
        self._require(slot_id)
        check_positive(count, "count")
        self._require_room(slot_id, self._stock[slot_id] + count, self._capacity[slot_id])
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
        self._sales[slot_id] += 1
        self._revenue += price

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

    def get_capacity(self, slot_id):
        self._require(slot_id)
        return self._capacity[slot_id]

    def set_capacity(self, slot_id, capacity):
        self._require(slot_id)
        check_capacity(capacity)
        if capacity is not None and self._stock[slot_id] > capacity:
            raise VendingError(f"slot {slot_id!r} already holds more than {capacity}")
        self._capacity[slot_id] = capacity

    def get_sales(self, slot_id):
        self._require(slot_id)
        return self._sales[slot_id]

    def get_revenue(self):
        return self._revenue

    def get_sales_report(self):
        # sorted() is stable, so ties keep the order the slots were added in.
        return sorted(self._sales.items(), key=lambda item: -item[1])

    def _require(self, slot_id):
        # Non-str ids are never stored, so they count as unknown too.
        if not isinstance(slot_id, str) or slot_id not in self._prices:
            raise KeyError(slot_id)

    @staticmethod
    def _require_room(slot_id, new_stock, capacity):
        if capacity is not None and new_stock > capacity:
            raise SlotFull(f"slot {slot_id!r} holds at most {capacity}")
