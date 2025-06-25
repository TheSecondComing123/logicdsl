# logicdsl/tagset.py
from __future__ import annotations

from typing import Dict, Iterable

from .core import BoolVar, Var
from .constraints import at_least_k, at_least_one, exactly_one, _to_bool
from .solver import LogicSolver


def _at_most_k(xs: Iterable[Var], k: int):
	"""Return BoolExpr enforcing that at most ``k`` of ``xs`` are true."""
	xs_b = [_to_bool(x) for x in xs]
	return at_least_k([~x for x in xs_b], len(xs_b) - k)


class TagSet:
	"""Convenience wrapper for a group of BoolVars."""

	def __init__(self, solver: LogicSolver, tags: Iterable[str], prefix: str = "") -> None:
		self._solver = solver
		self._vars: Dict[str, Var] = {t: BoolVar(prefix + t) for t in tags}

	def var(self, tag: str) -> Var:
		return self._vars[tag]

	def vars(self) -> Dict[str, Var]:
		return self._vars

	def enforce_exactly_one(self) -> None:
		self._solver.require(exactly_one(list(self._vars.values())))

	def enforce_at_least_one(self) -> None:
		self._solver.require(at_least_one(list(self._vars.values())))

	def enforce_at_most(self, k: int) -> None:
		self._solver.require(_at_most_k(list(self._vars.values()), k))
