# logicdsl/constraints.py
from __future__ import annotations

from typing import Iterable, List

from .core import BoolExpr, Expr, Var


# ───────────────────────────── utilities
def _fold_and(xs: List[BoolExpr]) -> BoolExpr:
	if not xs:
		return BoolExpr(lambda a: True, "true")
	out = xs[0]
	for x in xs[1:]:
		out = out & x
	return out


def _fold_or(xs: List[BoolExpr]) -> BoolExpr:
	if not xs:
		return BoolExpr(lambda a: False, "false")
	out = xs[0]
	for x in xs[1:]:
		out = out | x
	return out


# Coerce a BoolVar (domain {0,1}) to BoolExpr
def _to_bool(x):
	if isinstance(x, BoolExpr):
		return x
	if isinstance(x, Var) and x.domain == [0, 1]:
		return x == 1
	raise TypeError("Expected BoolExpr or BoolVar")


# ───────────────────────────── predicates
def distinct(vs: Iterable[Var]) -> BoolExpr:
	vs = list(vs)
	return BoolExpr(
		lambda a, _vs=vs: len({a[v.name] for v in _vs}) == len(_vs),
		"distinct",
	)


def at_least_one(xs: List[BoolExpr | Var]) -> BoolExpr:
	return _fold_or([_to_bool(x) for x in xs])


def at_most_one(xs: List[BoolExpr | Var]) -> BoolExpr:
	xs_b = [_to_bool(x) for x in xs]
	return _fold_and([~(p & q) for i, p in enumerate(xs_b) for q in xs_b[i + 1:]])


def exactly_one(xs: List[BoolExpr | Var]) -> BoolExpr:
	xs_b = [_to_bool(x) for x in xs]
	return at_least_one(xs_b) & at_most_one(xs_b)


def forall(vs: Iterable[Var], f) -> BoolExpr:
	return _fold_and([f(v) for v in vs])


def exists(vs: Iterable[Var], f) -> BoolExpr:
        return _fold_or([f(v) for v in vs])


# ───────────────────────────── arithmetic helpers
def sum_of(xs: Iterable[Expr | Var]) -> Expr:
        """Return an expression representing the sum of ``xs``.

        The empty sum evaluates to 0.
        """
        xs = list(xs)
        if not xs:
                return Expr(lambda a: 0)

        total = Expr._E(xs[0])
        for x in xs[1:]:
                total = total + Expr._E(x)
        return total


def product_of(xs: Iterable[Expr | Var]) -> Expr:
        """Return an expression representing the product of ``xs``.

        The empty product evaluates to 1.
        """
        xs = list(xs)
        if not xs:
                return Expr(lambda a: 1)

        prod = Expr._E(xs[0])
        for x in xs[1:]:
                prod = prod * Expr._E(x)
        return prod
