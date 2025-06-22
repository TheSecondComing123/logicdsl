from logicdsl import LogicSolver, Var, distinct

x = Var("x").in_range(0.0, 1.0, step=0.1)
y = Var("y") << {2, 4, 6, 8}
z = Var("z").in_range(0, 5)
a, b, c = [Var(v) << (1, 3) for v in "abc"]

S = LogicSolver()
# variables used in constraints are added automatically

S.require(x + y == 10)
S.require((x != y) & (y < 9))
S.require(~(z == 3))
S.require(distinct([a, b, c]))
S.require((x > 5) >> (y < 5))

S.prefer(z != 0, penalty=3)
S.prefer((a + b + c) >= 5)

S.maximize(x * y - z)

solution = S.solve()
print(S.pretty(solution))
