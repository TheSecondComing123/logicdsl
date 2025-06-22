import pytest

from logicdsl import Var, sum_of, product_of, LogicSolver, Z3Solver


@pytest.mark.parametrize("Solver", [LogicSolver, Z3Solver])
def test_basic_solution(Solver):
 x = Var("x") << (1, 9)
 y = Var("y") << {2, 4, 6, 8}
 S = Solver()
 S.require(sum_of([x, y]) == 10)
 S.maximize(product_of([x, y]))
 sol = S.solve()
 values = sol["assignment"]
 assert values in ({"x": 4, "y": 6}, {"x": 6, "y": 4})
 assert sol["penalty"] == 0


@pytest.mark.parametrize("Solver", [LogicSolver, Z3Solver])
def test_all_solutions_limit(Solver):
 x = Var("x") << (1, 3)
 y = Var("y") << (1, 3)
 S = Solver()
 S.require(sum_of([x, y]) == 4)
 sols = S.all_solutions(limit=2)
 assert len(sols) == 2
 assigns = [s["assignment"] for s in sols]
 for a in assigns:
     assert a["x"] + a["y"] == 4
