import pytest

from logicdsl import LogicSolver, Var, Z3Solver, product_of, sum_of


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


def test_z3solver_timeout_solve():
    x = Var("x") << (1, 9)
    S = Z3Solver()
    S.require(x >= 0)
    with pytest.raises(TimeoutError):
        S.solve(timeout=0.0)


def test_z3solver_timeout_all_solutions():
    x = Var("x") << {0, 1}
    S = Z3Solver()
    S.prefer(x == 1, penalty=1)
    assert S.all_solutions(timeout=0.0) == []


def test_z3solver_why_unsat():
    x = Var("x") << {0, 1}
    S = Z3Solver()
    S.require(x == 0, "x_zero")
    S.require(x == 1, "x_one")
    with pytest.raises(RuntimeError):
        S.solve()
    assert set(S.why_unsat()) == {"x_zero", "x_one"}
