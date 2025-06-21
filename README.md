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
x = Var("x") << (1, 9)
y = Var("y") << {2, 4, 6, 8}

solver = LogicSolver()
solver.add_variables([x, y])

# hard constraint and optimization objective
solver.require(x + y == 10)
solver.maximize(x * y)

solution = solver.solve()
print(solver.pretty(solution))
```

Running the above prints the best assignment of `x` and `y` that sums to 10 while maximizing their product.

