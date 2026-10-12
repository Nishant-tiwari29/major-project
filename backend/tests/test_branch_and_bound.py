import pytest
from app.dsa.branch_and_bound import VRPTWBranchAndBound, DeliveryStopInfo
from app.dsa.bitmask_tsp import solve_tsp_bitmask_dp
from app.dsa.clarke_wright import solve_clarke_wright_savings

def test_branch_and_bound_matches_bitmask_dp_unconstrained():
    # Symmetric 5-node cost matrix
    cost_matrix = [
        [0.0, 12.0, 18.0, 22.0, 15.0],
        [12.0, 0.0, 30.0, 25.0, 14.0],
        [18.0, 30.0, 0.0, 16.0, 28.0],
        [22.0, 25.0, 16.0, 0.0, 20.0],
        [15.0, 14.0, 28.0, 20.0, 0.0]
    ]
    duration_matrix = [[c * 1.5 for c in row] for row in cost_matrix]

    stops = [
        DeliveryStopInfo(0, 0, "Depot", 0.0, 0.0, 0.0, 1000.0, 0.0, 0),
        DeliveryStopInfo(1, 1, "Stop 1", 10.0, 0.1, 0.0, 1000.0, 5.0, 3),
        DeliveryStopInfo(2, 2, "Stop 2", 15.0, 0.2, 0.0, 1000.0, 5.0, 4),
        DeliveryStopInfo(3, 3, "Stop 3", 20.0, 0.3, 0.0, 1000.0, 5.0, 2),
        DeliveryStopInfo(4, 4, "Stop 4", 12.0, 0.1, 0.0, 1000.0, 5.0, 5),
    ]

    # Exact Bitmask DP
    dp_res = solve_tsp_bitmask_dp(cost_matrix)

    # Branch and Bound with ample capacity and wide time windows
    bb_solver = VRPTWBranchAndBound(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=500.0,
        vehicle_max_volume=5.0
    )
    bb_res = bb_solver.solve()

    assert bb_res.is_feasible
    assert pytest.approx(bb_res.optimal_cost, 0.001) == dp_res.optimal_cost
    assert bb_res.nodes_explored > 0
    assert bb_res.optimal_sequence[0] == 0
    assert bb_res.optimal_sequence[-1] == 0

def test_branch_and_bound_prunes_infeasible_time_window():
    cost_matrix = [
        [0.0, 50.0, 50.0],
        [50.0, 0.0, 50.0],
        [50.0, 50.0, 0.0]
    ]
    duration_matrix = [
        [0.0, 60.0, 60.0],
        [60.0, 0.0, 60.0],
        [60.0, 60.0, 0.0]
    ]
    # Stop 1 has latest deadline at 10.0 minutes, but travel from depot takes 60.0 minutes!
    stops = [
        DeliveryStopInfo(0, 0, "Depot", 0.0, 0.0, 0.0, 500.0, 0.0, 0),
        DeliveryStopInfo(1, 1, "Urgent Infeasible", 10.0, 0.1, 0.0, 10.0, 5.0, 5),
        DeliveryStopInfo(2, 2, "Stop 2", 10.0, 0.1, 0.0, 500.0, 5.0, 3)
    ]

    bb_solver = VRPTWBranchAndBound(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=100.0,
        vehicle_max_volume=2.0
    )
    bb_res = bb_solver.solve()

    # Must detect pruning by time
    assert bb_res.pruned_by_time > 0

def test_clarke_wright_capacity_enforcement():
    cost_matrix = [
        [0.0, 10.0, 12.0, 15.0],
        [10.0, 0.0, 14.0, 18.0],
        [12.0, 14.0, 0.0, 11.0],
        [15.0, 18.0, 11.0, 0.0]
    ]
    duration_matrix = [[c * 1.2 for c in row] for row in cost_matrix]
    stops = [
        DeliveryStopInfo(0, 0, "Depot", 0.0, 0.0, 0.0, 500.0, 0.0, 0),
        DeliveryStopInfo(1, 1, "Heavy 1", 60.0, 1.0, 0.0, 500.0, 10.0, 3),
        DeliveryStopInfo(2, 2, "Heavy 2", 60.0, 1.0, 0.0, 500.0, 10.0, 4),
        DeliveryStopInfo(3, 3, "Heavy 3", 60.0, 1.0, 0.0, 500.0, 10.0, 2)
    ]

    # Vehicle capacity is only 80 kg, so no two 60 kg items can share a vehicle!
    cw_res = solve_clarke_wright_savings(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=80.0,
        vehicle_max_volume=2.0
    )

    # Must produce 3 separate routes
    assert len(cw_res.routes) == 3
    for r in cw_res.routes:
        assert r.total_weight <= 80.0
