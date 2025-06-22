# logicdsl/__init__.py
"""
Public surface of the LogicDSL package.
"""

from .constraints import (
        at_least_one,
        at_most_one,
        at_least_k,
        distinct,
        exactly_one,
        exactly_k,
        exists,
        forall,
        sum_of,
        product_of,
)
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

__all__ = [
	"Var",
	"BoolVar",
	"Expr",
        "BoolExpr",
        "named",
        "when",
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
        "Soft",
]
