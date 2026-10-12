import heapq
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from app.dsa.graph import RoadNetworkGraph, haversine_distance_km

@dataclass
class AStarResult:
    source: int
    target: int
    path: List[int]
    total_cost: float
    nodes_explored: int

def astar_shortest_path(
    graph: RoadNetworkGraph,
    source: int,
    target: int,
    cost_metric: str = "duration"
) -> AStarResult:
    """
    Computes optimal shortest path between source and target using A* Search.
    Heuristic:
    - Distance: Great-circle Haversine distance (admissible since straight-line <= road distance).
    - Duration: Haversine distance / graph.max_speed_kmh * 60.0 (admissible since no vehicle exceeds max speed).
    Complexity: O((V + E) log V).
    """
    if source == target:
        return AStarResult(source=source, target=target, path=[source], total_cost=0.0, nodes_explored=1)

    target_node = graph.nodes[target]

    def heuristic(u: int) -> float:
        node = graph.nodes[u]
        dist_km = haversine_distance_km(node.lat, node.lon, target_node.lat, target_node.lon)
        if cost_metric == "distance":
            return dist_km
        else:
            # Minutes at maximum allowable speed
            return (dist_km / graph.max_speed_kmh) * 60.0

    # g_score[u] is the cost of the cheapest path from source to u currently known
    g_score: Dict[int, float] = {nid: float('inf') for nid in graph.nodes}
    g_score[source] = 0.0

    predecessors: Dict[int, Optional[int]] = {nid: None for nid in graph.nodes}

    # Priority Queue stores tuples: (f_score, g_score, u)
    pq: List[Tuple[float, float, int]] = [(heuristic(source), 0.0, source)]
    closed_set = set()
    nodes_explored = 0

    while pq:
        f, curr_g, u = heapq.heappop(pq)

        if u in closed_set:
            continue
        closed_set.add(u)
        nodes_explored += 1

        if u == target:
            # Target reached optimally
            break

        for edge in graph.adj.get(u, []):
            if edge.is_closed:
                continue

            weight = edge.duration_minutes if cost_metric == "duration" else edge.distance_km
            v = edge.target
            tentative_g = curr_g + weight

            if tentative_g < g_score[v]:
                g_score[v] = tentative_g
                predecessors[v] = u
                h_val = heuristic(v)
                heapq.heappush(pq, (tentative_g + h_val, tentative_g, v))

    # Reconstruct path
    path = []
    if g_score[target] != float('inf'):
        curr: Optional[int] = target
        while curr is not None:
            path.append(curr)
            curr = predecessors.get(curr)
        path.reverse()

    return AStarResult(
        source=source,
        target=target,
        path=path,
        total_cost=g_score[target],
        nodes_explored=nodes_explored
    )
