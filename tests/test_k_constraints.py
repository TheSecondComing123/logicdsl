"""
Unit tests for at_least_k and exactly_k constraints.
"""

from logicdsl import BoolVar, at_least_k, exactly_k


def assgn(**kwargs):
	return kwargs


def test_at_least_k_basic():
	bools = [BoolVar(f"p{i}") for i in range(4)]
	assignment = {f"p{i}": v for i, v in enumerate((1, 0, 1, 0))}
	assert at_least_k(bools, 2).satisfied(assignment)
	assert at_least_k(bools, 3).satisfied({f"p{i}": 1 for i in range(4)})
	assert not at_least_k(bools, 3).satisfied(assignment)


def test_at_least_k_boundaries():
	bools = [BoolVar("p0"), BoolVar("p1")]
	assignment = {"p0": 0, "p1": 1}
	assert at_least_k(bools, 0).satisfied(assignment)
	assert not at_least_k(bools, 3).satisfied(assignment)


def test_exactly_k_basic():
	bools = [BoolVar(f"q{i}") for i in range(3)]
	assignment = {"q0": 1, "q1": 0, "q2": 1}
	assert exactly_k(bools, 2).satisfied(assignment)
	assert not exactly_k(bools, 2).satisfied({"q0": 1, "q1": 1, "q2": 1})
	assert not exactly_k(bools, 2).satisfied({"q0": 0, "q1": 1, "q2": 0})


def test_exactly_k_boundaries():
	bools = [BoolVar("r0"), BoolVar("r1")]
	assignment0 = {"r0": 0, "r1": 0}
	assignment1 = {"r0": 1, "r1": 1}
	assert exactly_k(bools, 0).satisfied(assignment0)
	assert exactly_k(bools, 2).satisfied(assignment1)
	assert not exactly_k(bools, 3).satisfied(assignment1)
