from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.fleet_schema import VehicleResponse
from app.schemas.order_schema import DeliveryRequestResponse

class RouteStopResponse(BaseModel):
    id: Optional[int] = None
    stop_order: int
    delivery_request_id: Optional[int] = None
    stop_type: str # depot_start, delivery, charging, depot_end
    location_name: Optional[str] = None
    latitude: float
    longitude: float
    estimated_arrival: Optional[datetime] = None
    estimated_departure: Optional[datetime] = None
    waiting_time_min: float = 0.0
    slack_time_min: float = 0.0
    remaining_battery_kwh: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class PlannedRouteResponse(BaseModel):
    id: Optional[int] = None
    vehicle_id: int
    vehicle: Optional[VehicleResponse] = None
    route_distance_km: float
    route_duration_min: float
    route_cost: float
    route_co2_kg: float
    summary_polyline: Optional[str] = None
    stops: List[RouteStopResponse] = []
    model_config = ConfigDict(from_attributes=True)

class OptimizationJobResponse(BaseModel):
    id: str
    created_at: datetime
    objective_mode: str
    algorithm_name: str
    total_distance_km: float
    total_duration_min: float
    total_cost: float
    total_co2_kg: float
    violation_count: int
    status: str
    execution_time_ms: float
    routes: List[PlannedRouteResponse] = []
    dp_matrix_sample: Optional[Any] = None # For DP visualizer
    search_tree_sample: Optional[Any] = None # For B&B tree visualizer
    model_config = ConfigDict(from_attributes=True)

class OptimizationRequest(BaseModel):
    depot_ids: Optional[List[int]] = None
    vehicle_ids: Optional[List[int]] = None
    order_ids: Optional[List[int]] = None
    objective_mode: str = "balanced" # balanced, cheapest, fastest, greenest, shortest
    algorithm_choice: str = "branch_and_bound" # bitmask_dp, branch_and_bound, clarke_wright, nearest_neighbor
    include_ev_charging: bool = True
    traffic_multiplier: float = 1.0

class BenchmarkRequest(BaseModel):
    instance_size: int = 10 # Number of delivery locations
    algorithms: List[str] = ["bitmask_dp", "branch_and_bound", "clarke_wright", "nearest_neighbor"]
    objective_mode: str = "balanced"

class AlgorithmBenchmarkResult(BaseModel):
    algorithm_name: str
    execution_time_ms: float
    memory_usage_kb: float
    states_explored: int
    solution_cost: float
    total_distance_km: float
    total_duration_min: float
    optimality_gap_percent: float
    is_optimal_guaranteed: bool

class BenchmarkResponse(BaseModel):
    instance_size: int
    results: List[AlgorithmBenchmarkResult]
