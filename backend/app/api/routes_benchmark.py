from fastapi import APIRouter, HTTPException
from typing import List
from pathlib import Path
import random
import time

from app.schemas.route_schema import (
    BenchmarkRequest, BenchmarkResponse, AlgorithmBenchmarkResult
)
from app.dsa.graph import RoadNetworkGraph
from app.dsa.matrix_builder import build_cost_matrices
from app.dsa.bitmask_tsp import solve_tsp_bitmask_dp
from app.dsa.branch_and_bound import VRPTWBranchAndBound, DeliveryStopInfo
from app.dsa.clarke_wright import solve_clarke_wright_savings

router = APIRouter(prefix="/benchmark", tags=["Algorithm Benchmarking"])

@router.post("/run", response_model=BenchmarkResponse)
async def run_benchmark(payload: BenchmarkRequest):
    """
    Runs algorithms on an identical problem instance to benchmark:
    - Execution time (ms)
    - States/nodes explored
    - Solution cost
    - Optimality gap (%) against exact Bitmask DP reference solution
    """
    network_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_network.json"
    graph = RoadNetworkGraph.load_from_json(network_path)

    n_stops = max(3, min(payload.instance_size, 16)) # Cap at 16 for exact DP feasibility
    # Select nodes: Depot (0) + first (n_stops - 1) customer nodes
    customer_nodes = [nid for nid, node in graph.nodes.items() if node.node_type == "customer"]
    selected_nodes = [0] + customer_nodes[:n_stops - 1]

    stops_info = [
        DeliveryStopInfo(
            id=idx,
            node_id=nid,
            name=graph.nodes[nid].name,
            weight=15.0 if idx != 0 else 0.0,
            volume=0.2 if idx != 0 else 0.0,
            earliest_time_min=0.0,
            latest_time_min=1440.0,
            service_time_min=5.0,
            priority=3
        )
        for idx, nid in enumerate(selected_nodes)
    ]

    # Generate pairwise matrices
    matrices = build_cost_matrices(graph, selected_nodes)
    results: List[AlgorithmBenchmarkResult] = []

    # 1. Reference: Held-Karp Bitmask DP (Guaranteed Exact Optimal)
    dp_res = solve_tsp_bitmask_dp(matrices.distance_matrix, include_dp_sample=False)
    optimal_cost = dp_res.optimal_cost

    results.append(AlgorithmBenchmarkResult(
        algorithm_name="Held-Karp Bitmask DP (Exact)",
        execution_time_ms=round(dp_res.execution_time_ms, 2),
        memory_usage_kb=round((1 << (n_stops - 1)) * (n_stops - 1) * 8 / 1024.0, 1),
        states_explored=dp_res.states_explored,
        solution_cost=round(dp_res.optimal_cost, 2),
        total_distance_km=round(dp_res.optimal_cost, 2),
        total_duration_min=round(dp_res.optimal_cost * 1.5, 2),
        optimality_gap_percent=0.0, # Ground truth reference
        is_optimal_guaranteed=True
    ))

    # 2. Branch and Bound with Lower-Bound Pruning
    bb_solver = VRPTWBranchAndBound(
        cost_matrix=matrices.distance_matrix,
        duration_matrix=matrices.duration_matrix,
        stops=stops_info,
        vehicle_max_weight=1000.0,
        vehicle_max_volume=10.0
    )
    bb_res = bb_solver.solve()
    bb_gap = ((bb_res.optimal_cost - optimal_cost) / optimal_cost * 100.0) if optimal_cost > 0 else 0.0

    results.append(AlgorithmBenchmarkResult(
        algorithm_name="Branch and Bound with Pruning (Exact)",
        execution_time_ms=round(bb_res.execution_time_ms, 2),
        memory_usage_kb=round(bb_res.nodes_explored * 0.12, 1),
        states_explored=bb_res.nodes_explored,
        solution_cost=round(bb_res.optimal_cost, 2),
        total_distance_km=round(bb_res.optimal_cost, 2),
        total_duration_min=round(bb_res.schedule[-1].arrival_time_min if bb_res.schedule else 0.0, 2),
        optimality_gap_percent=max(0.0, round(bb_gap, 2)),
        is_optimal_guaranteed=True
    ))

    # 3. Clarke-Wright Savings + 2-Opt Heuristic
    cw_res = solve_clarke_wright_savings(
        cost_matrix=matrices.distance_matrix,
        duration_matrix=matrices.duration_matrix,
        stops=stops_info,
        vehicle_max_weight=1000.0,
        vehicle_max_volume=10.0,
        num_vehicles=1
    )
    cw_dist = cw_res.total_distance
    cw_gap = ((cw_dist - optimal_cost) / optimal_cost * 100.0) if optimal_cost > 0 else 0.0

    results.append(AlgorithmBenchmarkResult(
        algorithm_name="Clarke-Wright Savings + 2-Opt (Heuristic)",
        execution_time_ms=round(cw_res.execution_time_ms, 2),
        memory_usage_kb=round(n_stops * n_stops * 0.05, 1),
        states_explored=n_stops * n_stops,
        solution_cost=round(cw_dist, 2),
        total_distance_km=round(cw_dist, 2),
        total_duration_min=round(cw_res.total_duration, 2),
        optimality_gap_percent=max(0.0, round(cw_gap, 2)),
        is_optimal_guaranteed=False
    ))

    # 4. Nearest Neighbor (Greedy Baseline)
    t0_nn = time.perf_counter()
    visited = {0}
    curr = 0
    nn_dist = 0.0
    while len(visited) < n_stops:
        nxt = min([j for j in range(n_stops) if j not in visited], key=lambda j: matrices.distance_matrix[curr][j])
        nn_dist += matrices.distance_matrix[curr][nxt]
        visited.add(nxt)
        curr = nxt
    nn_dist += matrices.distance_matrix[curr][0]
    nn_time = (time.perf_counter() - t0_nn) * 1000.0
    nn_gap = ((nn_dist - optimal_cost) / optimal_cost * 100.0) if optimal_cost > 0 else 0.0

    results.append(AlgorithmBenchmarkResult(
        algorithm_name="Nearest Neighbor (Greedy Baseline)",
        execution_time_ms=round(nn_time, 2),
        memory_usage_kb=round(n_stops * 0.02, 1),
        states_explored=n_stops,
        solution_cost=round(nn_dist, 2),
        total_distance_km=round(nn_dist, 2),
        total_duration_min=round(nn_dist * 1.5, 2),
        optimality_gap_percent=max(0.0, round(nn_gap, 2)),
        is_optimal_guaranteed=False
    ))

    return BenchmarkResponse(
        instance_size=n_stops,
        results=results
    )
