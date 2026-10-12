import time
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from app.dsa.branch_and_bound import DeliveryStopInfo, RouteStopSchedule

@dataclass
class VehicleRoute:
    vehicle_idx: int
    stops_sequence: List[int] # 0 -> ... -> 0
    total_distance: float
    total_duration: float
    total_weight: float
    total_volume: float
    schedule: List[RouteStopSchedule]
    is_feasible: bool

@dataclass
class ClarkeWrightResult:
    routes: List[VehicleRoute]
    total_distance: float
    total_duration: float
    total_cost: float
    execution_time_ms: float

def run_2opt_local_search(
    route: List[int],
    cost_matrix: List[List[float]],
    max_iterations: int = 50
) -> Tuple[List[int], float]:
    """
    2-Opt local search algorithm to remove crossing edges and improve route quality.
    Time Complexity: O(iterations * n^2).
    """
    best_route = list(route)
    n = len(best_route)

    def route_cost(r):
        return sum(cost_matrix[r[i]][r[i + 1]] for i in range(len(r) - 1))

    best_cost = route_cost(best_route)
    improved = True
    iterations = 0

    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(1, n - 2):
            for j in range(i + 1, n - 1):
                # Reverse segment between i and j
                new_route = best_route[:i] + best_route[i:j + 1][::-1] + best_route[j + 1:]
                new_cost = route_cost(new_route)
                if new_cost < best_cost - 1e-4:
                    best_route = new_route
                    best_cost = new_cost
                    improved = True
                    break
            if improved:
                break

    return best_route, best_cost

def solve_clarke_wright_savings(
    cost_matrix: List[List[float]],
    duration_matrix: List[List[float]],
    stops: List[DeliveryStopInfo], # Index 0 is Depot
    vehicle_max_weight: float,
    vehicle_max_volume: float,
    num_vehicles: int = 4
) -> ClarkeWrightResult:
    """
    Clarke-Wright Savings Heuristic for Multi-Vehicle Routing with capacity and time feasibility checks.
    Savings formula: s(i, j) = c(0, i) + c(0, j) - c(i, j).
    """
    start_time = time.perf_counter()
    n = len(stops)
    if n <= 1:
        return ClarkeWrightResult([], 0.0, 0.0, 0.0, 0.0)

    # 1. Compute Savings s(i, j) for all customer pairs
    savings = []
    for i in range(1, n):
        for j in range(i + 1, n):
            s_val = cost_matrix[0][i] + cost_matrix[0][j] - cost_matrix[i][j]
            savings.append((s_val, i, j))

    # Sort savings in descending order
    savings.sort(reverse=True, key=lambda x: x[0])

    # 2. Initially assign each customer to a dedicated back-and-forth route: [0, i, 0]
    # Represent routes as internal customer sequences: [i]
    active_routes: List[List[int]] = [[i] for i in range(1, n)]

    def get_route_load(r_indices):
        w = sum(stops[idx].weight for idx in r_indices)
        v = sum(stops[idx].volume for idx in r_indices)
        return w, v

    def check_time_feasibility(r_indices):
        curr_time = 0.0
        prev = 0
        for idx in r_indices:
            curr_time += duration_matrix[prev][idx]
            stop = stops[idx]
            if curr_time > stop.latest_time_min:
                return False
            curr_time = max(curr_time, stop.earliest_time_min) + stop.service_time_min
            prev = idx
        return True

    # 3. Merge routes greedily based on savings
    for s_val, i, j in savings:
        r_i = None
        r_j = None
        for r in active_routes:
            if i in r:
                r_i = r
            if j in r:
                r_j = r

        if r_i is not None and r_j is not None and r_i != r_j:
            # Check if i and j are at route ends
            merged_candidate = None
            if r_i[-1] == i and r_j[0] == j:
                merged_candidate = r_i + r_j
            elif r_j[-1] == j and r_i[0] == i:
                merged_candidate = r_j + r_i
            elif r_i[-1] == i and r_j[-1] == j:
                merged_candidate = r_i + r_j[::-1]
            elif r_i[0] == i and r_j[0] == j:
                merged_candidate = r_i[::-1] + r_j

            if merged_candidate is not None:
                w, v = get_route_load(merged_candidate)
                if w <= vehicle_max_weight and v <= vehicle_max_volume:
                    if check_time_feasibility(merged_candidate):
                        active_routes.remove(r_i)
                        active_routes.remove(r_j)
                        active_routes.append(merged_candidate)

    # 4. Refine with 2-Opt and construct schedules
    final_routes: List[VehicleRoute] = []
    tot_dist = 0.0
    tot_dur = 0.0

    for v_idx, cust_seq in enumerate(active_routes):
        initial_route = [0] + cust_seq + [0]
        refined_route, dist = run_2opt_local_search(initial_route, cost_matrix)

        # Build schedule
        schedule = [RouteStopSchedule(0, 0.0, 0.0, 0.0, 0.0, 0.0)]
        curr_time = 0.0
        curr_weight = 0.0
        route_dur = 0.0

        for stop_idx in refined_route[1:-1]:
            stop = stops[stop_idx]
            prev = schedule[-1].location_idx
            travel_t = duration_matrix[prev][stop_idx]
            arr_t = curr_time + travel_t
            wait_t = max(0.0, stop.earliest_time_min - arr_t)
            dep_t = max(arr_t, stop.earliest_time_min) + stop.service_time_min
            late_t = max(0.0, arr_t - stop.latest_time_min)

            curr_weight += stop.weight
            curr_time = dep_t
            schedule.append(RouteStopSchedule(stop_idx, arr_t, dep_t, wait_t, late_t, curr_weight))

        # Return to depot
        return_travel_t = duration_matrix[refined_route[-2]][0]
        schedule.append(RouteStopSchedule(0, curr_time + return_travel_t, curr_time + return_travel_t, 0.0, 0.0, curr_weight))
        route_dur = curr_time + return_travel_t

        w_tot, v_tot = get_route_load(cust_seq)
        tot_dist += dist
        tot_dur += route_dur

        final_routes.append(VehicleRoute(
            vehicle_idx=v_idx,
            stops_sequence=refined_route,
            total_distance=round(dist, 2),
            total_duration=round(route_dur, 2),
            total_weight=round(w_tot, 2),
            total_volume=round(v_tot, 2),
            schedule=schedule,
            is_feasible=True
        ))

    exec_time = (time.perf_counter() - start_time) * 1000.0

    return ClarkeWrightResult(
        routes=final_routes,
        total_distance=round(tot_dist, 2),
        total_duration=round(tot_dur, 2),
        total_cost=round(tot_dist * 1.20, 2),
        execution_time_ms=exec_time
    )
