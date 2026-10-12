from typing import List, Dict, Tuple
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph
from app.dsa.dijkstra import dijkstra_shortest_path

@dataclass
class CostMatrices:
    location_node_ids: List[int]
    distance_matrix: List[List[float]] # km
    duration_matrix: List[List[float]] # minutes
    paths_matrix: Dict[Tuple[int, int], List[int]] # Exact sequence of road nodes

def build_cost_matrices(
    graph: RoadNetworkGraph,
    location_node_ids: List[int]
) -> CostMatrices:
    """
    Computes pairwise distance and travel duration matrices for a subset of location nodes
    (e.g., depot + delivery stops) using repeated Dijkstra SSSP.
    Time Complexity: O(K * (V + E) log V), where K = len(location_node_ids).
    """
    k = len(location_node_ids)
    dist_matrix = [[0.0] * k for _ in range(k)]
    dur_matrix = [[0.0] * k for _ in range(k)]
    paths: Dict[Tuple[int, int], List[int]] = {}

    for i, src in enumerate(location_node_ids):
        # Compute shortest duration from src
        res_dur = dijkstra_shortest_path(graph, source=src, cost_metric="duration")
        res_dist = dijkstra_shortest_path(graph, source=src, cost_metric="distance")

        for j, tgt in enumerate(location_node_ids):
            if i == j:
                dist_matrix[i][j] = 0.0
                dur_matrix[i][j] = 0.0
                paths[(src, tgt)] = [src]
            else:
                dur_matrix[i][j] = res_dur.distances.get(tgt, float('inf'))
                dist_matrix[i][j] = res_dist.distances.get(tgt, float('inf'))
                paths[(src, tgt)] = res_dur.get_path_to(tgt)

    return CostMatrices(
        location_node_ids=location_node_ids,
        distance_matrix=dist_matrix,
        duration_matrix=dur_matrix,
        paths_matrix=paths
    )
