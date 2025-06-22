# LogicDSL

LogicDSL is a tiny domain-specific language for solving finite-domain logic problems in Python. It lets you declare integer variables, compose arithmetic and logical expressions, and search for assignments that satisfy a set of constraints.

## Installation

Install the project in editable mode so that you can run the examples directly:

```bash
pip install -e .
```

## Quick Example

```python
from logicdsl import LogicSolver, Var

# define variables with finite domains
x = Var("x").in_range(0.0, 1.0, step=0.1)
y = Var("y") << {2, 4, 6, 8}

solver = LogicSolver()

# variables used in constraints are added automatically

# hard constraint and optimization objective
solver.require(x + y == 10)
solver.maximize(x * y)

solution = solver.solve()
print(solver.pretty(solution))
```

Running the above prints the best assignment of `x` and `y` that sums to 10 while maximizing their product.

Variables do not need to be registered explicitly; the solver automatically discovers all variables that appear in constraints or objectives.

### Objective Modes

By default the solver optimizes objectives lexicographically.  To combine
multiple objectives using a weighted sum pass ``objective_mode="sum"`` when
creating the solver.  Each call to ``maximize``/``minimize`` accepts an optional
``weight`` parameter used in the sum.

```python
solver = LogicSolver(objective_mode="sum")
solver.maximize(x, weight=1)
solver.maximize(y, weight=2)
```

### Soft Constraints

Use `prefer` to add a soft constraint with an optional penalty and weight. The
weight influences the search when using `objective_mode="sum"`.

```python
solver.prefer(x > 5, penalty=1, weight=5.0)
```

### Quantifiers

`forall` and `exists` still accept a list of variables and a lambda
function as before.  When called with only the variable list they now
return quantifier objects that accept a predicate using `>>` or
`.require()`.

```python
xs = [Var(f"x{i}") << (1, 3) for i in range(3)]

# traditional
forall(xs, lambda v: v <= 3)

# new style
forall(xs) >> (lambda v: v <= 3)
exists(xs).require(lambda v: v == 2)
```

### When/Then Helper

``when(cond).then(expr)`` builds an implication ``cond >> expr``.  This can make
dynamic constructions a bit clearer.

```python
p = BoolVar("p")
q = BoolVar("q")

rule = when(p).then(q)  # equivalent to p >> q
```

### Let Helper

`let(expr).then(lambda t: predicate)` simply passes a temporary expression to
a lambda function.  This is handy when you want to name an intermediate result
inside a constraint without creating a separate variable.

```python
x = Var("x") << (0, 5)
y = Var("y") << (0, 5)

constraint = let(x + y).then(lambda t: t < 7)
```

