# logicdsl/solver.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple, Set
import time

from .core import BoolExpr, Expr, Var


def collect_vars(expr: Expr | BoolExpr) -> List[Var]:
	"""Return vars referenced in an expression tree in deterministic order."""
	vars_set: Set[Var] = set(getattr(expr, "_vars", set()))
	return sorted(vars_set, key=lambda v: v.name)


class Soft:
	"""
	Wrapper for a soft constraint with a penalty and optional weight.
	"""
	
	def __init__(self, bexp: BoolExpr, penalty: int = 1, weight: float = 1.0, name: str | None = None):
		self.bexp = bexp
		self.penalty = penalty
		self.weight = float(weight)
		self.name = name or bexp.name
	
	def cost(self, a: Dict[str, Any]) -> int:
		return 0 if self.bexp.satisfied(a) else self.penalty

	def weighted_cost(self, a: Dict[str, Any]) -> float:
		return 0.0 if self.bexp.satisfied(a) else self.penalty * self.weight


class LogicSolver:
	"""
	Naïve back-tracking finite-domain solver (good enough for demos).
	"""

	def __init__(self, trace: bool = False, objective_mode: str = "lex"):
		self.vars: List[Var] = []
		self.hard: List[Tuple[str, BoolExpr]] = []
		self.soft: List[Soft] = []
		# objective tuple: (expression, sense, weight)
		self.objectives: List[Tuple[Expr, int, float]] = []
		self.trace = trace
		self.objective_mode = objective_mode

		if objective_mode not in {"lex", "sum"}:
			raise ValueError("objective_mode must be 'lex' or 'sum'")

		self._best_score: Tuple[int, float | List[float]] | None = None
		self._best_assignment: Dict[str, Any] | None = None
		self._failed_constraints: Set[str] = set()

	def _ensure_vars(self, expr: Expr | BoolExpr) -> None:
		"""Collect variables from an expression and register them."""
		for v in collect_vars(expr):
			if v.domain is None:
				raise ValueError(f"{v.name} missing domain")
			if v.name not in {x.name for x in self.vars}:
				self.vars.append(v)
	
	# ───────────────────────────── API
	def add_variables(self, vs: List[Var]) -> None:
		for v in vs:
			if v.domain is None:
				raise ValueError(f"{v.name} missing domain")
			if v.name not in {x.name for x in self.vars}:
				self.vars.append(v)
	
	def require(self, bexp: BoolExpr, name: str | None = None) -> None:
		self._ensure_vars(bexp)
		self.hard.append((name or bexp.name, bexp))
	
	def prefer(self, bexp: BoolExpr, penalty: int = 1, weight: float = 1.0, name: str | None = None) -> None:
		self._ensure_vars(bexp)
		self.soft.append(Soft(bexp, penalty, weight, name))
	
	def maximize(self, expr: Expr, weight: float = 1.0) -> None:
		"""Add an objective to maximize ``expr`` with optional ``weight``."""
		self._ensure_vars(expr)
		self.objectives.append((expr, 1, float(weight)))

	def minimize(self, expr: Expr, weight: float = 1.0) -> None:
		"""Add an objective to minimize ``expr`` with optional ``weight``."""
		self._ensure_vars(expr)
		self.objectives.append((expr, -1, float(weight)))
	
	# ───────────────────────────── solving internals
	def _score(self, a: Dict[str, Any]) -> Tuple[int, float | List[float]]:
		"""Return (penalty, objective score)."""
		penalty = sum(s.cost(a) for s in self.soft)
		if self.objective_mode == "sum":
			soft_cost = sum(s.weight * s.cost(a) for s in self.soft)
			score = (
				sum(
					weight * sense * expr.eval(a)
					for expr, sense, weight in self.objectives
				) - soft_cost
			)
			return penalty, score

		obj_vec = [sense * expr.eval(a) for expr, sense, _ in self.objectives]
		return penalty, obj_vec
	def _better(self, new, best) -> bool:
		if best is None:
			return True
		if new[0] != best[0]:
			return new[0] < best[0]	 # lower penalty

		if self.objective_mode == "sum":
			return new[1] > best[1]

		return new[1] > best[1]	 # lexicographic objectives
	
	def _consistent(self, partial: Dict[str, Any]) -> bool:
		for name, rule in self.hard:
			try:
				ok = rule.satisfied(partial)
			except KeyError:  # unassigned vars
				ok = True
			if not ok:
				self._failed_constraints.add(name)
				return False
		return True
	
	def _bt(
		self,
		idx: int,
		assignment: Dict[str, Any],
		solutions: List[Dict[str, Any]] | None = None,
		limit: int | None = None,
		start: float | None = None,
		timeout: float | None = None,
	) -> None:
		# treat a zero timeout as an immediate expiration
		if start is not None and timeout is not None and time.monotonic() - start >= timeout:
			raise TimeoutError()
		if solutions is not None and limit is not None and len(solutions) >= limit:
			return

		if idx == len(self.vars):
			if solutions is not None:
				penalty, obj_val = self._score(assignment)
				entry = {
					"assignment": assignment.copy(),
					"penalty": penalty,
				}
				if self.objective_mode == "sum":
					entry["objective"] = obj_val
				else:
					entry["objectives"] = obj_val
				solutions.append(entry)
				return

			score = self._score(assignment)
			if self._better(score, self._best_score):
				self._best_score = score
				self._best_assignment = assignment.copy()
				if self.trace:
					print("NEW BEST", score, self._best_assignment)
			return
		
		v = self.vars[idx]
		for val in v.domain:
			assignment[v.name] = val
			if self._consistent(assignment):
				self._bt(idx + 1, assignment, solutions, limit, start, timeout)
				if solutions is not None and limit is not None and len(solutions) >= limit:
					assignment.pop(v.name, None)
					return
		assignment.pop(v.name, None)
	
	def solve(self, timeout: float | None = None) -> Dict[str, Any]:
		"""Search for the best assignment within the optional timeout."""
		self._best_score, self._best_assignment = None, None
		self._failed_constraints = set()
		start = time.monotonic()
		self._bt(0, {}, None, None, start, timeout)
		if self._best_assignment is None:
			raise RuntimeError("No feasible solution")
		penalty, obj_val = self._best_score
		result = {
			"assignment": self._best_assignment,
			"penalty": penalty,
		}
		if self.objective_mode == "sum":
			result["objective"] = obj_val
		else:
			result["objectives"] = obj_val
		return result

	def all_solutions(self, limit: int | None = None, timeout: float | None = None) -> List[Dict[str, Any]]:
		"""Return all feasible assignments up to ``limit`` or until the timeout expires."""
		solutions: List[Dict[str, Any]] = []
		start = time.monotonic()
		try:
			self._bt(0, {}, solutions, limit, start, timeout)
		except TimeoutError:
			pass
		return solutions

	def why_unsat(self) -> List[str]:
		"""Return names of hard constraints that failed during the last search."""
		return sorted(self._failed_constraints)
	
	# ───────────────────────────── convenience
	@staticmethod
	def _pretty_dict(d: Dict[str, Any]) -> str:
		return "\n".join(f"{k:>10} : {v}" for k, v in sorted(d.items()))
	
	def pretty(self, sol: Dict[str, Any]) -> str:
		rows = [self._pretty_dict(sol["assignment"])]
		rows.append(f"	penalty : {sol['penalty']}")
		if self.objectives:
			if self.objective_mode == "sum":
				rows.append(f"	objective : {sol['objective']}")
			else:
				rows.append(f" objectives : {tuple(sol['objectives'])}")
		return "\n".join(rows)


# ───────────────────────────── quick sanity test
if __name__ == "__main__":
	from .core import Var
	
	x = Var("x") << (1, 9)
	y = Var("y") << {2, 4, 6, 8}
	
	solver = LogicSolver(trace=True)
	# variables used in constraints are added automatically
	solver.require(x + y == 10, "sum10")
	solver.maximize(x * y)
	
	sol = solver.solve()
	print("\n=== SOLUTION ===")
	print(solver.pretty(sol))
