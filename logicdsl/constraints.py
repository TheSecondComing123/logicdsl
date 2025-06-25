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


def at_least_k(xs: List[BoolExpr | Var], k: int) -> BoolExpr:
	"""Return a BoolExpr satisfied when at least ``k`` of ``xs`` are true."""
	xs_b = [_to_bool(x) for x in xs]
	
	if k <= 0:
		return _fold_and([])
	if k > len(xs_b):
		return _fold_or([])
	
	from itertools import combinations
	
	clauses = [_fold_and(list(combo)) for combo in combinations(xs_b, k)]
	return _fold_or(clauses)


def exactly_k(xs: List[BoolExpr | Var], k: int) -> BoolExpr:
	"""Return a BoolExpr satisfied when exactly ``k`` of ``xs`` are true."""
	xs_b = [_to_bool(x) for x in xs]
	n = len(xs_b)
	
	if k < 0 or k > n:
		return _fold_or([])
	if k == 0:
		return _fold_and([~x for x in xs_b])
	if k == n:
		return _fold_and(xs_b)
	
	return at_least_k(xs_b, k) & at_least_k([~x for x in xs_b], n - k)


class ForAll:
	"""Quantifier representing conjunction over a set of variables."""
	
	def __init__(self, vs: Iterable[Var]):
		self.vs = list(vs)
	
	def require(self, f) -> BoolExpr:
		return _fold_and([f(v) for v in self.vs])
	
	def __rshift__(self, f) -> BoolExpr:
		return self.require(f)


class Exists:
	"""Quantifier representing disjunction over a set of variables."""
	
	def __init__(self, vs: Iterable[Var]):
		self.vs = list(vs)
	
	def require(self, f) -> BoolExpr:
		return _fold_or([f(v) for v in self.vs])
	
	def __rshift__(self, f) -> BoolExpr:
		return self.require(f)


def forall(vs: Iterable[Var], f=None) -> BoolExpr | ForAll:
	if f is None:
		return ForAll(vs)
	return ForAll(vs).require(f)


def exists(vs: Iterable[Var], f=None) -> BoolExpr | Exists:
	if f is None:
		return Exists(vs)
	return Exists(vs).require(f)


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
