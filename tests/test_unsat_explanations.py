import pytest

from logicdsl import LogicSolver, Var


def test_why_unsat_simple():
	x = Var("x") << {0, 1}
	S = LogicSolver()
	S.require(x == 0, "x_zero")
	S.require(x == 1, "x_one")
	with pytest.raises(RuntimeError):
		S.solve()
	assert set(S.why_unsat()) == {"x_zero", "x_one"}


def test_why_unsat_conflict():
	x = Var("x") << {0, 1}
	y = Var("y") << {0, 1}
	S = LogicSolver()
	S.require(x == y, "eq")
	S.require(x != y, "neq")
	with pytest.raises(RuntimeError):
		S.solve()
	assert set(S.why_unsat()) == {"eq", "neq"}
