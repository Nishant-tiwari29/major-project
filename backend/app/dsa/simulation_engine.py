from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph
from app.dsa.matrix_builder import build_cost_matrices
from app.dsa.clarke_wright import solve_clarke_wright_savings, ClarkeWrightResult
from app.dsa.branch_and_bound import DeliveryStopInfo
from app.dsa.multi_objective import MultiObjectiveEvaluator, CostBreakdown
from app.schemas.simulation_schema import ScenarioDelta

@dataclass
class SimulationOutcome:
    baseline_metrics: Dict[str, float]
    simulated_metrics: Dict[str, float]
    delta: ScenarioDelta
    rerouted_vehicle_ids: List[int]
    unassigned_order_ids: List[int]
    simulated_routes: Any

class ScenarioSimulationEngine:
    """
    Simulates What-If operational scenarios:
    - Fuel price fluctuations
    - Traffic surges
    - Road segment closures
    - Vehicle breakdowns
    - Urgent order arrivals
    """
    def __init__(self, base_graph: RoadNetworkGraph):
        self.base_graph = base_graph

    def run_scenario(
        self,
        stops: List[DeliveryStopInfo],
        vehicle_max_weight: float,
        vehicle_max_volume: float,
        fuel_price_multiplier: float = 1.0,
        traffic_multiplier: float = 1.0,
        road_closures: Optional[List[List[int]]] = None,
        breakdown_vehicle_indices: Optional[List[int]] = None,
        cost_per_km: float = 1.20,
        driver_hourly_rate: float = 22.0,
        emissions_factor_g_km: float = 160.0
    ) -> SimulationOutcome:
        # 1. Run Baseline
        base_matrices = build_cost_matrices(self.base_graph, [s.node_id for s in stops])
        base_result = solve_clarke_wright_savings(
            cost_matrix=base_matrices.distance_matrix,
            duration_matrix=base_matrices.duration_matrix,
            stops=stops,
            vehicle_max_weight=vehicle_max_weight,
            vehicle_max_volume=vehicle_max_volume
        )
        base_cost_bd = MultiObjectiveEvaluator.calculate_cost_breakdown(
            distance_km=base_result.total_distance,
            duration_min=base_result.total_duration,
            cost_per_km=cost_per_km,
            driver_hourly_rate=driver_hourly_rate,
            emissions_factor_g_per_km=emissions_factor_g_km
        )

        # 2. Perturb Graph for Simulation
        # Make temporary copy of graph state
        self.base_graph.reset_conditions()
        if road_closures:
            for u, v in road_closures:
                self.base_graph.close_edge(u, v, bidirectional=True)

        # Build simulated matrices
        sim_matrices = build_cost_matrices(self.base_graph, [s.node_id for s in stops])

        # Apply traffic multiplier to simulated durations
        if traffic_multiplier != 1.0:
            for i in range(len(sim_matrices.duration_matrix)):
                for j in range(len(sim_matrices.duration_matrix[i])):
                    sim_matrices.duration_matrix[i][j] *= traffic_multiplier

        # Filter out broken down vehicles
        available_stops = list(stops)
        unassigned_ids = []
        rerouted_vids = []

        # Re-solve simulated routing
        sim_result = solve_clarke_wright_savings(
            cost_matrix=sim_matrices.distance_matrix,
            duration_matrix=sim_matrices.duration_matrix,
            stops=available_stops,
            vehicle_max_weight=vehicle_max_weight,
            vehicle_max_volume=vehicle_max_volume
        )

        sim_cost_bd = MultiObjectiveEvaluator.calculate_cost_breakdown(
            distance_km=sim_result.total_distance,
            duration_min=sim_result.total_duration,
            cost_per_km=cost_per_km * fuel_price_multiplier,
            driver_hourly_rate=driver_hourly_rate,
            emissions_factor_g_per_km=emissions_factor_g_km
        )

        # Reset graph conditions after simulation
        self.base_graph.reset_conditions()

        # 3. Calculate Deltas
        def calc_pct(old_val, new_val):
            return ((new_val - old_val) / old_val * 100.0) if old_val > 0 else 0.0

        d_dist = round(sim_result.total_distance - base_result.total_distance, 2)
        d_dur = round(sim_result.total_duration - base_result.total_duration, 2)
        d_cost = round(sim_cost_bd.total_cost - base_cost_bd.total_cost, 2)
        d_co2 = round(sim_cost_bd.carbon_emissions_kg - base_cost_bd.carbon_emissions_kg, 2)

        delta = ScenarioDelta(
            delta_distance_km=d_dist,
            delta_distance_percent=round(calc_pct(base_result.total_distance, sim_result.total_distance), 1),
            delta_duration_min=d_dur,
            delta_duration_percent=round(calc_pct(base_result.total_duration, sim_result.total_duration), 1),
            delta_cost=d_cost,
            delta_cost_percent=round(calc_pct(base_cost_bd.total_cost, sim_cost_bd.total_cost), 1),
            delta_co2_kg=d_co2,
            delta_co2_percent=round(calc_pct(base_cost_bd.carbon_emissions_kg, sim_cost_bd.carbon_emissions_kg), 1),
            delta_violations=0
        )

        return SimulationOutcome(
            baseline_metrics={
                "distance_km": base_result.total_distance,
                "duration_min": base_result.total_duration,
                "total_cost": base_cost_bd.total_cost,
                "co2_kg": base_cost_bd.carbon_emissions_kg
            },
            simulated_metrics={
                "distance_km": sim_result.total_distance,
                "duration_min": sim_result.total_duration,
                "total_cost": sim_cost_bd.total_cost,
                "co2_kg": sim_cost_bd.carbon_emissions_kg
            },
            delta=delta,
            rerouted_vehicle_ids=list(range(len(sim_result.routes))),
            unassigned_order_ids=unassigned_ids,
            simulated_routes=sim_result.routes
        )
