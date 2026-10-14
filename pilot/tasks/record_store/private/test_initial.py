import pytest
from records import RecordStore, ValidationError

ADA = {"name": "Ada", "email": "ada@example.com", "age": 36}
BOB = {"name": "Bob", "email": "bob@example.com", "age": 41}


def person(n):
    # Distinct emails, so these tests stay valid if emails must later be unique.
    return {"name": f"P{n}", "email": f"p{n}@example.com", "age": 20 + n}


@pytest.fixture
def path(tmp_path):
    return tmp_path / "db"


@pytest.fixture
def store(path):
    return RecordStore(path)


def snapshot(store):
    return {record_id: store.get(record_id) for record_id in store.list_ids()}


# --- ids --------------------------------------------------------------------


def test_ids_start_at_one_and_increase(store):
    assert [store.add(person(n)) for n in range(3)] == [1, 2, 3]


def test_ids_are_not_reused_after_delete(store, path):
    store.add(person(1))
    second = store.add(person(2))
    store.delete(second)
    assert store.add(person(3)) == 3
    assert RecordStore(path).add(person(4)) == 4


def test_accepts_str_path(path):
    assert RecordStore(str(path)).add(ADA) == 1


def test_new_store_is_empty(store):
    assert store.list_ids() == []


# --- reads ------------------------------------------------------------------


def test_list_ids_is_sorted(store):
    for n in range(3):
        store.add(person(n))
    store.delete(2)
    assert store.list_ids() == [1, 3]


def test_get_returns_a_copy(store):
    record_id = store.add(ADA)
    store.get(record_id)["name"] = "Mallory"
    assert store.get(record_id) == ADA


def test_add_stores_a_copy(store):
    record = dict(ADA)
    record_id = store.add(record)
    record["name"] = "Mallory"
    assert store.get(record_id) == ADA


@pytest.mark.parametrize("operation", ["get", "delete"])
def test_missing_id_raises_key_error(store, operation):
    store.add(ADA)
    with pytest.raises(KeyError):
        getattr(store, operation)(99)


def test_update_missing_id_raises_key_error(store):
    with pytest.raises(KeyError):
        store.update(1, {"age": 1})


@pytest.mark.parametrize("fields", [{"age": -5}, {}, "junk"])
def test_missing_id_is_reported_before_bad_fields(store, fields):
    store.add(ADA)
    with pytest.raises(KeyError):
        store.update(99, fields)


@pytest.mark.parametrize("bad_id", ["1", True, 1.0, None])
@pytest.mark.parametrize("operation", ["get", "delete"])
def test_ids_that_are_not_int_are_not_stored(store, operation, bad_id):
    store.add(ADA)  # id 1 exists, and True == 1 == 1.0 in Python
    with pytest.raises(KeyError):
        getattr(store, operation)(bad_id)
    assert store.list_ids() == [1]


@pytest.mark.parametrize("bad_id", ["1", True, 1.0])
def test_update_with_id_that_is_not_int_raises_key_error(store, bad_id):
    store.add(ADA)
    with pytest.raises(KeyError):
        store.update(bad_id, {"age": 50})
    assert store.get(1) == ADA


# --- validation -------------------------------------------------------------


@pytest.mark.parametrize(
    "record",
    [
        {"name": "Ada", "email": "ada@example.com"},
        {**ADA, "phone": "555"},
        {**ADA, "name": ""},
        {**ADA, "name": "x" * 101},
        {**ADA, "name": 7},
        {**ADA, "email": "ada.example.com"},
        {**ADA, "email": "ada@@example.com"},
        {**ADA, "email": "@example.com"},
        {**ADA, "email": "ada@"},
        {**ADA, "email": None},
        {**ADA, "age": -1},
        {**ADA, "age": 151},
        {**ADA, "age": 36.0},
        {**ADA, "age": "36"},
        {**ADA, "age": True},
        ["Ada", "ada@example.com", 36],
    ],
)
def test_invalid_records_are_rejected(store, record):
    with pytest.raises(ValidationError):
        store.add(record)


@pytest.mark.parametrize(
    "record",
    [{**ADA, "name": "x"}, {**ADA, "name": "x" * 100}, {**ADA, "age": 0}, {**ADA, "age": 150}],
)
def test_boundary_values_are_accepted(store, record):
    assert store.get(store.add(record)) == record


def test_duplicate_emails_are_allowed(store):
    first = store.add(ADA)
    second = store.add({**BOB, "email": ADA["email"]})
    assert store.get(first)["email"] == store.get(second)["email"]


# --- updates and deletes ----------------------------------------------------


def test_update_changes_only_given_fields(store):
    record_id = store.add(ADA)
    store.update(record_id, {"age": 37})
    assert store.get(record_id) == {**ADA, "age": 37}


def test_update_checks_the_merged_record(store):
    record_id = store.add(ADA)
    with pytest.raises(ValidationError):
        store.update(record_id, {"email": "nope"})
    assert store.get(record_id) == ADA


@pytest.mark.parametrize(
    "fields", [{}, {"phone": "x"}, {"age": 37, "phone": "x"}, ["age"], None, "age"]
)
def test_update_fields_must_be_a_non_empty_dict_of_known_keys(store, fields):
    record_id = store.add(ADA)
    with pytest.raises(ValidationError):
        store.update(record_id, fields)
    assert store.get(record_id) == ADA


def test_delete_removes_record(store):
    record_id = store.add(ADA)
    store.delete(record_id)
    assert store.list_ids() == []
    with pytest.raises(KeyError):
        store.get(record_id)


# --- failed operations have no effect --------------------------------------


def test_failed_add_changes_nothing(store, path):
    store.add(ADA)
    with pytest.raises(ValidationError):
        store.add({**BOB, "age": -5})
    assert snapshot(store) == {1: ADA}
    assert snapshot(RecordStore(path)) == {1: ADA}
    assert store.add(BOB) == 2  # the failed add did not use up an id


def test_failed_update_leaves_record_unchanged(store, path):
    record_id = store.add(ADA)
    with pytest.raises(ValidationError):
        store.update(record_id, {"name": "Ada Lovelace", "age": 999})
    assert store.get(record_id) == ADA
    assert RecordStore(path).get(record_id) == ADA


def test_failed_delete_changes_nothing(store):
    store.add(ADA)
    with pytest.raises(KeyError):
        store.delete(5)
    assert snapshot(store) == {1: ADA}


# --- persistence ------------------------------------------------------------


def test_all_changes_are_saved(store, path):
    first = store.add(ADA)
    second = store.add(BOB)
    store.update(first, {"name": "Ada L"})
    store.delete(second)
    assert snapshot(RecordStore(path)) == {first: {**ADA, "name": "Ada L"}}


def test_reopened_store_continues_id_sequence(store, path):
    store.add(ADA)
    store.add(BOB)
    assert RecordStore(path).add(person(3)) == 3
