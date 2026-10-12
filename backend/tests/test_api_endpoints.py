import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_root_and_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_root = await ac.get("/")
        assert r_root.status_code == 200
        if "application/json" in r_root.headers.get("content-type", ""):
            assert r_root.json()["status"] == "online"
        else:
            assert "html" in r_root.headers.get("content-type", "").lower()

        r_health = await ac.get("/health")
        assert r_health.status_code == 200
        assert r_health.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_fleet_and_orders():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r_depots = await ac.get("/api/v1/fleet/depots")
        assert r_depots.status_code == 200
        assert len(r_depots.json()) > 0

        r_vehicles = await ac.get("/api/v1/fleet/vehicles")
        assert r_vehicles.status_code == 200
        assert len(r_vehicles.json()) > 0

        r_orders = await ac.get("/api/v1/orders/pending")
        assert r_orders.status_code == 200
        assert len(r_orders.json()) > 0

@pytest.mark.asyncio
async def test_optimization_solve_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Test Bitmask DP
        res_dp = await ac.post("/api/v1/optimize/solve", json={
            "objective_mode": "balanced",
            "algorithm_choice": "bitmask_dp",
            "include_ev_charging": False,
            "traffic_multiplier": 1.0
        })
        assert res_dp.status_code == 200
        data_dp = res_dp.json()
        assert data_dp["total_distance_km"] > 0
        assert data_dp["dp_matrix_sample"] is not None
        assert len(data_dp["routes"]) > 0

        # 2. Test Branch and Bound
        res_bb = await ac.post("/api/v1/optimize/solve", json={
            "objective_mode": "cheapest",
            "algorithm_choice": "branch_and_bound",
            "include_ev_charging": False,
            "traffic_multiplier": 1.0
        })
        assert res_bb.status_code == 200
        data_bb = res_bb.json()
        assert data_bb["total_distance_km"] > 0
        assert data_bb["search_tree_sample"] is not None

        # 3. Test Clarke Wright
        res_cw = await ac.post("/api/v1/optimize/solve", json={
            "objective_mode": "greenest",
            "algorithm_choice": "clarke_wright",
            "include_ev_charging": True,
            "traffic_multiplier": 1.0
        })
        assert res_cw.status_code == 200
        data_cw = res_cw.json()
        assert data_cw["total_distance_km"] > 0

@pytest.mark.asyncio
async def test_benchmark_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/benchmark/run", json={
            "instance_size": 5,
            "algorithms": ["bitmask_dp", "branch_and_bound", "clarke_wright", "nearest_neighbor"]
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 4
        # Assert Bitmask DP has 0% gap
        dp_entry = next(r for r in data["results"] if "Bitmask DP" in r["algorithm_name"])
        assert dp_entry["optimality_gap_percent"] == 0.0

@pytest.mark.asyncio
async def test_simulation_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/simulate/scenario", json={
            "fuel_price_multiplier": 1.25,
            "traffic_multiplier": 1.30,
            "road_closures": [[0, 5]]
        })
        assert res.status_code == 200
        data = res.json()
        assert "delta" in data
        assert data["simulated_plan"]["total_cost"] > 0

@pytest.mark.asyncio
async def test_ml_predict_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/ml/predict-edge", json={
            "distance_km": 10.5,
            "speed_limit_kmh": 50.0,
            "hour_of_day": 9,
            "day_of_week": 1,
            "weather": "rain",
            "congestion_index": 2.0
        })
        assert res.status_code == 200
        data = res.json()
        assert data["predicted_duration_minutes"] > 0
