class Expr:
	def __init__(self, fn):
		self._f = fn  # fn : assignment -> number
	
	def eval(self, a):
		return self._f(a)
	
	# internal: coerce plain numbers or Var into Expr
	@staticmethod
	def _E(v):
		if isinstance(v, Expr):
			return v
		if isinstance(v, Var):
			return v.expr
		if isinstance(v, (int, float)):
			return Expr(lambda a, val=v: val)
		raise TypeError(f"Unsupported operand type: {type(v)}")
	
	# helper building binary operator closures
	@staticmethod
	def _bin(pair, op):
		left, right = pair
		return Expr(lambda a, l=left, r=right: op(l.eval(a), r.eval(a)))
	
	# arithmetic operators
	def __add__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x + y)
	
	__radd__ = __add__
	
	def __sub__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x - y)
	
	def __rsub__(self, o):
		o = Expr._E(o)
		return Expr._bin((o, self), lambda x, y: x - y)
	
	def __mul__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x * y)
	
	__rmul__ = __mul__
	
	def __truediv__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x / y)
	
	def __floordiv__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x // y)
	
	def __pow__(self, o):
		o = Expr._E(o)
		return Expr._bin((self, o), lambda x, y: x ** y)
	
	def __neg__(self):
		return Expr(lambda a, s=self: -s.eval(a))
	
	# absolute value via method so we don't shadow __abs__
	def abs(self):
		return Expr(lambda a, s=self: abs(s.eval(a)))
	
	# comparisons -> BoolExpr
	def _cmp(self, o, op):
		o = Expr._E(o)
		return BoolExpr(lambda a, s=self: op(s.eval(a), o.eval(a)))
	
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


class BoolExpr:
	def __init__(self, fn, name=None):
		self._f = fn
		self.name = name or "<anon>"
	
	def satisfied(self, a):
		return self._f(a)
	
	# logical composition
	def __and__(self, o):
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) and t.satisfied(a))
	
	__rand__ = __and__
	
	def __or__(self, o):
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) or t.satisfied(a))
	
	__ror__ = __or__
	
	def __invert__(self):
		return BoolExpr(lambda a, s=self: not s.satisfied(a))
	
	def __xor__(self, o):
		return BoolExpr(lambda a, s=self, t=o: s.satisfied(a) ^ t.satisfied(a))
	
	# implication: self >> o
	def __rshift__(self, o):
		return BoolExpr(lambda a, s=self, t=o: (not s.satisfied(a)) or t.satisfied(a))
	
	def __repr__(self):
		return f"BoolExpr({self.name})"


class Var:
	def __init__(self, name):
		self.name = name
		self.domain = None
		self.expr = Expr(lambda a, n=name: a[n])
	
	# domain binding through << or .in_range
	def __lshift__(self, spec):
		if isinstance(spec, tuple) and len(spec) == 2:
			lo, hi = spec
			self.domain = list(range(lo, hi + 1))
		elif isinstance(spec, (list, set, range)):
			self.domain = list(spec)
		else:
			raise ValueError(f"Bad domain for {self.name}")
		return self
	
	def in_range(self, lo, hi):
		self.domain = list(range(lo, hi + 1))
		return self
	
	# delegate arithmetic/comparisons to Expr
	def __getattr__(self, item):
		# allow getattr for dunder arithmetic (e.g. __add__) to propagate
		if hasattr(self.expr, item):
			return getattr(self.expr, item)
		raise AttributeError(item)
	
	# arithmetic
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
	
	def __pow__(self, o):
		return self.expr ** o
	
	def __neg__(self):
		return -self.expr
	
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
	
	def __repr__(self):
		return f"Var({self.name}:{self.domain})"


def BoolVar(name):
	return Var(name) << {0, 1}


# helper predicates
def distinct(vs):
	return BoolExpr(
		lambda a, _vs=vs: len({a[v.name] for v in _vs}) == len(_vs), "distinct"
	)


