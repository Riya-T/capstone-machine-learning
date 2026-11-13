Add Wallet.reverse(op_id, reversal_id) -> None. Find the existing
operation op_id and append an opposite operation of the same amount
for the same member, under a new unused reversal_id. Leave the original
history row in place. Each operation can be reversed at most once.
Reversal operations themselves may be reversed using the same rules.
Both IDs must be nonempty strings or the call raises ValueError.
An unknown valid original ID raises KeyError. An original that has
already been reversed, a new ID that is already used anywhere, or a
reversal that would make the balance negative raises ValueError.
Every failure leaves all balances, histories, ID availability and
reversal eligibility unchanged. Existing behavior still applies.

For example, after crediting 5 as "p1" and debiting 3 as "p2",
reverse("p2", "r2") appends a credit for 3 and restores balance to 5.
