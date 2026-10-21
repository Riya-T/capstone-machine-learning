Add client groups to `gateway.py`, so the allow list can be managed for a
whole group at once.

- Add `Gateway.create_group(group)`. An empty group name raises
  `ValueError`; a name that already exists raises `GatewayError`.
- Add `Gateway.get_groups() -> list[str]`: the groups, in the order they
  were created.
- Add `Gateway.assign_group(client_id, group)`, which puts the client in
  the group. A client is in at most one group, so this takes it out of
  any group it was in. It raises `KeyError` for a client that is not
  registered, then `KeyError` for a group that does not exist.
- Add `Gateway.get_group(client_id) -> str | None`: the client's group,
  or `None` when it is in no group. It raises `KeyError` for a client that
  is not registered.
- Add `Gateway.get_members(group) -> list[str]`: the clients in the group,
  in the order they were registered. It raises `KeyError` for a group that
  does not exist.
- Add `Gateway.allow_group(group)`, which allows every member, exactly as
  if `allow` were called on each. If `allow` would raise for any member,
  `allow_group` raises that error instead and allows nobody. Clients that
  join the group later are not allowed automatically.
- Add `Gateway.revoke_group(group)`, which revokes every member, exactly as
  if `revoke` were called on each.
- `allow_group` and `revoke_group` raise `KeyError` for a group that does
  not exist. A group with no members is fine: nothing happens.
- Being in a group changes nothing else about a client.

All existing behavior must keep working.
