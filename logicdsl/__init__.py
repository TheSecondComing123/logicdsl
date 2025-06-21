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

from .solver import LogicSolver, Soft

__all__ = [
	"Var",
	"BoolVar",
	"Expr",
        "BoolExpr",
        "named",
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
