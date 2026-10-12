from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact_email = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)

    delivery_requests = relationship("DeliveryRequest", back_populates="customer")

class DeliveryRequest(Base):
    __tablename__ = "delivery_requests"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=True)
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    priority = Column(Integer, default=3) # 1 (Lowest) to 5 (Urgent)
    service_time_min = Column(Float, default=10.0) # Unloading duration
    status = Column(String(30), default="pending") # pending, assigned, in_transit, delivered, infeasible

    customer = relationship("Customer", back_populates="delivery_requests")
    depot = relationship("Depot", back_populates="delivery_requests")
    packages = relationship("Package", back_populates="delivery_request", cascade="all, delete-orphan")
    route_stops = relationship("RouteStop", back_populates="delivery_request")

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    delivery_request_id = Column(Integer, ForeignKey("delivery_requests.id"), nullable=False)
    weight_kg = Column(Float, nullable=False)
    volume_m3 = Column(Float, nullable=False)
    fragile = Column(Boolean, default=False)
    requires_cold_chain = Column(Boolean, default=False)
    tracking_code = Column(String(50), unique=True, nullable=True)

    delivery_request = relationship("DeliveryRequest", back_populates="packages")
