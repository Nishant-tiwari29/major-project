from app.schemas.fleet_schema import (
    DepotBase, DepotCreate, DepotResponse,
    VehicleBase, VehicleCreate, VehicleResponse,
    DriverBase, DriverResponse,
    ChargingStationBase, ChargingStationResponse
)
from app.schemas.order_schema import (
    CustomerBase, CustomerCreate, CustomerResponse,
    PackageBase, PackageCreate, PackageResponse,
    DeliveryRequestBase, DeliveryRequestCreate, DeliveryRequestResponse
)
from app.schemas.route_schema import (
    RouteStopResponse, PlannedRouteResponse,
    OptimizationJobResponse, OptimizationRequest,
    BenchmarkRequest, BenchmarkResponse, AlgorithmBenchmarkResult
)
from app.schemas.simulation_schema import (
    ScenarioSimulationRequest, ScenarioSimulationResponse, ScenarioDelta
)

__all__ = [
    "DepotBase", "DepotCreate", "DepotResponse",
    "VehicleBase", "VehicleCreate", "VehicleResponse",
    "DriverBase", "DriverResponse",
    "ChargingStationBase", "ChargingStationResponse",
    "CustomerBase", "CustomerCreate", "CustomerResponse",
    "PackageBase", "PackageCreate", "PackageResponse",
    "DeliveryRequestBase", "DeliveryRequestCreate", "DeliveryRequestResponse",
    "RouteStopResponse", "PlannedRouteResponse",
    "OptimizationJobResponse", "OptimizationRequest",
    "BenchmarkRequest", "BenchmarkResponse", "AlgorithmBenchmarkResult",
    "ScenarioSimulationRequest", "ScenarioSimulationResponse", "ScenarioDelta"
]
