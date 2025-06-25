# logicdsl/__init__.py
"""
Public surface of the LogicDSL package.
"""

from .constraints import (at_least_k, at_least_one, at_most_one, distinct, exactly_k, exactly_one, exists, forall,
                          product_of, sum_of)
from .core import BoolExpr, BoolVar, Expr, Var


def named(expr: BoolExpr, name: str) -> BoolExpr:
	"""Return a BoolExpr with the provided name."""
	return expr.named(name)


class _ImplicationBuilder:
	"""Helper object returned by :func:`when` to chain ``.then``."""
	
	def __init__(self, cond: BoolExpr) -> None:
		self._cond = cond
	
	def then(self, expr: BoolExpr | Var) -> BoolExpr:
		"""Return implication ``cond >> expr``."""
		return self._cond >> BoolExpr._B(expr)


def when(cond: BoolExpr | Var) -> _ImplicationBuilder:
	"""Convenience builder for implication expressions.

	``when(p).then(q)`` is equivalent to ``p >> q`` but can be useful when
	constructing conditions dynamically.
	"""
	return _ImplicationBuilder(BoolExpr._B(cond))


from .solver import LogicSolver, Soft
from .z3solver import Z3Solver


class _LetBuilder:
	"""Helper returned by :func:`let` to pass a temporary expression."""
	
	def __init__(self, expr: Expr | Var | int | float) -> None:
		self._expr = Expr._E(expr)
	
	def then(self, f):
		"""Apply ``f`` to the stored expression and return the result."""
		return f(self._expr)


def let(expr: Expr | Var | int | float) -> _LetBuilder:
	"""Convenience helper for applying a predicate to ``expr``.

	``let(x + y).then(lambda t: t < 10)`` is equivalent to
	``(lambda t: t < 10)(x + y)`` but can improve readability when
	constructing larger expressions.
	"""
	return _LetBuilder(expr)


__all__ = [
	"Var",
	"BoolVar",
	"Expr",
	"BoolExpr",
	"named",
	"when",
	"let",
	# constraints
	"distinct",
	"at_least_one",
	"at_most_one",
	"at_least_k",
	"exactly_one",
	"exactly_k",
	"forall",
	"exists",
	"sum_of",
	"product_of",
	# solver
	"LogicSolver",
	"Z3Solver",
	"Soft",
]
