"""Finds the cheapest mix of deposits that closes the ecological deficit (linear programming)."""
import math
import numpy as np
from scipy.optimize import linprog
import config as C
from model import apply_transaction, compute_metrics

KEYS = list(C.DEPOSITS)
PILLARS = ["carbon", "water", "cooling"]
EFFECT_KEY = {"carbon": "carbon", "water": "water", "cooling": "green"}
BIG = 1e5  # penalty per unit of unmet need (slack)


def recommend(state, target_score=70, max_trees=None, max_rain_m2=None):
    m = compute_metrics(state)
    need = {p: max(0.0, target_score / 100 * m["pillars"][p]["target"] - m["pillars"][p]["value"])
            for p in PILLARS}

    n = len(KEYS)
    cost = [C.DEPOSITS[k]["cost"] for k in KEYS] + [BIG] * 3
    A, b = [], []
    for j, p in enumerate(PILLARS):
        row = [-C.DEPOSITS[k][EFFECT_KEY[p]] for k in KEYS] + [0.0] * 3
        row[n + j] = -1.0
        A.append(row)
        b.append(-need[p])
    # ground space and roof space limits
    A.append([C.DEPOSITS[k]["ground_m2"] for k in KEYS] + [0.0] * 3)
    b.append(state.plantable_m2)
    A.append([C.DEPOSITS[k]["roof_m2"] for k in KEYS] + [0.0] * 3)
    b.append(state.roof_free_m2)

    bounds = []
    for k in KEYS:
        ub = None
        if k == "plant_trees" and max_trees is not None:
            ub = max_trees
        if k == "rainwater_harvest" and max_rain_m2 is not None:
            ub = max_rain_m2
        bounds.append((0, ub))
    bounds += [(0, None)] * 3

    res = linprog(cost, A_ub=np.array(A), b_ub=np.array(b), bounds=bounds, method="highs")
    if not res.success:
        return {"plan": [], "total_cost": 0, "before": m, "after": m, "ok": False}

    plan, new_state, total = [], state, 0
    for k, x in zip(KEYS, res.x[:n]):
        qty = math.ceil(x - 1e-6)
        if qty <= 0:
            continue
        d = C.DEPOSITS[k]
        plan.append({"category": k, "action": d["label"], "quantity": qty,
                     "unit": d["unit"], "cost_inr": qty * d["cost"]})
        total += qty * d["cost"]
        new_state = apply_transaction(new_state, k, qty)
    return {"plan": plan, "total_cost": total, "before": m,
            "after": compute_metrics(new_state), "ok": True}
