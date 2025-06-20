# logicdsl/solver.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .core import BoolExpr, Expr


class Soft:
	"""
	Wrapper for a soft constraint with a penalty.
	"""
	
	def __init__(self, bexp: BoolExpr, penalty: int = 1, name: str | None = None):
		self.bexp = bexp
		self.penalty = penalty
		self.name = name or bexp.name
	
	def cost(self, a: Dict[str, Any]) -> int:
		return 0 if self.bexp.satisfied(a) else self.penalty


class LogicSolver:
	"""
	Naïve back-tracking finite-domain solver (good enough for demos).
	"""
	
	def __init__(self, trace: bool = False):
		self.vars: List[Var] = []
		self.hard: List[Tuple[str, BoolExpr]] = []
		self.soft: List[Soft] = []
		self.objectives: List[Tuple[Expr, int]] = []  # sense: +1=max, -1=min
		self.trace = trace
		
		self._best_score: Tuple[int, List[float]] | None = None
		self._best_assignment: Dict[str, Any] | None = None
	
	# ───────────────────────────── API
	def add_variables(self, vs: List[Var]) -> None:
		for v in vs:
			if v.domain is None:
				raise ValueError(f"{v.name} missing domain")
			if v.name not in {x.name for x in self.vars}:
				self.vars.append(v)
	
	def require(self, bexp: BoolExpr, name: str | None = None) -> None:
		self.hard.append((name or bexp.name, bexp))
	
	def prefer(self, bexp: BoolExpr, penalty: int = 1, name: str | None = None) -> None:
		self.soft.append(Soft(bexp, penalty, name))
	
	def maximize(self, expr: Expr) -> None:
		self.objectives.append((expr, 1))
	
	def minimize(self, expr: Expr) -> None:
		self.objectives.append((expr, -1))
	
	# ───────────────────────────── solving internals
	def _score(self, a: Dict[str, Any]) -> Tuple[int, List[float]]:
		penalty = sum(s.cost(a) for s in self.soft)
		obj_vec = [sense * expr.eval(a) for expr, sense in self.objectives]
		return penalty, obj_vec
	
	def _better(self, new, best) -> bool:
		if best is None:
			return True
		if new[0] != best[0]:
			return new[0] < best[0]  # lower penalty
		return new[1] > best[1]  # lexicographic objectives
	
	def _consistent(self, partial: Dict[str, Any]) -> bool:
		for _, rule in self.hard:
			try:
				ok = rule.satisfied(partial)
			except KeyError:  # unassigned vars
				ok = True
			if not ok:
				return False
		return True
	
	def _bt(self, idx: int, assignment: Dict[str, Any]) -> None:
		if idx == len(self.vars):
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
				self._bt(idx + 1, assignment)
		assignment.pop(v.name, None)
	
	def solve(self) -> Dict[str, Any]:
		self._best_score, self._best_assignment = None, None
		self._bt(0, {})
		if self._best_assignment is None:
			raise RuntimeError("No feasible solution")
		penalty, obj_vec = self._best_score
		return {
			"assignment": self._best_assignment,
			"penalty": penalty,
			"objectives": obj_vec,
		}
	
	# ───────────────────────────── convenience
	@staticmethod
	def _pretty_dict(d: Dict[str, Any]) -> str:
		return "\n".join(f"{k:>10} : {v}" for k, v in sorted(d.items()))
	
	def pretty(self, sol: Dict[str, Any]) -> str:
		rows = [self._pretty_dict(sol["assignment"])]
		rows.append(f"  penalty : {sol['penalty']}")
		if self.objectives:
			rows.append(f" objectives : {tuple(sol['objectives'])}")
		return "\n".join(rows)


# ───────────────────────────── quick sanity test
if __name__ == "__main__":
	from .core import Var
	
	x = Var("x") << (1, 9)
	y = Var("y") << {2, 4, 6, 8}
	
	solver = LogicSolver(trace=True)
	solver.add_variables([x, y])
	solver.require(x + y == 10, "sum10")
	solver.maximize(x * y)
	
	sol = solver.solve()
	print("\n=== SOLUTION ===")
	print(solver.pretty(sol))
