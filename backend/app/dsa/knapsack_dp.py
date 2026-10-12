from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class Item:
    id: int
    name: str
    weight: float
    volume: float
    priority: int # Value to maximize

@dataclass
class KnapsackResult:
    max_priority_score: int
    selected_items: List[Item]
    total_weight: float
    total_volume: float
    weight_utilization_percent: float
    volume_utilization_percent: float
    execution_time_ms: float

def solve_2d_knapsack_dp(
    items: List[Item],
    max_weight: float,
    max_volume: float,
    weight_scale: int = 10, # 0.1 kg resolution
    volume_scale: int = 100 # 0.01 m3 resolution
) -> KnapsackResult:
    """
    Exact Multi-Dimensional (2D) Knapsack Dynamic Programming solver for vehicle loading.
    - Resolves continuous weights/volumes using integer scaling factors.
    - Recurrence: DP[i][w][v] = max(DP[i-1][w][v], DP[i-1][w - w_i][v - v_i] + p_i)
    - Reconstructs exact package assignments.
    """
    start_time = time.perf_counter()

    W_int = int(round(max_weight * weight_scale))
    V_int = int(round(max_volume * volume_scale))
    n = len(items)

    # Scaled item properties
    weights = [int(round(it.weight * weight_scale)) for it in items]
    volumes = [int(round(it.volume * volume_scale)) for it in items]
    values = [it.priority for it in items]

    # Full 3D table for accurate item reconstruction: dp[i][w][v]
    # To conserve memory while preserving reconstruction, store decisions:
    # take[i][w][v] is True if item i was included
    dp = [[0] * (V_int + 1) for _ in range(W_int + 1)]
    # Keep track of history per item
    history: List[List[List[bool]]] = []

    for i in range(n):
        w_i = weights[i]
        v_i = volumes[i]
        val_i = values[i]
        take_i = [[False] * (V_int + 1) for _ in range(W_int + 1)]

        # Traverse backwards to use 2D table in-place
        for w in range(W_int, w_i - 1, -1):
            for v in range(V_int, v_i - 1, -1):
                if dp[w - w_i][v - v_i] + val_i > dp[w][v]:
                    dp[w][v] = dp[w - w_i][v - v_i] + val_i
                    take_i[w][v] = True

        history.append(take_i)

    # Reconstruct optimal item set
    selected: List[Item] = []
    curr_w = W_int
    curr_v = V_int

    for i in range(n - 1, -1, -1):
        if history[i][curr_w][curr_v]:
            selected.append(items[i])
            curr_w -= weights[i]
            curr_v -= volumes[i]

    selected.reverse()

    tot_w = sum(it.weight for it in selected)
    tot_v = sum(it.volume for it in selected)
    w_util = (tot_w / max_weight * 100.0) if max_weight > 0 else 0.0
    v_util = (tot_v / max_volume * 100.0) if max_volume > 0 else 0.0
    exec_time = (time.perf_counter() - start_time) * 1000.0

    return KnapsackResult(
        max_priority_score=sum(it.priority for it in selected),
        selected_items=selected,
        total_weight=round(tot_w, 2),
        total_volume=round(tot_v, 2),
        weight_utilization_percent=round(w_util, 1),
        volume_utilization_percent=round(v_util, 1),
        execution_time_ms=exec_time
    )
