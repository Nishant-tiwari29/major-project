from fastapi import APIRouter
from app.api.routes_fleet import router as fleet_router
from app.api.routes_orders import router as orders_router
from app.api.routes_routing import router as routing_router
from app.api.routes_benchmark import router as benchmark_router
from app.api.routes_simulation import router as simulation_router
from app.api.routes_ml import router as ml_router

api_router = APIRouter()
api_router.include_router(fleet_router)
api_router.include_router(orders_router)
api_router.include_router(routing_router)
api_router.include_router(benchmark_router)
api_router.include_router(simulation_router)
api_router.include_router(ml_router)
