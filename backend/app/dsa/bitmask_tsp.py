import itertools
import time
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BitmaskTSPResult:
    optimal_cost: float
    optimal_route: List[int] # Sequence of node indices: 0 -> n1 -> n2 -> ... -> 0
    states_explored: int
    execution_time_ms: float
    dp_matrix_sample: Optional[Dict[str, Any]] = None # Visualizer payload

def solve_tsp_bitmask_dp(
    cost_matrix: List[List[float]],
    include_dp_sample: bool = True
) -> BitmaskTSPResult:
    """
    Exact Held-Karp Dynamic Programming algorithm for TSP.
    - Depot is fixed at index 0.
    - Visited subset of customers is represented as integer bitmask: bit k is 1 if node (k+1) is visited.
    - Recurrence: dp(mask, u) = min_{v in mask \\ {u}} [dp(mask \\ {u}, v) + cost(v, u)]
    - Time Complexity: O(n^2 * 2^n)
    - Space Complexity: O(n * 2^n)
    Guaranteed to find the globally optimal tour.
    """
    start_time = time.perf_counter()
    n = len(cost_matrix)

    if n <= 1:
        return BitmaskTSPResult(
            optimal_cost=0.0,
            optimal_route=[0, 0] if n == 1 else [],
            states_explored=1,
            execution_time_ms=0.0
        )

    if n == 2:
        cost = cost_matrix[0][1] + cost_matrix[1][0]
        return BitmaskTSPResult(
            optimal_cost=cost,
            optimal_route=[0, 1, 0],
            states_explored=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0
        )

    # Let num_customers = n - 1 (indices 1 to n - 1)
    num_cust = n - 1
    total_masks = 1 << num_cust

    # dp[mask][u]: min cost to visit subset `mask` ending at customer (u + 1)
    # mask has bits 0..(num_cust-1) corresponding to nodes 1..num_cust
    dp = [[float('inf')] * num_cust for _ in range(total_masks)]
    parent = [[-1] * num_cust for _ in range(total_masks)]

    # Base case: single customer visited directly from depot 0
    for u in range(num_cust):
        mask = 1 << u
        node_u = u + 1
        dp[mask][u] = cost_matrix[0][node_u]
        parent[mask][u] = -1 # Came directly from depot (no previous customer)

    states_explored = num_cust

    # Iterate over subset sizes from 2 to num_cust
    for size in range(2, num_cust + 1):
        for mask in range(total_masks):
            # Check if mask has exactly `size` bits set
            if bin(mask).count('1') != size:
                continue

            for u in range(num_cust):
                if not (mask & (1 << u)):
                    continue # u not in current subset

                prev_mask = mask ^ (1 << u)
                node_u = u + 1
                best_cost = float('inf')
                best_prev = -1

                for v in range(num_cust):
                    if not (prev_mask & (1 << v)):
                        continue # v not in prev subset

                    node_v = v + 1
                    transition_cost = dp[prev_mask][v] + cost_matrix[node_v][node_u]
                    if transition_cost < best_cost:
                        best_cost = transition_cost
                        best_prev = v

                dp[mask][u] = best_cost
                parent[mask][u] = best_prev
                states_explored += 1

    # Close the Hamiltonian cycle by returning to depot 0 from last customer
    final_mask = total_masks - 1
    optimal_cost = float('inf')
    last_customer = -1

    for u in range(num_cust):
        node_u = u + 1
        tour_cost = dp[final_mask][u] + cost_matrix[node_u][0]
        if tour_cost < optimal_cost:
            optimal_cost = tour_cost
            last_customer = u

    # Route reconstruction
    route_customers = []
    curr_mask = final_mask
    curr_u = last_customer

    while curr_u != -1 and curr_mask > 0:
        route_customers.append(curr_u + 1)
        prev_u = parent[curr_mask][curr_u]
        curr_mask = curr_mask ^ (1 << curr_u)
        curr_u = prev_u

    route_customers.reverse()
    optimal_route = [0] + route_customers + [0]
    exec_time = (time.perf_counter() - start_time) * 1000.0

    # Build DP visualization sample (first 16 masks for educational UI rendering)
    dp_sample = None
    if include_dp_sample:
        dp_sample = {
            "num_customers": num_cust,
            "total_subsets": total_masks,
            "sample_states": []
        }
        for m in range(min(total_masks, 16)):
            row = []
            for u in range(num_cust):
                val = dp[m][u]
                row.append(None if val == float('inf') else round(val, 2))
            dp_sample["sample_states"].append({
                "mask": m,
                "binary": bin(m)[2:].zfill(num_cust),
                "values": row
            })

    return BitmaskTSPResult(
        optimal_cost=optimal_cost,
        optimal_route=optimal_route,
        states_explored=states_explored,
        execution_time_ms=exec_time,
        dp_matrix_sample=dp_sample
    )

def solve_tsp_brute_force(cost_matrix: List[List[float]]) -> Tuple[float, List[int]]:
    """
    O((n-1)!) brute-force solver used for proving mathematical optimality of Bitmask DP in tests.
    """
    n = len(cost_matrix)
    customers = list(range(1, n))
    best_cost = float('inf')
    best_route = []

    for perm in itertools.permutations(customers):
        current_route = [0] + list(perm) + [0]
        current_cost = 0.0
        for i in range(len(current_route) - 1):
            current_cost += cost_matrix[current_route[i]][current_route[i + 1]]
        if current_cost < best_cost:
            best_cost = current_cost
            best_route = current_route

    return best_cost, best_route
