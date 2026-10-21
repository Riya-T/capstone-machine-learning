Group the tags in `docstore.py` into named tag groups, for example a
group `status` holding the tags `draft`, `review` and `final`.

- Add `DocumentStore.create_group(group_name)`. A name that is empty or not
  a string raises `ValueError`; a name that is already a group raises
  `StoreError`. Group names are separate from tags and document ids.
- Add `DocumentStore.add_tag_to_group(group_name, tag)`. It raises
  `KeyError` for a group that does not exist, then `ValueError` for a tag
  that is empty or not a string, then `StoreError` if the tag already
  belongs to a different group: a tag is in at most one group. Adding a tag
  to the group it is already in does nothing. The tag need not be on any
  document yet.
- Add `DocumentStore.get_group_tags(group_name) -> list[str]`: the group's
  tags in the order they were added. `KeyError` for a group that does not
  exist.
- Add `DocumentStore.get_groups() -> list[str]`: all group names in the
  order they were created.
- Add `DocumentStore.get_documents_in_group(group_name) -> list[str]`: the
  ids of the documents carrying at least one tag of the group, in the order
  the documents were added, each id once. Tags added to the group later and
  documents tagged later both count. `KeyError` for a group that does not
  exist.

A failed call changes nothing. All existing behavior must keep working.
