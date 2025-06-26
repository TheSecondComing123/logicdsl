from __future__ import annotations

from typing import Any, Dict, List, Tuple, Set

import z3

from .core import BoolExpr, Expr, Var
from .solver import Soft, collect_vars


class Z3Solver:
    """Z3 backend solver mirroring :class:`LogicSolver`'s API."""

    def __init__(self, trace: bool = False, objective_mode: str = "lex") -> None:
        self.vars: List[Var] = []
        self.hard: List[Tuple[str, BoolExpr]] = []
        self.soft: List[Soft] = []
        self.objectives: List[Tuple[Expr, int, float]] = []
        self.trace = trace
        self.objective_mode = objective_mode
        if objective_mode not in {"lex", "sum"}:
            raise ValueError("objective_mode must be 'lex' or 'sum'")

        self._var_is_int: Dict[str, bool] = {}
        self._failed_constraints: Set[str] = set()

    def _ensure_vars(self, expr: Expr | BoolExpr) -> None:
        for v in collect_vars(expr):
            if v.domain is None:
                raise ValueError(f"{v.name} missing domain")
            if v.name not in {x.name for x in self.vars}:
                self.vars.append(v)

    def add_variables(self, vs: List[Var]) -> None:
        for v in vs:
            if v.domain is None:
                raise ValueError(f"{v.name} missing domain")
            if v.name not in {x.name for x in self.vars}:
                self.vars.append(v)

    def require(self, bexp: BoolExpr, name: str | None = None) -> None:
        self._ensure_vars(bexp)
        self.hard.append((name or bexp.name, bexp))

    def require_all(self, pred, vs) -> None:
        """Apply ``pred`` to each variable and add the resulting constraints."""
        for v in vs:
            self.require(pred(v))

    def require_if(self, cond: BoolExpr | Var, expr: BoolExpr | Var, name: str | None = None) -> None:
        """Add implication ``cond >> expr`` as a hard constraint."""
        self.require(BoolExpr._B(cond) >> BoolExpr._B(expr), name)

    def prefer(self, bexp: BoolExpr, penalty: int = 1, weight: float = 1.0, name: str | None = None) -> None:
        self._ensure_vars(bexp)
        self.soft.append(Soft(bexp, penalty, weight, name))

    def maximize(self, expr: Expr, weight: float = 1.0) -> None:
        self._ensure_vars(expr)
        self.objectives.append((expr, 1, float(weight)))

    def minimize(self, expr: Expr, weight: float = 1.0) -> None:
        self._ensure_vars(expr)
        self.objectives.append((expr, -1, float(weight)))

    def _make_z3_vars(self) -> Dict[str, z3.ExprRef]:
        mapping: Dict[str, z3.ExprRef] = {}
        self._var_is_int = {}
        for v in self.vars:
            is_int = all(float(val).is_integer() for val in v.domain)
            self._var_is_int[v.name] = is_int
            mapping[v.name] = z3.Int(v.name) if is_int else z3.Real(v.name)
        return mapping

    def _const(self, name: str, val: Any) -> z3.ExprRef:
        if self._var_is_int.get(name, True):
            return z3.IntVal(int(val))
        return z3.RealVal(float(val))

    def _model_value(self, model: z3.ModelRef, expr: z3.ExprRef) -> Any:
        val = model.eval(expr, model_completion=True)
        if isinstance(val, z3.IntNumRef):
            return val.as_long()
        if isinstance(val, z3.RatNumRef):
            num = val.numerator_as_long()
            den = val.denominator_as_long()
            return num / den
        return val

    def _build_penalty_expr(self, env: Dict[str, z3.ExprRef]) -> z3.ArithRef:
        terms = [z3.If(s.bexp.satisfied(env), 0, s.penalty) for s in self.soft]
        return z3.Sum(terms) if terms else z3.IntVal(0)

    def _build_objective_expr(self, env: Dict[str, z3.ExprRef]) -> z3.ArithRef:
        parts = [weight * sense * expr.eval(env) for expr, sense, weight in self.objectives]
        soft_parts = [s.weight * z3.If(s.bexp.satisfied(env), 0, s.penalty) for s in self.soft]
        obj = z3.Sum(parts) if parts else z3.IntVal(0)
        soft = z3.Sum(soft_parts) if soft_parts else z3.IntVal(0)
        return obj - soft

    def _domain_constraints(self, env: Dict[str, z3.ExprRef]) -> List[z3.BoolRef]:
        cons = []
        for v in self.vars:
            var = env[v.name]
            vals = [self._const(v.name, d) for d in v.domain]
            cons.append(z3.Or([var == c for c in vals]))
        return cons

    def _collect_failed_constraints(self) -> Set[str]:
        """Return names of hard constraints that make the problem unsatisfiable."""
        zvars = self._make_z3_vars()
        env = {k: v for k, v in zvars.items()}
        solver = z3.Solver()
        solver.set(unsat_core=True)
        for c in self._domain_constraints(env):
            solver.add(c)
        for name, bexp in self.hard:
            solver.assert_and_track(bexp.satisfied(env), name)
        if solver.check() == z3.unsat:
            core = solver.unsat_core()
            return {str(b) for b in core}
        return set()

    def solve(self, timeout: float | None = None) -> Dict[str, Any]:
        self._failed_constraints = set()
        zvars = self._make_z3_vars()
        env = {k: v for k, v in zvars.items()}
        penalty_expr = self._build_penalty_expr(env)
        opt = z3.Optimize()
        if timeout is not None:
            if timeout <= 0:
                raise TimeoutError()
            opt.set(timeout=int(timeout * 1000))

        for c in self._domain_constraints(env):
            opt.add(c)
        for _, bexp in self.hard:
            opt.add(bexp.satisfied(env))

        opt.minimize(penalty_expr)

        if self.objective_mode == "sum":
            obj_expr = self._build_objective_expr(env)
            opt.maximize(obj_expr)
        else:
            for expr, sense, _ in self.objectives:
                val = expr.eval(env)
                if sense == 1:
                    opt.maximize(val)
                else:
                    opt.minimize(val)

        check = opt.check()
        if check != z3.sat:
            if check == z3.unknown and opt.reason_unknown() == "timeout":
                raise TimeoutError()
            self._failed_constraints = self._collect_failed_constraints()
            raise RuntimeError("No feasible solution")

        model = opt.model()
        assignment = {v.name: self._model_value(model, zvars[v.name]) for v in self.vars}
        penalty_val = self._model_value(model, penalty_expr)

        result = {"assignment": assignment, "penalty": int(penalty_val)}
        if self.objectives:
            if self.objective_mode == "sum":
                obj_val = self._model_value(model, obj_expr)
                result["objective"] = float(obj_val)
            else:
                vals = [self._model_value(model, expr.eval(env)) for expr, _, _ in self.objectives]
                result["objectives"] = [float(v) if isinstance(v, float) else int(v) for v in vals]
        return result

    def all_solutions(self, limit: int | None = None, timeout: float | None = None) -> List[Dict[str, Any]]:
        if timeout is not None and timeout <= 0:
            return []
        zvars = self._make_z3_vars()
        env = {k: v for k, v in zvars.items()}
        solver = z3.Solver()
        if timeout is not None:
            solver.set(timeout=int(timeout * 1000))

        for c in self._domain_constraints(env):
            solver.add(c)
        for _, bexp in self.hard:
            solver.add(bexp.satisfied(env))

        solutions: List[Dict[str, Any]] = []

        while True:
            if limit is not None and len(solutions) >= limit:
                break
            check = solver.check()
            if check != z3.sat:
                if check == z3.unknown and solver.reason_unknown() == "timeout":
                    break
                if not solutions:
                    self._failed_constraints = self._collect_failed_constraints()
                break
            model = solver.model()
            assign = {v.name: self._model_value(model, zvars[v.name]) for v in self.vars}
            penalty = sum(s.cost(assign) for s in self.soft)
            if self.objective_mode == "sum":
                obj = sum(weight * sense * expr.eval(assign) for expr, sense, weight in self.objectives) - sum(
                    s.weight * s.cost(assign) for s in self.soft
                )
                entry = {"assignment": assign, "penalty": penalty, "objective": obj}
            else:
                objs = [sense * expr.eval(assign) for expr, sense, _ in self.objectives]
                entry = {"assignment": assign, "penalty": penalty, "objectives": objs}
            solutions.append(entry)

            # block this assignment
            solver.add(z3.Or([zvars[name] != self._const(name, val) for name, val in assign.items()]))

        return solutions

    def why_unsat(self) -> List[str]:
        """Return names of hard constraints that failed during the last search."""
        return sorted(self._failed_constraints)

    @staticmethod
    def _pretty_dict(d: Dict[str, Any]) -> str:
        return "\n".join(f"{k:>10} : {v}" for k, v in sorted(d.items()))

    def pretty(self, sol: Dict[str, Any]) -> str:
        rows = [self._pretty_dict(sol["assignment"])]
        rows.append(f"  penalty : {sol['penalty']}")
        if self.objectives:
            if self.objective_mode == "sum":
                rows.append(f"  objective : {sol['objective']}")
            else:
                rows.append(f" objectives : {tuple(sol['objectives'])}")
        return "\n".join(rows)
