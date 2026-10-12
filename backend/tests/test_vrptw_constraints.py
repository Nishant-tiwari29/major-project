import pytest
from app.dsa.branch_and_bound import VRPTWBranchAndBound, DeliveryStopInfo
from app.dsa.clarke_wright import solve_clarke_wright_savings
from app.dsa.ev_optimizer import EVRouteOptimizer
from app.dsa.graph import RoadNetworkGraph, Node, Edge

def test_zero_deliveries_edge_case():
    # Only depot present
    stops = [DeliveryStopInfo(0, 0, "Depot", 0.0, 0.0, 0.0, 1440.0, 0.0, 0)]
    cost_matrix = [[0.0]]
    duration_matrix = [[0.0]]

    bb_solver = VRPTWBranchAndBound(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=1000.0,
        vehicle_max_volume=10.0
    )
    bb_res = bb_solver.solve()
    assert bb_res.is_feasible
    assert bb_res.optimal_cost == 0.0

    cw_res = solve_clarke_wright_savings(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=1000.0,
        vehicle_max_volume=10.0
    )
    assert len(cw_res.routes) == 0

def test_insufficient_vehicle_capacity_rejection():
    # Package is 1500 kg, vehicle capacity is only 500 kg
    stops = [
        DeliveryStopInfo(0, 0, "Depot", 0.0, 0.0, 0.0, 1440.0, 0.0, 0),
        DeliveryStopInfo(1, 1, "Oversized Cargo", 1500.0, 1.0, 0.0, 1440.0, 10.0, 5)
    ]
    cost_matrix = [[0.0, 20.0], [20.0, 0.0]]
    duration_matrix = [[0.0, 30.0], [30.0, 0.0]]

    bb_solver = VRPTWBranchAndBound(
        cost_matrix=cost_matrix,
        duration_matrix=duration_matrix,
        stops=stops,
        vehicle_max_weight=500.0,
        vehicle_max_volume=5.0
    )
    bb_res = bb_solver.solve()
    # Must prune by capacity and report infeasible
    assert bb_res.pruned_by_capacity > 0

def test_ev_optimizer_handles_depleted_battery():
    graph = RoadNetworkGraph()
    graph.add_node(Node(0, "Depot", "depot", 28.60, 77.20))
    graph.add_node(Node(1, "Customer Far", "customer", 29.50, 78.50)) # ~150 km away
    graph.add_edge(Edge(0, 1, distance_km=150.0, speed_limit_kmh=60.0), bidirectional=True)

    # EV with only 10 kWh battery cannot cover 150 km (consumption 0.22 kWh/km => 33 kWh needed)
    ev_opt = EVRouteOptimizer(
        graph=graph,
        battery_capacity_kwh=10.0,
        initial_soc_kwh=10.0,
        consumption_kwh_per_km=0.22
    )
    ev_plan = ev_opt.optimize_ev_route([0, 1, 0])
    # Must flag battery as infeasible since no intermediate charging stations exist
    assert not ev_plan.is_battery_feasible
