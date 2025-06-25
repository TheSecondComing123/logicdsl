from logicdsl import LogicSolver, Var

# Task durations
DUR = {
	"A": 2,
	"B": 1,
	"C": 1,
}

# Start time variables (0..4)
start_A = Var("start_A").in_range(0, 4)
start_B = Var("start_B").in_range(0, 4)
start_C = Var("start_C").in_range(0, 4)

# Variable representing the overall completion time
makespan = Var("makespan").in_range(0, 6)

solver = LogicSolver()

# Tasks must not overlap: either A finishes before B starts or vice versa, etc.
solver.require((start_A + DUR["A"] <= start_B) | (start_B + DUR["B"] <= start_A), "A_vs_B")
solver.require((start_A + DUR["A"] <= start_C) | (start_C + DUR["C"] <= start_A), "A_vs_C")
solver.require((start_B + DUR["B"] <= start_C) | (start_C + DUR["C"] <= start_B), "B_vs_C")

# Guarded constraint: if A starts at time 0, then B must start at or after time 2
solver.require((start_A == 0) >> (start_B >= 2), "guard_A0_then_B>=2")

# Makespan must be at least each task's end time
solver.require(makespan >= start_A + DUR["A"], "end_A")
solver.require(makespan >= start_B + DUR["B"], "end_B")
solver.require(makespan >= start_C + DUR["C"], "end_C")

# Minimize the overall completion time
solver.minimize(makespan)

solution = solver.solve()
print(solver.pretty(solution))
