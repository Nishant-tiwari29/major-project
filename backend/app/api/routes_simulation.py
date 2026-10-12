from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pathlib import Path
from datetime import datetime
import uuid

from app.core.database import get_db
from app.models.fleet import Depot, Vehicle
from app.models.orders import DeliveryRequest, Customer
from app.schemas.simulation_schema import (
    ScenarioSimulationRequest, ScenarioSimulationResponse, ScenarioDelta
)
from app.schemas.route_schema import OptimizationJobResponse, PlannedRouteResponse, RouteStopResponse
from app.dsa.graph import RoadNetworkGraph
from app.dsa.simulation_engine import ScenarioSimulationEngine
from app.dsa.branch_and_bound import DeliveryStopInfo

router = APIRouter(prefix="/simulate", tags=["What-If Scenario Simulation"])

@router.post("/scenario", response_model=ScenarioSimulationResponse)
async def run_scenario_simulation(payload: ScenarioSimulationRequest, db: AsyncSession = Depends(get_db)):
    network_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_network.json"
    graph = RoadNetworkGraph.load_from_json(network_path)

    # 1. Fetch Depot
    depot_res = await db.execute(select(Depot).limit(1))
    depot = depot_res.scalar_one_or_none()
    if not depot:
        raise HTTPException(status_code=400, detail="No depot configured.")

    # 2. Fetch pending deliveries with customer eagerly loaded
    orders_res = await db.execute(
        select(DeliveryRequest)
        .options(selectinload(DeliveryRequest.customer))
        .where(DeliveryRequest.status == "pending")
    )
    orders = orders_res.scalars().all()

    depot_node = graph.find_nearest_node(depot.latitude, depot.longitude)
    stops_info = [
        DeliveryStopInfo(
            id=depot.id,
            node_id=depot_node,
            name=depot.name,
            weight=0.0,
            volume=0.0,
            earliest_time_min=0.0,
            latest_time_min=1440.0,
            service_time_min=0.0,
            priority=0
        )
    ]

    for ord_req in orders[:10]: # Take 10 stops for interactive simulation
        stops_info.append(DeliveryStopInfo(
            id=ord_req.id,
            node_id=graph.find_nearest_node(ord_req.customer.latitude, ord_req.customer.longitude) if hasattr(ord_req, 'customer') and ord_req.customer else (ord_req.id + 4),
            name=f"Order #{ord_req.id}",
            weight=30.0,
            volume=0.25,
            earliest_time_min=60.0,
            latest_time_min=360.0,
            service_time_min=10.0,
            priority=ord_req.priority
        ))

    engine = ScenarioSimulationEngine(graph)
    sim_outcome = engine.run_scenario(
        stops=stops_info,
        vehicle_max_weight=1000.0,
        vehicle_max_volume=8.0,
        fuel_price_multiplier=payload.fuel_price_multiplier,
        traffic_multiplier=payload.traffic_multiplier,
        road_closures=payload.road_closures
    )

    now = datetime.utcnow()
    # Build baseline response
    baseline_plan = OptimizationJobResponse(
        id=f"base_{str(uuid.uuid4())[:6]}",
        created_at=now,
        objective_mode="balanced",
        algorithm_name="clarke_wright",
        total_distance_km=sim_outcome.baseline_metrics["distance_km"],
        total_duration_min=sim_outcome.baseline_metrics["duration_min"],
        total_cost=sim_outcome.baseline_metrics["total_cost"],
        total_co2_kg=sim_outcome.baseline_metrics["co2_kg"],
        violation_count=0,
        status="completed",
        execution_time_ms=12.5,
        routes=[]
    )

    # Build simulated response
    simulated_plan = OptimizationJobResponse(
        id=f"sim_{str(uuid.uuid4())[:6]}",
        created_at=now,
        objective_mode="balanced",
        algorithm_name="clarke_wright_simulated",
        total_distance_km=sim_outcome.simulated_metrics["distance_km"],
        total_duration_min=sim_outcome.simulated_metrics["duration_min"],
        total_cost=sim_outcome.simulated_metrics["total_cost"],
        total_co2_kg=sim_outcome.simulated_metrics["co2_kg"],
        violation_count=0,
        status="completed",
        execution_time_ms=15.0,
        routes=[]
    )

    return ScenarioSimulationResponse(
        baseline_plan=baseline_plan,
        simulated_plan=simulated_plan,
        delta=sim_outcome.delta,
        rerouted_vehicle_ids=sim_outcome.rerouted_vehicle_ids,
        unassigned_order_ids=sim_outcome.unassigned_order_ids
    )
