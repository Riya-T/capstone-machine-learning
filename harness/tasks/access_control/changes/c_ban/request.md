Let clients of `gateway.py` be banned, for example after abuse.

- Add `class ClientBanned(GatewayError)` to `gateway.py`.
- Add `Gateway.ban(client_id)`, `Gateway.unban(client_id)` and
  `Gateway.is_banned(client_id) -> bool`. All three raise `KeyError` for a
  client that is not registered. New clients are not banned. Banning a
  banned client, or unbanning one that is not banned, does nothing.
- Banning takes the client off the allow list. Unbanning does not put it
  back: the client stays off the allow list until `allow` is called again.
- While a client is banned, `allow(client_id)` raises `ClientBanned` and
  changes nothing, and `send(client_id, message)` raises `ClientBanned` and
  records nothing. `revoke` on a banned client does nothing.
- In `allow`, `ClientBanned` is checked after `KeyError`. In `send`, it is
  checked after `KeyError` and `ValueError` and before `AccessDenied`.
- Add `Gateway.get_banned() -> list[str]`: the banned clients, in the order
  they were registered.
- Banning and unbanning leave the client's messages as they are.

All existing behavior must keep working.
