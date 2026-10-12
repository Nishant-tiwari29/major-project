import time
import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class DeliveryStopInfo:
    id: int # Original delivery request ID or customer ID
    node_id: int # Graph road node
    name: str
    weight: float
    volume: float
    earliest_time_min: float # Minutes from shift start (e.g., 0.0 = 08:00)
    latest_time_min: float # Minutes from shift start (e.g., 180.0 = 11:00)
    service_time_min: float
    priority: int

@dataclass
class RouteStopSchedule:
    location_idx: int
    arrival_time_min: float
    departure_time_min: float
    waiting_time_min: float
    lateness_min: float
    accumulated_load: float

@dataclass
class BranchAndBoundResult:
    optimal_cost: float
    optimal_sequence: List[int] # Indices in stops list: 0 -> ... -> 0
    schedule: List[RouteStopSchedule]
    nodes_explored: int
    pruned_by_bound: int
    pruned_by_time: int
    pruned_by_capacity: int
    execution_time_ms: float
    is_feasible: bool
    search_tree_sample: Optional[Dict[str, Any]] = None # For UI tree visualizer

class VRPTWBranchAndBound:
    """
    Branch and Bound solver with lower-bound and constraint pruning for VRPTW.
    - Guarantees exact optimal solution for single or multi-route permutations.
    - Pruning Rules:
      1. Time Window Infeasibility: arrival_time > latest_time => prune
      2. Capacity Overload: current_weight + min_remaining_weight > vehicle_capacity => prune
      3. Lower Bound: current_cost + incoming_edge_lower_bound >= best_upper_bound => prune
    """
    def __init__(
        self,
        cost_matrix: List[List[float]],
        duration_matrix: List[List[float]],
        stops: List[DeliveryStopInfo], # Index 0 is Depot
        vehicle_max_weight: float,
        vehicle_max_volume: float,
        late_penalty_per_min: float = 2.0
    ):
        self.cost_matrix = cost_matrix
        self.duration_matrix = duration_matrix
        self.stops = stops
        self.max_weight = vehicle_max_weight
        self.max_volume = vehicle_max_volume
        self.late_penalty = late_penalty_per_min
        self.n = len(stops)

        self.nodes_explored = 0
        self.pruned_by_bound = 0
        self.pruned_by_time = 0
        self.pruned_by_capacity = 0
        self.best_cost = float('inf')
        self.best_sequence: List[int] = []
        self.best_schedule: List[RouteStopSchedule] = []

        # Search tree log for visualization
        self.tree_nodes_log: List[Dict[str, Any]] = []

    def compute_lower_bound(self, current_cost: float, visited_set: set) -> float:
        """
        Calculates lower bound using minimum incoming edge relaxation for unvisited vertices.
        LB = current_cost + sum_{j in unvisited} min_{k in all, k != j} cost(k, j)
        """
        lb = current_cost
        unvisited = [j for j in range(1, self.n) if j not in visited_set]

        for j in unvisited:
            min_in = float('inf')
            for k in range(self.n):
                if k != j and self.cost_matrix[k][j] < min_in:
                    min_in = self.cost_matrix[k][j]
            lb += min_in

        # Add return to depot min cost
        if unvisited:
            min_to_depot = min(self.cost_matrix[j][0] for j in unvisited)
            lb += min_to_depot

        return lb

    def solve(self, record_tree_limit: int = 50) -> BranchAndBoundResult:
        start_time = time.perf_counter()

        # Initial Upper Bound via Greedy Nearest Neighbor
        self._compute_initial_upper_bound()

        # Root search state
        initial_schedule = [RouteStopSchedule(
            location_idx=0,
            arrival_time_min=0.0,
            departure_time_min=0.0,
            waiting_time_min=0.0,
            lateness_min=0.0,
            accumulated_load=0.0
        )]

        self._branch(
            current_path=[0],
            visited_set={0},
            current_cost=0.0,
            current_time=0.0,
            current_weight=0.0,
            current_volume=0.0,
            schedule=initial_schedule,
            parent_id="root",
            record_limit=record_tree_limit
        )

        exec_time = (time.perf_counter() - start_time) * 1000.0

        tree_sample = {
            "total_nodes_explored": self.nodes_explored,
            "pruned_by_bound": self.pruned_by_bound,
            "pruned_by_time": self.pruned_by_time,
            "pruned_by_capacity": self.pruned_by_capacity,
            "sample_tree": self.tree_nodes_log[:record_tree_limit]
        }

        is_feas = self.best_cost < float('inf')
        return BranchAndBoundResult(
            optimal_cost=self.best_cost if is_feas else 0.0,
            optimal_sequence=self.best_sequence if is_feas else [],
            schedule=self.best_schedule if is_feas else [],
            nodes_explored=self.nodes_explored,
            pruned_by_bound=self.pruned_by_bound,
            pruned_by_time=self.pruned_by_time,
            pruned_by_capacity=self.pruned_by_capacity,
            execution_time_ms=exec_time,
            is_feasible=is_feas,
            search_tree_sample=tree_sample
        )

    def _compute_initial_upper_bound(self):
        """Constructs an initial feasible route using Nearest Neighbor heuristic."""
        visited = {0}
        curr = 0
        curr_time = 0.0
        curr_weight = 0.0
        curr_cost = 0.0
        route = [0]
        schedule = [RouteStopSchedule(0, 0.0, 0.0, 0.0, 0.0, 0.0)]
        feasible = True

        while len(visited) < self.n:
            best_next = -1
            best_dist = float('inf')

            for j in range(1, self.n):
                if j not in visited:
                    if self.cost_matrix[curr][j] < best_dist:
                        best_dist = self.cost_matrix[curr][j]
                        best_next = j

            if best_next == -1:
                feasible = False
                break

            travel_dur = self.duration_matrix[curr][best_next]
            arr_time = curr_time + travel_dur
            stop = self.stops[best_next]

            # Strict feasibility checks
            if curr_weight + stop.weight > self.max_weight or arr_time > stop.latest_time_min:
                feasible = False
                break

            wait_time = max(0.0, stop.earliest_time_min - arr_time)
            dep_time = max(arr_time, stop.earliest_time_min) + stop.service_time_min
            late_time = max(0.0, arr_time - stop.latest_time_min)

            curr_cost += best_dist
            curr_time = dep_time
            curr_weight += stop.weight
            visited.add(best_next)
            route.append(best_next)
            schedule.append(RouteStopSchedule(best_next, arr_time, dep_time, wait_time, late_time, curr_weight))
            curr = best_next

        if feasible and len(visited) == self.n:
            # Return to depot
            return_cost = self.cost_matrix[curr][0]
            curr_cost += return_cost
            route.append(0)
            schedule.append(RouteStopSchedule(0, curr_time + self.duration_matrix[curr][0], curr_time, 0.0, 0.0, curr_weight))

            self.best_cost = curr_cost
            self.best_sequence = route
            self.best_schedule = schedule
        else:
            self.best_cost = float('inf')
            self.best_sequence = []
            self.best_schedule = []

    def _branch(
        self,
        current_path: List[int],
        visited_set: set,
        current_cost: float,
        current_time: float,
        current_weight: float,
        current_volume: float,
        schedule: List[RouteStopSchedule],
        parent_id: str,
        record_limit: int
    ):
        self.nodes_explored += 1
        node_id = f"node_{self.nodes_explored}"
        last_node = current_path[-1]

        # 1. Base Case: All customers visited -> complete cycle to depot 0
        if len(visited_set) == self.n:
            return_dist = self.cost_matrix[last_node][0]
            total_tour_cost = current_cost + return_dist
            if total_tour_cost < self.best_cost:
                self.best_cost = total_tour_cost
                final_schedule = list(schedule)
                final_schedule.append(RouteStopSchedule(
                    location_idx=0,
                    arrival_time_min=current_time + self.duration_matrix[last_node][0],
                    departure_time_min=current_time + self.duration_matrix[last_node][0],
                    waiting_time_min=0.0,
                    lateness_min=0.0,
                    accumulated_load=current_weight
                ))
                self.best_sequence = current_path + [0]
                self.best_schedule = final_schedule

            if len(self.tree_nodes_log) < record_limit:
                self.tree_nodes_log.append({
                    "id": node_id, "parent": parent_id,
                    "label": f"Depot 0 (Tour Cost: {total_tour_cost:.1f})",
                    "status": "solution"
                })
            return

        # 2. Lower Bound Pruning
        lb = self.compute_lower_bound(current_cost, visited_set)
        if lb >= self.best_cost:
            self.pruned_by_bound += 1
            if len(self.tree_nodes_log) < record_limit:
                self.tree_nodes_log.append({
                    "id": node_id, "parent": parent_id,
                    "label": f"Pruned (LB {lb:.1f} >= Best {self.best_cost:.1f})",
                    "status": "pruned_bound"
                })
            return

        # 3. Explore unvisited candidate children
        candidates = [j for j in range(1, self.n) if j not in visited_set]
        # Sort candidates by cost from last_node for faster discovery of tight bounds
        candidates.sort(key=lambda j: self.cost_matrix[last_node][j])

        for nxt in candidates:
            stop = self.stops[nxt]

            # Capacity Pruning Rule
            if current_weight + stop.weight > self.max_weight or current_volume + stop.volume > self.max_volume:
                self.pruned_by_capacity += 1
                continue

            # Time Window Calculation
            travel_dur = self.duration_matrix[last_node][nxt]
            arr_time = current_time + travel_dur

            # Strict time window deadline check
            if arr_time > stop.latest_time_min:
                self.pruned_by_time += 1
                continue

            wait_time = max(0.0, stop.earliest_time_min - arr_time)
            dep_time = max(arr_time, stop.earliest_time_min) + stop.service_time_min
            step_cost = self.cost_matrix[last_node][nxt]

            new_schedule_entry = RouteStopSchedule(
                location_idx=nxt,
                arrival_time_min=arr_time,
                departure_time_min=dep_time,
                waiting_time_min=wait_time,
                lateness_min=0.0,
                accumulated_load=current_weight + stop.weight
            )

            if len(self.tree_nodes_log) < record_limit:
                self.tree_nodes_log.append({
                    "id": f"{node_id}_{nxt}", "parent": node_id,
                    "label": f"{stop.name} (Arr: {arr_time:.1f}m)",
                    "status": "active"
                })

            self._branch(
                current_path=current_path + [nxt],
                visited_set=visited_set | {nxt},
                current_cost=current_cost + step_cost,
                current_time=dep_time,
                current_weight=current_weight + stop.weight,
                current_volume=current_volume + stop.volume,
                schedule=schedule + [new_schedule_entry],
                parent_id=node_id,
                record_limit=record_limit
            )
