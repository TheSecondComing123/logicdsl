# logicdsl/core.py
from __future__ import annotations

from typing import Any, Callable, Dict, Set


# ─────────────────────────────────────────────────────────────────────────────
class Expr:
	"""
	Arithmetic expression node built from Vars / literals.
	"""
	
	def __init__(self, fn: Callable[[Dict[str, Any]], float], vars: Set["Var"] | None = None):
		self._f = fn  # fn : assignment → number
		self._vars: Set[Var] = set(vars or [])
	
	# --------------------------------------------------------------------- eval
	def eval(self, a: Dict[str, Any]) -> float:
		return self._f(a)
	
	# ------------------------------------------------------------------ helpers
	@staticmethod
	def _E(v: Any) -> "Expr":  # coerce Var/int/float → Expr
		if isinstance(v, Expr):
		        return v
		if isinstance(v, Var):
		        return v.expr
		if isinstance(v, (int, float)):
		        return Expr(lambda a, val=v: val, vars=set())
		raise TypeError(f"Unsupported operand type: {type(v)}")
	
	@staticmethod
	def _bin(pair: tuple["Expr", "Expr"], op):
		l, r = pair
		return Expr(lambda a, _l=l, _r=r: op(_l.eval(a), _r.eval(a)), vars=l._vars | r._vars)
	
	# ------------------------------------------------------------ arithmetic ops
	def __add__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x + y)
	
	__radd__ = __add__
	
	def __sub__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x - y)
	
	def __rsub__(self, o):
		o = Expr._E(o); return Expr._bin((o, self), lambda x, y: x - y)
	
	def __mul__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x * y)
	
	__rmul__ = __mul__
	
	def __truediv__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x / y)
	
	def __floordiv__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x // y)
	
	# NEW: modulo
	def __mod__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x % y)
	
	def __rmod__(self, o):
		o = Expr._E(o); return Expr._bin((o, self), lambda x, y: x % y)
	
	def __pow__(self, o):
		o = Expr._E(o); return Expr._bin((self, o), lambda x, y: x ** y)
	
	def __neg__(self):
		return Expr(lambda a, s=self: -s.eval(a), vars=self._vars)
	def __abs__(self):
		return self.abs()

	def abs(self):
		return Expr(lambda a, s=self: abs(s.eval(a)), vars=self._vars)
	
	# ------------------------------------------------------- comparisons → BoolE
	def _cmp(self, o, op):
		o = Expr._E(o)
		return BoolExpr(lambda a, s=self: op(s.eval(a), o.eval(a)), vars=self._vars | o._vars)
	
	def __eq__(self, o):
		return self._cmp(o, lambda x, y: x == y)
	
	def __ne__(self, o):
		return self._cmp(o, lambda x, y: x != y)
	
	def __lt__(self, o):
		return self._cmp(o, lambda x, y: x < y)
	
	def __le__(self, o):
		return self._cmp(o, lambda x, y: x <= y)
	
	def __gt__(self, o):
		return self._cmp(o, lambda x, y: x > y)
	
	def __ge__(self, o):
		return self._cmp(o, lambda x, y: x >= y)


# ─────────────────────────────────────────────────────────────────────────────
class BoolExpr:
	"""
	Boolean expression node (built from comparisons or logic ops).
	"""
	
	def __init__(self, fn: Callable[[Dict[str, Any]], bool], name: str | None = None, vars: Set["Var"] | None = None):
		self._f = fn
		self.name = name or "<anon>"
		self._vars: Set[Var] = set(vars or [])
	
	def satisfied(self, a: Dict[str, Any]) -> bool:
		return self._f(a)
	
	# ---------------------------- helper: coerce BoolVar (domain {0,1}) to Bool
	@staticmethod
	def _B(x):
		from .core import Var  # local to avoid circular import
		if isinstance(x, BoolExpr):
			return x
		if isinstance(x, Var) and x.domain == [0, 1]:
			return x == 1
		raise TypeError("Expected BoolExpr or BoolVar-compatible Var")
	
	# --------------------------------------------------------- logic operators
	def __and__(self, o):
		o = BoolExpr._B(o)
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) and t.satisfied(a), vars=self._vars | o._vars)
	
	__rand__ = __and__
	
	def __or__(self, o):
		o = BoolExpr._B(o)
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) or t.satisfied(a), vars=self._vars | o._vars)
	
	__ror__ = __or__
	
	def __invert__(self):
		return BoolExpr(lambda a, s=self: not s.satisfied(a), vars=self._vars)
	
	def __xor__(self, o):
		o = BoolExpr._B(o)
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) ^ t.satisfied(a), vars=self._vars | o._vars)
	
	# implication  (self >> o)
	def __rshift__(self, o):
		o = BoolExpr._B(o)
		return BoolExpr(lambda a, s=self, t=o: (not s.satisfied(a)) or t.satisfied(a), vars=self._vars | o._vars)

	def named(self, name: str) -> "BoolExpr":
		"""Return a copy of this BoolExpr with a different name."""
		return BoolExpr(self._f, name, vars=self._vars)

	def __repr__(self) -> str:
		return f"BoolExpr({self.name})"


# ─────────────────────────────────────────────────────────────────────────────
class Var:
	"""
	Finite-domain variable.  Bind its domain with  `<< (lo,hi)` or `.in_range`.
	"""
	
	def __init__(self, name: str):
		self.name = name
		self.domain = None
		self.expr = Expr(lambda a, n=name: a[n], vars={self})

	def __hash__(self) -> int:
		return hash(self.name)
	
	# ------------------------------------------------------- domain assignment
	def __lshift__(self, spec):
		if isinstance(spec, tuple) and len(spec) == 2:
			lo, hi = spec
			self.domain = list(range(lo, hi + 1))
		elif isinstance(spec, (list, set, range)):
			self.domain = list(spec)
		else:
			raise ValueError(f"Bad domain for {self.name}")
		return self
	
	def in_range(self, lo: int, hi: int):
		self.domain = list(range(lo, hi + 1))
		return self
	
	# ------------------------------------------------ delegate to Expr for math
	def __getattr__(self, k):
		if hasattr(self.expr, k):
			return getattr(self.expr, k)
		raise AttributeError(k)
	
	# arithmetic mirrors Expr
	def __add__(self, o):
		return self.expr + o
	
	__radd__ = __add__
	
	def __sub__(self, o):
		return self.expr - o
	
	def __rsub__(self, o):
		return o - self.expr
	
	def __mul__(self, o):
		return self.expr * o
	
	__rmul__ = __mul__
	
	def __truediv__(self, o):
		return self.expr / o
	
	def __floordiv__(self, o):
		return self.expr // o
	
	# NEW modulo forwarders
	def __mod__(self, o):
		return self.expr % o
	
	def __rmod__(self, o):
		return o % self.expr
	
	def __pow__(self, o):
		return self.expr ** o
	
	def __neg__(self):
		return -self.expr
	def __abs__(self):
		return abs(self.expr)
	
	# comparisons
	def __eq__(self, o):
		return self.expr == o
	
	def __ne__(self, o):
		return self.expr != o
	
	def __lt__(self, o):
		return self.expr < o
	
	def __le__(self, o):
		return self.expr <= o
	
	def __gt__(self, o):
		return self.expr > o
	
	def __ge__(self, o):
		return self.expr >= o
	
	def __repr__(self) -> str:
		return f"Var({self.name}:{self.domain})"


# ---------------------------------------------------------------- convenience
def BoolVar(name: str) -> Var:
	"""
	Convenience 0/1 variable usable directly in BoolExpr logic.
	"""
	return Var(name) << {0, 1}
