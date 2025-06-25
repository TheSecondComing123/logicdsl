from logicdsl import LogicSolver
from logicdsl.tagset import TagSet


def count_true(assign, tags):
	return sum(assign[t] for t in tags)


def test_tagset_exactly_one():
	tags = ["r", "g", "b"]
	S = LogicSolver()
	ts = TagSet(S, tags)
	ts.enforce_exactly_one()
	sols = S.all_solutions()
	assert len(sols) == 3
	for s in sols:
		assert count_true(s["assignment"], tags) == 1


def test_tagset_at_least_one():
	S = LogicSolver()
	ts = TagSet(S, ["x", "y"])
	ts.enforce_at_least_one()
	sol = S.solve()
	a = sol["assignment"]
	assert a["x"] + a["y"] >= 1


def test_tagset_at_most_k():
	tags = ["a", "b", "c", "d"]
	S = LogicSolver()
	ts = TagSet(S, tags)
	ts.enforce_at_most(2)
	sols = S.all_solutions()
	assert len(sols) == 11
	for s in sols:
		assert count_true(s["assignment"], tags) <= 2
