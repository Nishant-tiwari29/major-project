from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph

@dataclass
class FloydWarshallResult:
    nodes: List[int]
    dist_matrix: List[List[float]]
    next_node: List[List[Optional[int]]]
    has_negative_cycle: bool

    def get_path(self, u: int, v: int) -> List[int]:
        node_to_idx = {nid: i for i, nid in enumerate(self.nodes)}
        if u not in node_to_idx or v not in node_to_idx:
            return []
        i, j = node_to_idx[u], node_to_idx[v]
        if self.dist_matrix[i][j] == float('inf'):
            return []
        path = [u]
        while i != j:
            next_idx = self.next_node[i][j]
            if next_idx is None:
                return []
            path.append(self.nodes[next_idx])
            i = next_idx
        return path

def floyd_warshall_apsp(
    graph: RoadNetworkGraph,
    cost_metric: str = "duration"
) -> FloydWarshallResult:
    """
    Computes All-Pairs Shortest Path (APSP) using Floyd-Warshall dynamic programming.
    Recurrence: D[k][i][j] = min(D[k-1][i][j], D[k-1][i][k] + D[k-1][k][j])
    Complexity: O(V^3) time, O(V^2) space.
    """
    nodes = sorted(list(graph.nodes.keys()))
    n = len(nodes)
    node_to_idx = {nid: i for i, nid in enumerate(nodes)}

    dist = [[float('inf')] * n for _ in range(n)]
    next_node: List[List[Optional[int]]] = [[None] * n for _ in range(n)]

    for i in range(n):
        dist[i][i] = 0.0
        next_node[i][i] = i

    for u, edges in graph.adj.items():
        if u not in node_to_idx:
            continue
        i = node_to_idx[u]
        for edge in edges:
            if edge.is_closed:
                continue
            if edge.target not in node_to_idx:
                continue
            j = node_to_idx[edge.target]
            weight = edge.duration_minutes if cost_metric == "duration" else edge.distance_km
            if weight < dist[i][j]:
                dist[i][j] = weight
                next_node[i][j] = j

    # DP 3-loop relaxation
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    next_node[i][j] = next_node[i][k]

    # Negative cycle check
    has_negative_cycle = any(dist[i][i] < 0 for i in range(n))

    return FloydWarshallResult(
        nodes=nodes,
        dist_matrix=dist,
        next_node=next_node,
        has_negative_cycle=has_negative_cycle
    )
