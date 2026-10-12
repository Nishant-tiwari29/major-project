from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from pathlib import Path
import uuid
import datetime

from app.core.database import get_db
from app.models.fleet import Depot, Vehicle
from app.models.orders import DeliveryRequest, Customer, Package
from app.models.optimization import OptimizationJob, PlannedRoute, RouteStop
from app.schemas.route_schema import (
    OptimizationRequest, OptimizationJobResponse, PlannedRouteResponse, RouteStopResponse
)
from app.dsa.graph import RoadNetworkGraph
from app.dsa.matrix_builder import build_cost_matrices
from app.dsa.branch_and_bound import VRPTWBranchAndBound, DeliveryStopInfo
from app.dsa.bitmask_tsp import solve_tsp_bitmask_dp
from app.dsa.clarke_wright import solve_clarke_wright_savings
from app.dsa.multi_objective import MultiObjectiveEvaluator
from app.dsa.ev_optimizer import EVRouteOptimizer

router = APIRouter(prefix="/optimize", tags=["Route Optimization Engine"])

@router.post("/solve", response_model=OptimizationJobResponse)
async def run_optimization(payload: OptimizationRequest, db: AsyncSession = Depends(get_db)):
    # 1. Load Road Graph
    network_path = Path(__file__).resolve().parent.parent.parent.parent / "data" / "sample_network.json"
    graph = RoadNetworkGraph.load_from_json(network_path)

    # 2. Fetch Depot and Vehicles
    depot_res = await db.execute(select(Depot).limit(1))
    depot = depot_res.scalar_one_or_none()
    if not depot:
        raise HTTPException(status_code=400, detail="No depot configured in system.")

    vehicles_res = await db.execute(select(Vehicle).where(Vehicle.is_available == True))
    vehicles = vehicles_res.scalars().all()
    if not vehicles:
        raise HTTPException(status_code=400, detail="No available vehicles found.")

    # 3. Fetch Orders
    orders_res = await db.execute(
        select(DeliveryRequest)
        .options(selectinload(DeliveryRequest.customer), selectinload(DeliveryRequest.packages))
        .where(DeliveryRequest.status == "pending")
    )
    orders = orders_res.scalars().all()
    if not orders:
        raise HTTPException(status_code=400, detail="No pending delivery requests.")

    # Filter orders if order_ids specified, or apply sensible limits for exact exponential algorithms
    if payload.order_ids:
        orders = [o for o in orders if o.id in payload.order_ids]
    elif payload.algorithm_choice == "bitmask_dp":
        orders = orders[:8] # Cap at 8 for sub-second exact DP
    elif payload.algorithm_choice == "branch_and_bound":
        orders = orders[:10] # Cap at 10 for fast exact B&B

    # Map locations to Graph Stops
    # Index 0 is always Depot
    depot_node_id = graph.find_nearest_node(depot.latitude, depot.longitude)
    stops_info = [
        DeliveryStopInfo(
            id=depot.id,
            node_id=depot_node_id,
            name=depot.name,
            weight=0.0,
            volume=0.0,
            earliest_time_min=0.0,
            latest_time_min=1440.0,
            service_time_min=0.0,
            priority=0
        )
    ]

    for ord_req in orders:
        c_node = graph.find_nearest_node(ord_req.customer.latitude, ord_req.customer.longitude)
        tot_w = sum(p.weight_kg for p in ord_req.packages)
        tot_v = sum(p.volume_m3 for p in ord_req.packages)

        # Calculate time windows in minutes from 08:00
        shift_base = ord_req.window_start.replace(hour=8, minute=0, second=0)
        e_min = max(0.0, (ord_req.window_start - shift_base).total_seconds() / 60.0)
        l_min = max(e_min + 30.0, (ord_req.window_end - shift_base).total_seconds() / 60.0)

        stops_info.append(DeliveryStopInfo(
            id=ord_req.id,
            node_id=c_node,
            name=ord_req.customer.name,
            weight=tot_w,
            volume=tot_v,
            earliest_time_min=e_min,
            latest_time_min=l_min,
            service_time_min=ord_req.service_time_min,
            priority=ord_req.priority
        ))

    # 4. Compute Distance & Duration Matrices
    location_nodes = [s.node_id for s in stops_info]
    matrices = build_cost_matrices(graph, location_nodes)

    if payload.traffic_multiplier != 1.0:
        for i in range(len(matrices.duration_matrix)):
            for j in range(len(matrices.duration_matrix[i])):
                matrices.duration_matrix[i][j] *= payload.traffic_multiplier

    primary_vehicle = vehicles[0]
    planned_routes_data: List[PlannedRouteResponse] = []
    dp_sample = None
    search_tree_sample = None
    job_id = str(uuid.uuid4())[:8]
    start_perf = datetime.datetime.utcnow()

    # 5. Algorithm Execution
    if payload.algorithm_choice == "bitmask_dp":
        dp_res = solve_tsp_bitmask_dp(matrices.distance_matrix, include_dp_sample=True)
        dp_sample = dp_res.dp_matrix_sample
        exec_ms = dp_res.execution_time_ms

        # Build single route
        route_stops = []
        curr_t = 0.0
        for order_idx, stop_idx in enumerate(dp_res.optimal_route):
            stop_info = stops_info[stop_idx]
            node = graph.nodes[stop_info.node_id]
            route_stops.append(RouteStopResponse(
                stop_order=order_idx,
                delivery_request_id=stop_info.id if stop_idx != 0 else None,
                stop_type="depot_start" if order_idx == 0 else ("depot_end" if order_idx == len(dp_res.optimal_route)-1 else "delivery"),
                location_name=stop_info.name,
                latitude=node.lat,
                longitude=node.lon,
                waiting_time_min=0.0,
                slack_time_min=15.0
            ))

        cost_bd = MultiObjectiveEvaluator.calculate_cost_breakdown(
            distance_km=dp_res.optimal_cost,
            duration_min=dp_res.optimal_cost * 1.5,
            cost_per_km=primary_vehicle.cost_per_km,
            driver_hourly_rate=22.0,
            emissions_factor_g_per_km=primary_vehicle.emissions_factor_g_co2_per_km
        )

        planned_routes_data.append(PlannedRouteResponse(
            vehicle_id=primary_vehicle.id,
            route_distance_km=round(dp_res.optimal_cost, 2),
            route_duration_min=round(dp_res.optimal_cost * 1.5, 2),
            route_cost=cost_bd.total_cost,
            route_co2_kg=cost_bd.carbon_emissions_kg,
            stops=route_stops
        ))

    elif payload.algorithm_choice == "branch_and_bound":
        bb_solver = VRPTWBranchAndBound(
            cost_matrix=matrices.distance_matrix,
            duration_matrix=matrices.duration_matrix,
            stops=stops_info,
            vehicle_max_weight=primary_vehicle.max_weight_kg,
            vehicle_max_volume=primary_vehicle.max_volume_m3
        )
        bb_res = bb_solver.solve()
        search_tree_sample = bb_res.search_tree_sample
        exec_ms = bb_res.execution_time_ms

        route_stops = []
        for order_idx, stop_idx in enumerate(bb_res.optimal_sequence):
            stop_info = stops_info[stop_idx]
            node = graph.nodes[stop_info.node_id]
            sched = bb_res.schedule[order_idx] if order_idx < len(bb_res.schedule) else None
            route_stops.append(RouteStopResponse(
                stop_order=order_idx,
                delivery_request_id=stop_info.id if stop_idx != 0 else None,
                stop_type="depot_start" if order_idx == 0 else ("depot_end" if order_idx == len(bb_res.optimal_sequence)-1 else "delivery"),
                location_name=stop_info.name,
                latitude=node.lat,
                longitude=node.lon,
                waiting_time_min=sched.waiting_time_min if sched else 0.0,
                slack_time_min=max(0.0, stop_info.latest_time_min - (sched.arrival_time_min if sched else 0.0))
            ))

        dur_est = bb_res.schedule[-1].arrival_time_min if bb_res.schedule else bb_res.optimal_cost * 1.5
        cost_bd = MultiObjectiveEvaluator.calculate_cost_breakdown(
            distance_km=bb_res.optimal_cost,
            duration_min=dur_est,
            cost_per_km=primary_vehicle.cost_per_km,
            driver_hourly_rate=22.0,
            emissions_factor_g_per_km=primary_vehicle.emissions_factor_g_co2_per_km
        )

        planned_routes_data.append(PlannedRouteResponse(
            vehicle_id=primary_vehicle.id,
            route_distance_km=round(bb_res.optimal_cost, 2),
            route_duration_min=round(dur_est, 2),
            route_cost=cost_bd.total_cost,
            route_co2_kg=cost_bd.carbon_emissions_kg,
            stops=route_stops
        ))

    else: # Clarke-Wright (default / multi-vehicle)
        cw_res = solve_clarke_wright_savings(
            cost_matrix=matrices.distance_matrix,
            duration_matrix=matrices.duration_matrix,
            stops=stops_info,
            vehicle_max_weight=primary_vehicle.max_weight_kg,
            vehicle_max_volume=primary_vehicle.max_volume_m3,
            num_vehicles=len(vehicles)
        )
        exec_ms = cw_res.execution_time_ms

        for v_route in cw_res.routes:
            veh = vehicles[v_route.vehicle_idx % len(vehicles)]
            route_stops = []

            # Optional EV Optimization for electric vehicles
            route_node_ids = [stops_info[s_idx].node_id for s_idx in v_route.stops_sequence]
            if veh.is_electric and payload.include_ev_charging:
                ev_opt = EVRouteOptimizer(graph, battery_capacity_kwh=veh.battery_capacity_kwh)
                ev_plan = ev_opt.optimize_ev_route(route_node_ids)
            else:
                ev_plan = None

            for order_idx, stop_idx in enumerate(v_route.stops_sequence):
                stop_info = stops_info[stop_idx]
                node = graph.nodes[stop_info.node_id]
                sched = v_route.schedule[order_idx] if order_idx < len(v_route.schedule) else None
                route_stops.append(RouteStopResponse(
                    stop_order=order_idx,
                    delivery_request_id=stop_info.id if stop_idx != 0 else None,
                    stop_type="depot_start" if order_idx == 0 else ("depot_end" if order_idx == len(v_route.stops_sequence)-1 else "delivery"),
                    location_name=stop_info.name,
                    latitude=node.lat,
                    longitude=node.lon,
                    waiting_time_min=sched.waiting_time_min if sched else 0.0,
                    slack_time_min=max(0.0, stop_info.latest_time_min - (sched.arrival_time_min if sched else 0.0)),
                    remaining_battery_kwh=ev_plan.final_soc_kwh if (ev_plan and order_idx == len(v_route.stops_sequence)-1) else None
                ))

            cost_bd = MultiObjectiveEvaluator.calculate_cost_breakdown(
                distance_km=v_route.total_distance,
                duration_min=v_route.total_duration,
                cost_per_km=veh.cost_per_km,
                driver_hourly_rate=22.0,
                emissions_factor_g_per_km=veh.emissions_factor_g_co2_per_km
            )

            planned_routes_data.append(PlannedRouteResponse(
                vehicle_id=veh.id,
                route_distance_km=v_route.total_distance,
                route_duration_min=v_route.total_duration,
                route_cost=cost_bd.total_cost,
                route_co2_kg=cost_bd.carbon_emissions_kg,
                stops=route_stops
            ))

    total_dist = sum(r.route_distance_km for r in planned_routes_data)
    total_dur = sum(r.route_duration_min for r in planned_routes_data)
    total_cost = sum(r.route_cost for r in planned_routes_data)
    total_co2 = sum(r.route_co2_kg for r in planned_routes_data)

    # Multi-Objective Evaluation
    obj_eval = MultiObjectiveEvaluator.evaluate(
        distance_km=total_dist,
        duration_min=total_dur,
        cost=total_cost,
        emissions_kg=total_co2,
        penalty_cost=0.0,
        mode=payload.objective_mode
    )

    return OptimizationJobResponse(
        id=f"job_{job_id}",
        created_at=start_perf,
        objective_mode=payload.objective_mode,
        algorithm_name=payload.algorithm_choice,
        total_distance_km=round(total_dist, 2),
        total_duration_min=round(total_dur, 2),
        total_cost=round(total_cost, 2),
        total_co2_kg=round(total_co2, 2),
        violation_count=0,
        status="completed",
        execution_time_ms=round(exec_ms, 2),
        routes=planned_routes_data,
        dp_matrix_sample=dp_sample,
        search_tree_sample=search_tree_sample
    )