def at_least_one(xs):
	return fold_or(xs)


def at_most_one(xs):
	return fold_and(
		[~(p & q) for i, p in enumerate(xs) for q in xs[i + 1:]]
	)


def exactly_one(xs):
	return at_least_one(xs) & at_most_one(xs)


def forall(vs, f):
	return fold_and([f(v) for v in vs])


def exists(vs, f):
	return fold_or([f(v) for v in vs])


def fold_and(xs):
	if not xs:
		return BoolExpr(lambda a: True, "true")
	it = iter(xs)
	r = next(it)
	for x in it:
		r = r & x
	return r


def fold_or(xs):
	if not xs:
		return BoolExpr(lambda a: False, "false")
	it = iter(xs)
	r = next(it)
	for x in it:
		r = r | x
	return r


class Soft:
	def __init__(self, bexp, penalty=1, name=None):
		self.bexp = bexp
		self.penalty = penalty
		self.name = name or bexp.name
	
	def cost(self, a):
		return 0 if self.bexp.satisfied(a) else self.penalty


class LogicSolver:
	def __init__(self, trace=False):
		self.vars = []
		self.hard = []
		self.soft = []
		self.objectives = []  # list of (Expr, sense) where sense=1 max, -1 min
		self.trace = trace
		self._best = None
		self._best_assignment = None
	
	# public API
	def add_variables(self, vs):
		for v in vs:
			if v.domain is None:
				raise ValueError(f"{v.name} missing domain")
			if v.name not in {x.name for x in self.vars}:
				self.vars.append(v)
	
	def require(self, bexp, name=None):
		self.hard.append((name or bexp.name, bexp))
	
	def prefer(self, bexp, penalty=1, name=None):
		self.soft.append(Soft(bexp, penalty, name))
	
	def maximize(self, expr):
		self.objectives.append((expr, 1))
	
	def minimize(self, expr):
		self.objectives.append((expr, -1))
	
	# scoring
	def _score(self, a):
		penalty = sum(s.cost(a) for s in self.soft)
		obj_vec = [sense * expr.eval(a) for expr, sense in self.objectives]
		return (penalty, obj_vec)
	
	def _better(self, new_score, best_score):
		if best_score is None:
			return True
		# lower penalty wins
		if new_score[0] != best_score[0]:
			return new_score[0] < best_score[0]
		# lexicographic compare objective vector
		return new_score[1] > best_score[1]
	
	# early pruning
	def _consistent(self, partial):
		for _, rule in self.hard:
			try:
				ok = rule.satisfied(partial)
			except KeyError:
				ok = True  # rule not decidable yet
			if not ok:
				return False
		return True
	
	def _bt(self, idx, assignment):
		if idx == len(self.vars):  # full assignment
			score = self._score(assignment)
			if self._better(score, self._best):
				self._best = score
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
	
	def solve(self):
		self._best, self._best_assignment = None, None
		self._bt(0, {})
		if self._best_assignment is None:
			raise RuntimeError("No feasible solution")
		return {
			"assignment": self._best_assignment,
			"penalty": self._best[0],
			"objectives": [
				sense * obj for (obj, sense), obj in zip(self.objectives, self._best[1])
			],
		}
	
	def pretty(self, sol):
		rows = [f"{k:>10} : {v}" for k, v in sorted(sol["assignment"].items())]
		rows.append(f"  penalty : {sol['penalty']}")
		if self.objectives:
			rows.append(f" objectives : {tuple(sol['objectives'])}")
		return "".join(rows)


# self-test only triggers when run as script, not on import
if __name__ == '__main__':
	x = Var('x') << (1, 9)
	y = Var('y') << {2, 4, 6, 8}
	s = LogicSolver(trace=True)
	s.add_variables([x, y])
	s.require(x + y == 10)
	s.maximize(x * y)
	print(s.pretty(s.solve()))
