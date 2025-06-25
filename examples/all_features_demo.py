from logicdsl import BoolVar, LogicSolver, when, at_least_one

N = 3
houses = range(N)

colors = ['red', 'green', 'blue']
nations = ['brit', 'swede', 'norwegian']
drinks = ['milk', 'tea', 'water']

solver = LogicSolver()

# Create variables: house x attribute → BoolVar
def make_vars(tags):
    return {(h, t): BoolVar(f"{t}_{h}") for h in houses for t in tags}

color_vars = make_vars(colors)
nation_vars = make_vars(nations)
drink_vars = make_vars(drinks)

# Each tag (e.g. 'red') appears in exactly one house
def add_exactly_one_group(group_vars):
    for t in set(k[1] for k in group_vars):
        vars_for_tag = [group_vars[(h, t)] for h in houses]
        solver.require(at_least_one(vars_for_tag), name=f"{t}_somewhere")
        for i in range(len(vars_for_tag)):
            for j in range(i + 1, len(vars_for_tag)):
                solver.require(~((vars_for_tag[i] == 1) & (vars_for_tag[j] == 1)),
                               name=f"{t}_unique_{i}_{j}")

# Each house has exactly one of each tag group (e.g. one color per house)
def add_exactly_one_per_house(group_vars):
    for h in houses:
        vars_for_house = [group_vars[(h, t)] for t in set(k[1] for k in group_vars)]
        solver.require(at_least_one(vars_for_house), name=f"house_{h}_some_tag")
        for i in range(len(vars_for_house)):
            for j in range(i + 1, len(vars_for_house)):
                solver.require(~((vars_for_house[i] == 1) & (vars_for_house[j] == 1)),
                               name=f"house_{h}_tag_unique_{i}_{j}")

# Apply the structure constraints
for group in [color_vars, nation_vars, drink_vars]:
    add_exactly_one_group(group)
    add_exactly_one_per_house(group)

# Logic clues
for h in houses:
    # 1. The Brit lives in the red house.
    solver.require(when(nation_vars[(h, 'brit')] == 1).then(color_vars[(h, 'red')] == 1))

    # 2. The Swede drinks tea.
    solver.require(when(nation_vars[(h, 'swede')] == 1).then(drink_vars[(h, 'tea')] == 1))

# 3. The green house is directly to the right of the red house.
for h in range(N - 1):
    solver.require(when(color_vars[(h, 'red')] == 1).then(color_vars[(h + 1, 'green')] == 1))

# 4. The person in the middle house drinks milk.
solver.require(drink_vars[(1, 'milk')] == 1)

# 5. The Norwegian lives in the first house.
solver.require(nation_vars[(0, 'norwegian')] == 1)

# Solve it
solution = solver.solve()
print(solver.pretty(solution))
