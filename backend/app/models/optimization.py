from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class OptimizationJob(Base):
    __tablename__ = "optimization_jobs"

    id = Column(String(50), primary_key=True, index=True) # UUID or timestamp-hash
    created_at = Column(DateTime, default=datetime.utcnow)
    objective_mode = Column(String(50), default="balanced") # balanced, cheapest, fastest, greenest, shortest
    algorithm_name = Column(String(50), default="branch_and_bound") # bitmask_dp, branch_and_bound, clarke_wright, nearest_neighbor
    total_distance_km = Column(Float, default=0.0)
    total_duration_min = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    total_co2_kg = Column(Float, default=0.0)
    violation_count = Column(Integer, default=0)
    status = Column(String(30), default="completed") # pending, processing, completed, failed
    execution_time_ms = Column(Float, default=0.0)
    parameters = Column(JSON, nullable=True) # what-if scenario overrides

    routes = relationship("PlannedRoute", back_populates="job", cascade="all, delete-orphan")
    benchmark_metrics = relationship("BenchmarkMetric", back_populates="job", cascade="all, delete-orphan")

class PlannedRoute(Base):
    __tablename__ = "planned_routes"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), ForeignKey("optimization_jobs.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    route_distance_km = Column(Float, default=0.0)
    route_duration_min = Column(Float, default=0.0)
    route_cost = Column(Float, default=0.0)
    route_co2_kg = Column(Float, default=0.0)
    summary_polyline = Column(Text, nullable=True) # GeoJSON or encoded polyline

    job = relationship("OptimizationJob", back_populates="routes")
    vehicle = relationship("Vehicle", back_populates="routes")
    stops = relationship("RouteStop", back_populates="planned_route", cascade="all, delete-orphan", order_by="RouteStop.stop_order")

class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    planned_route_id = Column(Integer, ForeignKey("planned_routes.id"), nullable=False)
    stop_order = Column(Integer, nullable=False)
    delivery_request_id = Column(Integer, ForeignKey("delivery_requests.id"), nullable=True)
    stop_type = Column(String(30), default="delivery") # depot_start, delivery, charging, depot_end
    location_name = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    estimated_arrival = Column(DateTime, nullable=True)
    estimated_departure = Column(DateTime, nullable=True)
    waiting_time_min = Column(Float, default=0.0)
    slack_time_min = Column(Float, default=0.0)
    remaining_battery_kwh = Column(Float, nullable=True)

    planned_route = relationship("PlannedRoute", back_populates="stops")
    delivery_request = relationship("DeliveryRequest", back_populates="route_stops")

class BenchmarkMetric(Base):
    __tablename__ = "benchmark_metrics"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), ForeignKey("optimization_jobs.id"), nullable=True)
    algorithm_name = Column(String(50), nullable=False)
    instance_size = Column(Integer, nullable=False) # Number of delivery locations
    execution_time_ms = Column(Float, nullable=False)
    memory_usage_kb = Column(Float, default=0.0)
    states_explored = Column(Integer, default=0)
    solution_cost = Column(Float, nullable=False)
    total_distance_km = Column(Float, default=0.0)
    optimality_gap_percent = Column(Float, default=0.0)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("OptimizationJob", back_populates="benchmark_metrics")
