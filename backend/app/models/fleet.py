from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Depot(Base):
    __tablename__ = "depots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)
    operating_hours = Column(String(50), default="08:00-20:00")

    vehicles = relationship("Vehicle", back_populates="depot", cascade="all, delete-orphan")
    delivery_requests = relationship("DeliveryRequest", back_populates="depot")

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=False)
    license_plate = Column(String(20), unique=True, nullable=False)
    vehicle_type = Column(String(50), default="van") # van, truck, ev_van, bike
    max_weight_kg = Column(Float, nullable=False, default=1000.0)
    max_volume_m3 = Column(Float, nullable=False, default=8.0)
    max_range_km = Column(Float, nullable=False, default=300.0)
    cost_per_km = Column(Float, nullable=False, default=1.20)
    cost_per_hour = Column(Float, nullable=False, default=25.0)
    is_electric = Column(Boolean, default=False)
    battery_capacity_kwh = Column(Float, default=60.0)
    current_battery_kwh = Column(Float, default=60.0)
    emissions_factor_g_co2_per_km = Column(Float, default=160.0) # g CO2 / km
    is_available = Column(Boolean, default=True)

    depot = relationship("Depot", back_populates="vehicles")
    routes = relationship("PlannedRoute", back_populates="vehicle")
    assignments = relationship("DriverAssignment", back_populates="vehicle")

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False)
    max_shift_hours = Column(Float, default=8.0)
    hourly_rate = Column(Float, default=20.0)
    shift_start = Column(String(10), default="08:00")
    shift_end = Column(String(10), default="17:00")
    is_available = Column(Boolean, default=True)

    assignments = relationship("DriverAssignment", back_populates="driver")

class DriverAssignment(Base):
    __tablename__ = "driver_assignments"

    id = Column(Integer, primary_key=True, index=True)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    shift_date = Column(DateTime, default=datetime.utcnow)

    driver = relationship("Driver", back_populates="assignments")
    vehicle = relationship("Vehicle", back_populates="assignments")

class ChargingStation(Base):
    __tablename__ = "charging_stations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    charger_type = Column(String(50), default="DC_Fast")
    charging_rate_kw = Column(Float, default=50.0) # kW
    cost_per_kwh = Column(Float, default=0.28)
    is_available = Column(Boolean, default=True)
