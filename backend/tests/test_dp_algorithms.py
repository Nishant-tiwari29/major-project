import pytest
import random
from app.dsa.bitmask_tsp import solve_tsp_bitmask_dp, solve_tsp_brute_force
from app.dsa.knapsack_dp import solve_2d_knapsack_dp, Item

def test_tsp_bitmask_matches_brute_force():
    # Test on multiple small instances of sizes 4, 5, and 6
    random.seed(42)
    for n in [4, 5, 6]:
        # Generate random distance matrix
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(n):
                if i != j:
                    matrix[i][j] = float(random.randint(10, 80))

        # Solve with exact Bitmask DP
        dp_res = solve_tsp_bitmask_dp(matrix)
        # Solve with brute force
        bf_cost, bf_route = solve_tsp_brute_force(matrix)

        # Assert exact global optimality match
        assert pytest.approx(dp_res.optimal_cost, 0.001) == bf_cost
        assert dp_res.optimal_route[0] == 0
        assert dp_res.optimal_route[-1] == 0
        assert len(set(dp_res.optimal_route[:-1])) == n

def test_tsp_route_reconstruction_validity():
    # 4-city known triangle + depot
    matrix = [
        [0.0, 10.0, 15.0, 20.0],
        [10.0, 0.0, 35.0, 25.0],
        [15.0, 35.0, 0.0, 30.0],
        [20.0, 25.0, 30.0, 0.0]
    ]
    res = solve_tsp_bitmask_dp(matrix)
    # Reconstructed tour cost should equal optimal_cost
    reconstructed_cost = sum(
        matrix[res.optimal_route[i]][res.optimal_route[i + 1]]
        for i in range(len(res.optimal_route) - 1)
    )
    assert pytest.approx(reconstructed_cost, 0.001) == res.optimal_cost

def test_2d_knapsack_capacity_limits():
    items = [
        Item(id=1, name="Box A", weight=10.0, volume=0.5, priority=5),
        Item(id=2, name="Box B", weight=20.0, volume=1.0, priority=10),
        Item(id=3, name="Box C", weight=15.0, volume=0.8, priority=7),
        Item(id=4, name="Box D", weight=5.0, volume=0.2, priority=3),
    ]

    # Vehicle capacity: 25 kg, 1.2 m3
    res = solve_2d_knapsack_dp(items, max_weight=25.0, max_volume=1.2)

    assert res.total_weight <= 25.0
    assert res.total_volume <= 1.2
    # Item 2 (20kg, 1.0m3, prio 10) + Item 4 (5kg, 0.2m3, prio 3) = 25kg, 1.2m3, prio 13
    assert res.max_priority_score == 13
    assert {it.id for it in res.selected_items} == {2, 4}

def test_2d_knapsack_zero_capacity():
    items = [Item(id=1, name="Box A", weight=10.0, volume=0.5, priority=5)]
    res = solve_2d_knapsack_dp(items, max_weight=0.0, max_volume=0.0)
    assert res.max_priority_score == 0
    assert len(res.selected_items) == 0
