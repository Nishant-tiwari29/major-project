import math
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes the great-circle distance between two points on Earth using Haversine formula."""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@dataclass
class Node:
    id: int
    name: str
    node_type: str # depot, customer, charging, intersection
    lat: float
    lon: float
    elevation_m: float = 0.0

@dataclass
class Edge:
    source: int
    target: int
    distance_km: float
    speed_limit_kmh: float = 50.0
    toll_cost: float = 0.0
    elevation_change_m: float = 0.0
    congestion_multiplier: float = 1.0
    is_closed: bool = False

    @property
    def effective_speed_kmh(self) -> float:
        return max(5.0, self.speed_limit_kmh / self.congestion_multiplier)

    @property
    def duration_minutes(self) -> float:
        """Calculates travel duration in minutes given effective speed."""
        if self.is_closed:
            return float('inf')
        return (self.distance_km / self.effective_speed_kmh) * 60.0

    @property
    def traversal_cost(self) -> float:
        if self.is_closed:
            return float('inf')
        return self.distance_km

class RoadNetworkGraph:
    """
    Weighted directed graph representation of the road network using an adjacency list.
    Supports dynamic updates (road closures, traffic congestion) and shortest path queries.
    """
    def __init__(self):
        self.nodes: Dict[int, Node] = {}
        self.adj: Dict[int, List[Edge]] = {}
        self.max_speed_kmh: float = 80.0

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self.adj:
            self.adj[node.id] = []

    def add_edge(self, edge: Edge, bidirectional: bool = False):
        if edge.source not in self.adj:
            self.adj[edge.source] = []
        self.adj[edge.source].append(edge)
        self.max_speed_kmh = max(self.max_speed_kmh, edge.speed_limit_kmh)

        if bidirectional:
            reverse_edge = Edge(
                source=edge.target,
                target=edge.source,
                distance_km=edge.distance_km,
                speed_limit_kmh=edge.speed_limit_kmh,
                toll_cost=edge.toll_cost,
                elevation_change_m=-edge.elevation_change_m,
                congestion_multiplier=edge.congestion_multiplier,
                is_closed=edge.is_closed
            )
            if edge.target not in self.adj:
                self.adj[edge.target] = []
            self.adj[edge.target].append(reverse_edge)

    def close_edge(self, source: int, target: int, bidirectional: bool = True):
        """Simulates road closure by setting edge closed status."""
        for edge in self.adj.get(source, []):
            if edge.target == target:
                edge.is_closed = True
        if bidirectional:
            for edge in self.adj.get(target, []):
                if edge.target == source:
                    edge.is_closed = True

    def set_congestion(self, source: int, target: int, multiplier: float, bidirectional: bool = True):
        """Simulates traffic congestion on an edge."""
        for edge in self.adj.get(source, []):
            if edge.target == target:
                edge.congestion_multiplier = multiplier
        if bidirectional:
            for edge in self.adj.get(target, []):
                if edge.target == source:
                    edge.congestion_multiplier = multiplier

    def reset_conditions(self):
        """Resets all closures and congestion multipliers to baseline."""
        for edges in self.adj.values():
            for edge in edges:
                edge.is_closed = False
                edge.congestion_multiplier = 1.0

    @classmethod
    def load_from_json(cls, filepath: str | Path) -> "RoadNetworkGraph":
        graph = cls()
        with open(filepath, "r") as f:
            data = json.load(f)
        for n in data["nodes"]:
            graph.add_node(Node(
                id=n["id"],
                name=n["name"],
                node_type=n.get("type", "intersection"),
                lat=n["lat"],
                lon=n["lon"],
                elevation_m=n.get("elevation_m", 0.0)
            ))
        for e in data["edges"]:
            graph.add_edge(Edge(
                source=e["source"],
                target=e["target"],
                distance_km=e["distance_km"],
                speed_limit_kmh=e.get("speed_limit_kmh", 50.0),
                toll_cost=e.get("toll_cost", 0.0),
                elevation_change_m=e.get("elevation_change_m", 0.0)
            ), bidirectional=False)
        return graph

    def find_nearest_node(self, lat: float, lon: float) -> int:
        """Finds the graph node closest to given GPS coordinates."""
        best_id = -1
        best_dist = float('inf')
        for nid, node in self.nodes.items():
            d = haversine_distance_km(lat, lon, node.lat, node.lon)
            if d < best_dist:
                best_dist = d
                best_id = nid
        return best_id
