import heapq
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph

@dataclass
class DijkstraResult:
    source: int
    distances: Dict[int, float]
    predecessors: Dict[int, Optional[int]]
    nodes_explored: int

    def get_path_to(self, target: int) -> List[int]:
        if target not in self.distances or self.distances[target] == float('inf'):
            return []
        path = []
        curr: Optional[int] = target
        while curr is not None:
            path.append(curr)
            curr = self.predecessors.get(curr)
        path.reverse()
        return path if path and path[0] == self.source else []

def dijkstra_shortest_path(
    graph: RoadNetworkGraph,
    source: int,
    target: Optional[int] = None,
    cost_metric: str = "duration" # "duration" or "distance"
) -> DijkstraResult:
    """
    Executes Dijkstra's algorithm from a single source node.
    - If target is specified, terminates early when target is extracted from min-heap.
    - Complexity: O((V + E) log V).
    """
    distances: Dict[int, float] = {nid: float('inf') for nid in graph.nodes}
    predecessors: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}
    distances[source] = 0.0

    # Min-Heap stores tuples: (distance, node_id)
    pq: List[Tuple[float, int]] = [(0.0, source)]
    visited = set()
    nodes_explored = 0

    while pq:
        curr_dist, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)
        nodes_explored += 1

        if target is not None and u == target:
            break

        if curr_dist > distances[u]:
            continue

        for edge in graph.adj.get(u, []):
            if edge.is_closed:
                continue

            weight = edge.duration_minutes if cost_metric == "duration" else edge.distance_km
            v = edge.target
            new_dist = curr_dist + weight

            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    return DijkstraResult(
        source=source,
        distances=distances,
        predecessors=predecessors,
        nodes_explored=nodes_explored
    )
