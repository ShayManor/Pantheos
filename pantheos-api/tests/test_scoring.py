import pytest

from app import scoring


def test_weight_known_and_default():
    assert scoring.weight(0) == 8
    assert scoring.weight(1) == 4
    assert scoring.weight(2) == 2
    assert scoring.weight(3) == 1
    assert scoring.weight(9) == 1  # unknown → default


def test_own_urgency_no_deadline():
    assert scoring.own_urgency(None, 5) == 0.3


def test_own_urgency_with_deadline():
    assert scoring.own_urgency(24, 0) == pytest.approx(0.5)  # slack 24 → 1/(1+1)


def test_own_urgency_none_effort():
    assert scoring.own_urgency(24, None) == pytest.approx(0.5)


def test_inherited_urgency():
    assert scoring.inherited_urgency(0.3, []) == 0.3
    assert scoring.inherited_urgency(0.3, [0.5]) == pytest.approx(0.4)  # 0.8*0.5 > 0.3


def test_compute_score():
    assert scoring.compute_score(0, 1.0) == pytest.approx(8.0)


def test_due_display():
    assert scoring.due_display(None) is None
    assert scoring.due_display(5) == "now"
    assert scoring.due_display(48) == "in 2d"


def test_is_hot():
    assert scoring.is_hot(None) is False
    assert scoring.is_hot(48) is True
    assert scoring.is_hot(96) is False


def test_format_score():
    assert scoring.format_score(4.44) == "4.4"


def test_score_tickets_dep_propagation():
    rows = [
        {"id": "A", "pri": 2, "deadline_hours": None, "effort_hours": 5, "dep_ids": []},
        {"id": "B", "pri": 1, "deadline_hours": 24, "effort_hours": 0, "dep_ids": ["A", "NOPE"]},
    ]
    scores = scoring.score_tickets(rows)
    assert set(scores) == {"A", "B"}
    # A is depended on by B → inherits urgency and outscores its own baseline
    assert scores["A"] > scoring.compute_score(2, 0.3)
