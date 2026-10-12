from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph, haversine_distance_km
from app.dsa.dijkstra import dijkstra_shortest_path
from app.core.config import settings

@dataclass
class ChargingStopDetail:
    station_node_id: int
    station_name: str
    arrival_soc_kwh: float
    energy_charged_kwh: float
    charging_duration_min: float
    charging_cost: float
    inserted_after_stop_idx: int

@dataclass
class EVRoutePlan:
    original_route_nodes: List[int]
    augmented_route_nodes: List[int]
    charging_stops: List[ChargingStopDetail]
    final_soc_kwh: float
    total_charging_cost: float
    total_charging_duration_min: float
    is_battery_feasible: bool

class EVRouteOptimizer:
    """
    Simulates and optimizes electric vehicle routes with State-of-Charge (SoC) tracking,
    minimum battery reserve enforcement, and automated charging station detour insertion.
    """
    def __init__(
        self,
        graph: RoadNetworkGraph,
        battery_capacity_kwh: float = 60.0,
        initial_soc_kwh: float = 60.0,
        consumption_kwh_per_km: float = 0.22,
        min_reserve_ratio: float = 0.15 # 15% reserve
    ):
        self.graph = graph
        self.capacity_kwh = battery_capacity_kwh
        self.initial_soc_kwh = initial_soc_kwh
        self.consumption = consumption_kwh_per_km
        self.min_reserve_kwh = battery_capacity_kwh * min_reserve_ratio

        # Find all charging station nodes in the graph
        self.charging_stations = [
            n for n in graph.nodes.values() if n.node_type == "charging"
        ]

    def optimize_ev_route(
        self,
        route_nodes: List[int]
    ) -> EVRoutePlan:
        """
        Inspects route segment by segment. If next stop drops SoC below min_reserve_kwh,
        finds the closest available fast charger and inserts a charging detour.
        """
        if not route_nodes:
            return EVRoutePlan([], [], [], self.initial_soc_kwh, 0.0, 0.0, True)

        current_soc = self.initial_soc_kwh
        augmented_nodes = [route_nodes[0]]
        charging_stops: List[ChargingStopDetail] = []
        tot_charge_cost = 0.0
        tot_charge_dur = 0.0
        feasible = True

        for i in range(len(route_nodes) - 1):
            u = augmented_nodes[-1]
            v = route_nodes[i + 1]

            # Shortest path between u and v
            dijk = dijkstra_shortest_path(self.graph, source=u, target=v, cost_metric="distance")
            leg_distance = dijk.distances.get(v, 0.0)
            energy_needed = leg_distance * self.consumption

            if (current_soc - energy_needed) < self.min_reserve_kwh:
                # Need to charge before or at u! Find closest charging station to u
                best_station = None
                best_station_dist = float('inf')

                for station in self.charging_stations:
                    d_stat = dijkstra_shortest_path(self.graph, source=u, target=station.id, cost_metric="distance")
                    dist_to_stat = d_stat.distances.get(station.id, float('inf'))
                    if dist_to_stat < best_station_dist:
                        best_station_dist = dist_to_stat
                        best_station = station

                if best_station is not None and (current_soc - (best_station_dist * self.consumption)) >= 0:
                    arr_soc = max(0.0, current_soc - (best_station_dist * self.consumption))
                    # Charge up to 90% capacity for battery longevity
                    target_soc = self.capacity_kwh * 0.90
                    kwh_charged = max(0.0, target_soc - arr_soc)

                    # 100 kW DC fast charger: time in min = (kWh / 100) * 60
                    dur_min = (kwh_charged / 100.0) * 60.0
                    cost = kwh_charged * settings.DEFAULT_ELECTRICITY_COST_PER_KWH

                    charging_detail = ChargingStopDetail(
                        station_node_id=best_station.id,
                        station_name=best_station.name,
                        arrival_soc_kwh=round(arr_soc, 2),
                        energy_charged_kwh=round(kwh_charged, 2),
                        charging_duration_min=round(dur_min, 1),
                        charging_cost=round(cost, 2),
                        inserted_after_stop_idx=len(augmented_nodes) - 1
                    )
                    charging_stops.append(charging_detail)
                    tot_charge_cost += cost
                    tot_charge_dur += dur_min

                    # Insert charging station into route
                    augmented_nodes.append(best_station.id)
                    current_soc = target_soc

                    # Now travel from station to target v
                    d_from_station = dijkstra_shortest_path(self.graph, source=best_station.id, target=v, cost_metric="distance")
                    dist_stat_v = d_from_station.distances.get(v, 0.0)
                    current_soc -= (dist_stat_v * self.consumption)
                else:
                    # Vehicle stranded (infeasible range)
                    feasible = False
                    current_soc = max(0.0, current_soc - energy_needed)
            else:
                current_soc -= energy_needed

            augmented_nodes.append(v)

        return EVRoutePlan(
            original_route_nodes=route_nodes,
            augmented_route_nodes=augmented_nodes,
            charging_stops=charging_stops,
            final_soc_kwh=round(current_soc, 2),
            total_charging_cost=round(tot_charge_cost, 2),
            total_charging_duration_min=round(tot_charge_dur, 2),
            is_battery_feasible=feasible and (current_soc >= self.min_reserve_kwh)
        )
