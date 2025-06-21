from logicdsl import LogicSolver, Var


def demo():
        """Run a tiny solver demo."""
        x = Var("x") << (1, 9)
        y = Var("y") << {2, 4, 6, 8}
        solver = LogicSolver(trace=True)
        solver.add_variables([x, y])
        solver.require(x + y == 10, "sum10")
        solver.maximize(x * y)
        result = solver.solve()
        print(solver.pretty(result))


if __name__ == "__main__":
        demo()
