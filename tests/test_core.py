"""
Unit tests for logicdsl.core and logicdsl.constraints.

Run with:
    pytest -q
"""

from logicdsl import (BoolVar, Var, at_most_one, distinct, exactly_one, exists, forall)


# ─────────────────────────────────────────────────────────────────────────────
# Helper to build a tiny assignment dict quickly
def assgn(**kwargs):
	return kwargs


# ─────────────────────────────────────────────────────────────────────────────
def test_expr_arithmetic_and_eval():
	x = Var("x") << (1, 5)
	y = Var("y") << {2, 4}
	
	expr = (x + y * 3) ** 2 // 2
	result = expr.eval(assgn(x=2, y=4))  # (2 + 12)**2 // 2 = 14**2 // 2 = 196 // 2
	assert result == 98


def test_var_neg_and_abs():
	x = Var("x") << (-5, 5)
	expr = (-x).abs()  # | -x |
	assert expr.eval(assgn(x=-3)) == 3
	assert expr.eval(assgn(x=4)) == 4


def test_bool_comparisons():
	x = Var("x") << (0, 10)
	y = Var("y") << (0, 10)
	
	beq = x + 1 == y
	bgt = x > y
	
	assert beq.satisfied(assgn(x=3, y=4)) is True
	assert beq.satisfied(assgn(x=5, y=4)) is False
	assert bgt.satisfied(assgn(x=6, y=2)) is True
	assert (~bgt).satisfied(assgn(x=1, y=8)) is True  # NOT


def test_logic_composition():
	x = Var("x") << (1, 4)
	y = BoolVar("y")
	
	expr = (x < 3) & y
	assert expr.satisfied(assgn(x=2, y=1))
	assert not expr.satisfied(assgn(x=4, y=1))
	assert not expr.satisfied(assgn(x=2, y=0))
	
	xor_expr = (x < 3) ^ (x > 3)
	assert xor_expr.satisfied(assgn(x=1))
	assert xor_expr.satisfied(assgn(x=4))
	assert not xor_expr.satisfied(assgn(x=3))  # both false


def test_set_constraints():
	a, b, c = [Var(v) << (1, 3) for v in "abc"]
	# distinct true case
	assert distinct([a, b, c]).satisfied(assgn(a=1, b=2, c=3))
	# false when duplicates
	assert not distinct([a, b, c]).satisfied(assgn(a=1, b=2, c=2))
	
	bools = [BoolVar(f"p{i}") for i in range(3)]
	assignment = {f"p{i}": v for i, v in enumerate((1, 0, 0))}
	# exactly_one should pass
	assert exactly_one(bools).satisfied(assignment)
	
	assignment_bad = {f"p{i}": 1 for i in range(3)}
	# at_most_one fails on 3 ones
	assert not at_most_one(bools).satisfied(assignment_bad)


def test_quantifiers():
	xs = [Var(f"x{i}") << (1, 3) for i in range(3)]
	# forall xs: x <= 3   (always true by domain)
	assert forall(xs, lambda v: v <= 3).satisfied(assgn(x0=1, x1=2, x2=3))
	
	# exists xs: x == 2
	assert exists(xs, lambda v: v == 2).satisfied(assgn(x0=1, x1=2, x2=3))
	assert not exists(xs, lambda v: v == 4).satisfied(assgn(x0=1, x1=2, x2=3))


def test_boolexpr_named():
	expr = (Var("x") << (1, 2)) == 1
	named = expr.named("Xeq1")
	assert named.name == "Xeq1"
