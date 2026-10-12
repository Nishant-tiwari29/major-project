from pydantic import BaseModel
from typing import Optional, List, Dict
from app.schemas.route_schema import OptimizationJobResponse

class ScenarioSimulationRequest(BaseModel):
    baseline_job_id: Optional[str] = None
    fuel_price_multiplier: float = 1.0
    traffic_multiplier: float = 1.0
    road_closures: List[List[int]] = [] # Pairs of node IDs [u, v]
    breakdown_vehicle_ids: List[int] = []
    urgent_order_count: int = 0
    objective_mode: str = "balanced"

class ScenarioDelta(BaseModel):
    delta_distance_km: float
    delta_distance_percent: float
    delta_duration_min: float
    delta_duration_percent: float
    delta_cost: float
    delta_cost_percent: float
    delta_co2_kg: float
    delta_co2_percent: float
    delta_violations: int

class ScenarioSimulationResponse(BaseModel):
    baseline_plan: OptimizationJobResponse
    simulated_plan: OptimizationJobResponse
    delta: ScenarioDelta
    rerouted_vehicle_ids: List[int]
    unassigned_order_ids: List[int]
