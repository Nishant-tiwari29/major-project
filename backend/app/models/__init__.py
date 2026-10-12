from app.core.database import Base
from app.models.fleet import Depot, Vehicle, Driver, DriverAssignment, ChargingStation
from app.models.orders import Customer, DeliveryRequest, Package
from app.models.optimization import OptimizationJob, PlannedRoute, RouteStop, BenchmarkMetric

__all__ = [
    "Base",
    "Depot",
    "Vehicle",
    "Driver",
    "DriverAssignment",
    "ChargingStation",
    "Customer",
    "DeliveryRequest",
    "Package",
    "OptimizationJob",
    "PlannedRoute",
    "RouteStop",
    "BenchmarkMetric"
]
