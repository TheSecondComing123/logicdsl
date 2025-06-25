"""
Integration tests for logicdsl.solver.
"""

import pytest

from logicdsl import LogicSolver, Var, distinct, product_of, sum_of


def test_basic_optimal_solution():
	"""
	x ∈ [1..9], y ∈ {2,4,6,8}
	Hard: x + y = 10
	Maximize: x * y
	"""
	x = Var("x") << (1, 9)
	y = Var("y") << {2, 4, 6, 8}
	
	S = LogicSolver()
	S.require(sum_of([x, y]) == 10, "sum10")
	S.maximize(product_of([x, y]))
	
	sol = S.solve()
	best = sol["assignment"]
	assert best == {"x": 4, "y": 6} or best == {"x": 6, "y": 4}
	assert sol["penalty"] == 0
	assert sol["objectives"][0] == best["x"] * best["y"]


def test_soft_penalty_and_objective():
	"""
	Add a soft constraint z == 0 (penalty 5) and an objective to minimize z.
	Optimal solution should choose z = 0 to avoid penalty if possible.
	"""
	x = Var("x") << (1, 5)
	z = Var("z") << {0, 1}
	
	S = LogicSolver()
	# hard: x even
	S.require(x % 2 == 0, "x_even")
	# soft: prefer z == 0
	S.prefer(z == 0, penalty=5, name="z_zero")
	# objective: minimize z
	S.minimize(z)
	
	sol = S.solve()
	assert sol["assignment"]["z"] == 0
	assert sol["penalty"] == 0
	# objective list has one element (min z) → value should be 0
	assert sol["objectives"][0] == 0


def test_distinct_constraint_in_solver():
	"""
	Three vars in [1..3] must be distinct, maximize sum.
	Best assignment should be 1,2,3 in some order → sum 6.
	"""
	a, b, c = [Var(v) << (1, 3) for v in "abc"]
	
	S = LogicSolver()
	S.require(distinct([a, b, c]), "all_diff")
	S.maximize(sum_of([a, b, c]))
	
	sol = S.solve()
	values = list(sol["assignment"].values())
	assert sorted(values) == [1, 2, 3]
	assert sum(values) == 6
	assert sol["penalty"] == 0
	assert sol["objectives"][0] == 6


def test_unsat_raises():
	"""
	Impossible constraint should raise RuntimeError.
	"""
	x = Var("x") << {1}
	y = Var("y") << {2}
	S = LogicSolver()
	S.require(sum_of([x, y]) == 100, "impossible")
	
	with pytest.raises(RuntimeError):
		S.solve()


def test_all_solutions_limit():
	"""Enumerate first two solutions to x + y == 4 with x,y in [1..3]."""
	x = Var("x") << (1, 3)
	y = Var("y") << (1, 3)
	
	S = LogicSolver()
	S.require(sum_of([x, y]) == 4)
	
	sols = S.all_solutions(limit=2)
	assert len(sols) == 2
	assert sols[0]["assignment"] == {"x": 1, "y": 3}
	assert sols[1]["assignment"] == {"x": 2, "y": 2}


def test_all_solutions_penalty_and_objective():
	"""Return solutions with penalties and objective values included."""
	x = Var("x") << {0, 1}
	
	S = LogicSolver()
	S.prefer(x == 1, penalty=5)
	S.maximize(x)
	
	sols = S.all_solutions()
	assert len(sols) == 2
	# first assignment should be x=0 (penalty 5)
	assert sols[0]["assignment"]["x"] == 0
	assert sols[0]["penalty"] == 5
	assert sols[0]["objectives"][0] == 0
	# second assignment should be x=1 (penalty 0)
	assert sols[1]["assignment"]["x"] == 1
	assert sols[1]["penalty"] == 0
	assert sols[1]["objectives"][0] == 1


def test_objective_mode_sum():
	"""Weighted-sum objectives choose different assignment than lexicographic."""
	x = Var("x") << {0, 1}
	y = Var("y") << {0, 1}
	
	constraint = sum_of([x, y]) <= 1
	
	S_lex = LogicSolver()
	S_lex.require(constraint)
	S_lex.maximize(x)
	S_lex.maximize(y)
	
	sol_lex = S_lex.solve()
	assert sol_lex["assignment"] == {"x": 1, "y": 0}
	
	S_sum = LogicSolver(objective_mode="sum")
	S_sum.require(constraint)
	S_sum.maximize(x, weight=1)
	S_sum.maximize(y, weight=2)
	
	sol_sum = S_sum.solve()
	assert sol_sum["assignment"] == {"x": 0, "y": 1}
	assert sol_sum["objective"] == 2


def test_soft_weights_with_sum_mode():
	"""Weighted soft constraints influence tie-breaking when using sum mode."""
	x = Var("x") << {0, 1}
	y = Var("y") << {0, 1}
	
	S = LogicSolver(objective_mode="sum")
	S.require(sum_of([x, y]) == 1)
	S.prefer(x == 1, penalty=1, weight=5.0)
	S.prefer(y == 1, penalty=1, weight=1.0)
	
	sol = S.solve()
	assert sol["assignment"] == {"x": 1, "y": 0}
	assert sol["penalty"] == 1
	assert sol["objective"] == -1


def test_solve_timeout():
	"""Solver should raise TimeoutError when search exceeds the limit."""
	x = Var("x") << (1, 9)
	y = Var("y") << (1, 9)
	
	S = LogicSolver()
	S.require(sum_of([x, y]) >= 0)
	
	with pytest.raises(TimeoutError):
		S.solve(timeout=0.0)


def test_all_solutions_timeout_returns_partial():
	"""all_solutions returns any found solutions when timing out."""
	x = Var("x") << (0, 1)
	
	S = LogicSolver()
	S.prefer(x == 1, penalty=1)
	
	sols = S.all_solutions(timeout=0.0)
	assert sols == []


def test_require_all():
	xs = [Var(f"x{i}") << (0, 3) for i in range(3)]

	S = LogicSolver()
	S.require_all(lambda v: v < 2, xs)
	S.require(sum_of(xs) == 3)

	sol = S.solve()
	assert sol["assignment"] == {f"x{i}": 1 for i in range(3)}
