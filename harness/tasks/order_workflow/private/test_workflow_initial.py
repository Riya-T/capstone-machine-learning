"""Hidden tests for the initial order_workflow spec. They decide whether a
program is correct to begin with. Never shown to the writer or the editor.

Usage (with workflow.py importable, e.g. in the sandbox):
    python -m pytest private/test_workflow_initial.py
"""

import pytest
from workflow import InvalidTransition, OrderWorkflow, WorkflowError

STATES = ["new", "paid", "shipped", "delivered", "cancelled"]
BAD_TOTALS = [0, -5, 1.5, "10", None]
BAD_STATE_NAMES = ["", "Paid", "refunded", None, 1]


@pytest.fixture
def flow():
    wf = OrderWorkflow()
    wf.create_order("o1", 2500)
    wf.create_order("o2", 900)
    return wf


def state(wf):
    """Every order's state and total, to check that a failed call changed nothing."""
    return {o: (wf.get_state(o), wf.get_total(o)) for o in wf.get_orders()}


PATH_TO = {
    "new": [],
    "paid": ["paid"],
    "shipped": ["paid", "shipped"],
    "delivered": ["paid", "shipped", "delivered"],
    "cancelled": ["cancelled"],
}


def bring_to(wf, order_id, target):
    """Move a new order along an allowed path until it is in `target`."""
    for s in PATH_TO[target]:
        wf.move(order_id, s)


# --- orders -----------------------------------------------------------------------


def test_a_new_order_has_its_total_and_state(flow):
    assert flow.get_state("o2") == "new"
    assert flow.get_total("o2") == 900


def test_orders_are_listed_in_creation_order():
    wf = OrderWorkflow()
    for name in ["c", "a", "b"]:
        wf.create_order(name, 100)
    assert wf.get_orders() == ["c", "a", "b"]


def test_an_empty_order_id_is_rejected():
    wf = OrderWorkflow()
    with pytest.raises(ValueError):
        wf.create_order("", 100)
    assert wf.get_orders() == []


@pytest.mark.parametrize("total", BAD_TOTALS)
def test_invalid_totals_are_rejected(total):
    wf = OrderWorkflow()
    with pytest.raises(ValueError):
        wf.create_order("o1", total)
    assert wf.get_orders() == []


def test_creating_an_existing_order_is_rejected(flow):
    flow.move("o1", "paid")
    with pytest.raises(WorkflowError):
        flow.create_order("o1", 100)
    assert flow.get_state("o1") == "paid"
    assert flow.get_total("o1") == 2500
    assert flow.get_orders() == ["o1", "o2"]


def test_a_bad_total_is_reported_before_a_duplicate_id(flow):
    with pytest.raises(ValueError):
        flow.create_order("o1", 0)
    assert flow.get_total("o1") == 2500


@pytest.mark.parametrize(
    "call",
    [
        lambda wf: wf.move("o9", "paid"),
        lambda wf: wf.get_state("o9"),
        lambda wf: wf.get_total("o9"),
        lambda wf: wf.move(None, "paid"),
        lambda wf: wf.get_state(1),
    ],
)
def test_orders_that_do_not_exist_raise_key_error(flow, call):
    before = state(flow)
    with pytest.raises(KeyError):
        call(flow)
    assert state(flow) == before


# --- moving -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        ["paid"],
        ["paid", "shipped"],
        ["paid", "shipped", "delivered"],
        ["cancelled"],
        ["paid", "cancelled"],
    ],
)
def test_every_allowed_path_can_be_walked(flow, path):
    for s in path:
        flow.move("o1", s)
    assert flow.get_state("o1") == path[-1]
    assert flow.get_state("o2") == "new"


@pytest.mark.parametrize(
    ("start", "target"),
    [
        ("new", "shipped"),
        ("new", "delivered"),
        ("paid", "delivered"),
        ("paid", "new"),
        ("shipped", "cancelled"),
        ("shipped", "paid"),
        ("shipped", "new"),
    ],
)
def test_moves_off_the_allowed_paths_are_rejected(flow, start, target):
    bring_to(flow, "o1", start)
    before = state(flow)
    with pytest.raises(InvalidTransition):
        flow.move("o1", target)
    assert state(flow) == before


@pytest.mark.parametrize("final", ["delivered", "cancelled"])
@pytest.mark.parametrize("target", STATES)
def test_final_orders_cannot_move_anywhere(flow, final, target):
    bring_to(flow, "o1", final)
    before = state(flow)
    with pytest.raises(InvalidTransition):
        flow.move("o1", target)
    assert state(flow) == before


@pytest.mark.parametrize("current", ["new", "paid", "shipped"])
def test_moving_to_the_current_state_is_rejected(flow, current):
    bring_to(flow, "o1", current)
    with pytest.raises(InvalidTransition):
        flow.move("o1", current)
    assert flow.get_state("o1") == current


@pytest.mark.parametrize("name", BAD_STATE_NAMES)
def test_unknown_state_names_are_rejected_when_moving(flow, name):
    before = state(flow)
    with pytest.raises(ValueError):
        flow.move("o1", name)
    assert state(flow) == before


@pytest.mark.parametrize("name", BAD_STATE_NAMES)
def test_unknown_state_names_are_rejected_when_listing(flow, name):
    with pytest.raises(ValueError):
        flow.get_orders_in(name)


def test_a_missing_order_is_reported_before_a_bad_state_name(flow):
    with pytest.raises(KeyError):
        flow.move("o9", "refunded")


def test_a_bad_state_name_is_reported_before_an_invalid_transition(flow):
    bring_to(flow, "o1", "delivered")
    with pytest.raises(ValueError):
        flow.move("o1", "refunded")


def test_orders_in_a_state_follow_moves(flow):
    flow.create_order("o3", 100)
    flow.move("o3", "paid")
    flow.move("o1", "paid")
    assert flow.get_orders_in("new") == ["o2"]
    assert flow.get_orders_in("paid") == ["o1", "o3"]
    flow.move("o3", "cancelled")
    assert flow.get_orders_in("paid") == ["o1"]
    assert flow.get_orders_in("cancelled") == ["o3"]
    assert flow.get_orders_in("shipped") == []


def test_every_order_is_in_exactly_one_state(flow):
    flow.move("o1", "paid")
    flow.move("o1", "shipped")
    listed = [o for s in STATES for o in flow.get_orders_in(s)]
    assert sorted(listed) == ["o1", "o2"]


def test_failed_moves_leave_the_lists_unchanged(flow):
    flow.move("o1", "paid")
    for call in (
        lambda: flow.move("o1", "delivered"),
        lambda: flow.move("o1", "refunded"),
        lambda: flow.move("o9", "paid"),
    ):
        with pytest.raises((KeyError, ValueError, WorkflowError)):
            call()
    assert flow.get_orders_in("paid") == ["o1"]
    assert flow.get_orders_in("new") == ["o2"]


def test_invalid_transition_is_a_workflow_error():
    assert issubclass(InvalidTransition, WorkflowError)


def test_workflows_do_not_share_orders():
    first, second = OrderWorkflow(), OrderWorkflow()
    first.create_order("o1", 100)
    first.move("o1", "paid")
    assert second.get_orders() == []
    second.create_order("o1", 200)
    assert second.get_state("o1") == "new"
    assert second.get_total("o1") == 200
