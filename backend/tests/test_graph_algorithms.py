import pytest
from pathlib import Path
from app.dsa.graph import RoadNetworkGraph, Node, Edge, haversine_distance_km
from app.dsa.dijkstra import dijkstra_shortest_path
from app.dsa.astar import astar_shortest_path
from app.dsa.floyd_warshall import floyd_warshall_apsp
from app.dsa.matrix_builder import build_cost_matrices

@pytest.fixture
def sample_graph():
    network_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_network.json"
    return RoadNetworkGraph.load_from_json(network_path)

def test_haversine_distance():
    # Distance between New Delhi (28.6139, 77.2090) and Connaught Place (28.6328, 77.2197) is ~2.3 km
    d = haversine_distance_km(28.6139, 77.2090, 28.6328, 77.2197)
    assert 2.0 < d < 2.6

def test_dijkstra_shortest_path(sample_graph):
    # From Central Depot (node 0) to Saket (node 8)
    res = dijkstra_shortest_path(sample_graph, source=0, target=8, cost_metric="distance")
    assert res.distances[8] < float('inf')
    path = res.get_path_to(8)
    assert len(path) >= 2
    assert path[0] == 0
    assert path[-1] == 8

def test_astar_matches_dijkstra(sample_graph):
    src, tgt = 0, 8
    dijkstra_res = dijkstra_shortest_path(sample_graph, source=src, target=tgt, cost_metric="distance")
    astar_res = astar_shortest_path(sample_graph, source=src, target=tgt, cost_metric="distance")

    # Both must find the exact same optimal distance
    assert pytest.approx(dijkstra_res.distances[tgt], 0.001) == astar_res.total_cost
    assert astar_res.path[0] == src
    assert astar_res.path[-1] == tgt
    # A* heuristic ensures fewer or equal nodes explored
    assert astar_res.nodes_explored <= dijkstra_res.nodes_explored

def test_floyd_warshall_consistency(sample_graph):
    # Create small subgraph of 5 nodes to test Floyd-Warshall
    fw_res = floyd_warshall_apsp(sample_graph, cost_metric="distance")
    assert not fw_res.has_negative_cycle

    # Cross-verify with Dijkstra from node 0
    dijkstra_res = dijkstra_shortest_path(sample_graph, source=0, cost_metric="distance")
    node_to_idx = {nid: i for i, nid in enumerate(fw_res.nodes)}
    idx_0 = node_to_idx[0]

    for target_id in [5, 6, 21, 3]:
        idx_t = node_to_idx[target_id]
        assert pytest.approx(fw_res.dist_matrix[idx_0][idx_t], 0.001) == dijkstra_res.distances[target_id]

def test_road_closure_rerouting(sample_graph):
    # Baseline path from 0 to 5 is direct: [0, 5]
    base_res = dijkstra_shortest_path(sample_graph, source=0, target=5, cost_metric="distance")
    assert base_res.get_path_to(5) == [0, 5]

    # Close road (0, 5)
    sample_graph.close_edge(0, 5, bidirectional=True)
    detour_res = dijkstra_shortest_path(sample_graph, source=0, target=5, cost_metric="distance")

    # New path must not use (0, 5) directly
    detour_path = detour_res.get_path_to(5)
    assert detour_path != [0, 5]
    assert detour_res.distances[5] > base_res.distances[5]

    # Reset
    sample_graph.reset_conditions()
    reset_res = dijkstra_shortest_path(sample_graph, source=0, target=5, cost_metric="distance")
    assert reset_res.get_path_to(5) == [0, 5]

def test_matrix_builder(sample_graph):
    locations = [0, 5, 6, 8]
    matrices = build_cost_matrices(sample_graph, locations)
    assert len(matrices.distance_matrix) == 4
    assert len(matrices.duration_matrix) == 4
    for i in range(4):
        assert matrices.distance_matrix[i][i] == 0.0
        assert matrices.duration_matrix[i][i] == 0.0
