from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PackageBase(BaseModel):
    weight_kg: float
    volume_m3: float
    fragile: bool = False
    requires_cold_chain: bool = False
    tracking_code: Optional[str] = None

class PackageCreate(PackageBase):
    pass

class PackageResponse(PackageBase):
    id: int
    delivery_request_id: int
    model_config = ConfigDict(from_attributes=True)

class CustomerBase(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    latitude: float
    longitude: float
    address: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DeliveryRequestBase(BaseModel):
    customer_id: int
    depot_id: Optional[int] = None
    window_start: datetime
    window_end: datetime
    priority: int = 3
    service_time_min: float = 10.0
    status: str = "pending"

class DeliveryRequestCreate(DeliveryRequestBase):
    packages: List[PackageCreate]

class DeliveryRequestResponse(DeliveryRequestBase):
    id: int
    packages: List[PackageResponse] = []
    customer: Optional[CustomerResponse] = None
    model_config = ConfigDict(from_attributes=True)
