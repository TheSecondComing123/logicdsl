# logicdsl/__init__.py
"""
Public surface of the LogicDSL package.
"""

from .constraints import (at_least_one, at_most_one, distinct, exactly_one, exists, forall)
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
	"exactly_one",
	"forall",
	"exists",
	# solver
	"LogicSolver",
	"Soft",
]
