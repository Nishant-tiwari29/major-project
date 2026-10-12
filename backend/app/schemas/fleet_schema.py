from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class DepotBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    operating_hours: str = "08:00-20:00"

class DepotCreate(DepotBase):
    pass

class DepotResponse(DepotBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class VehicleBase(BaseModel):
    depot_id: int
    license_plate: str
    vehicle_type: str = "van"
    max_weight_kg: float = 1000.0
    max_volume_m3: float = 8.0
    max_range_km: float = 300.0
    cost_per_km: float = 1.20
    cost_per_hour: float = 25.0
    is_electric: bool = False
    battery_capacity_kwh: float = 60.0
    current_battery_kwh: float = 60.0
    emissions_factor_g_co2_per_km: float = 160.0
    is_available: bool = True

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DriverBase(BaseModel):
    full_name: str
    license_number: str
    max_shift_hours: float = 8.0
    hourly_rate: float = 20.0
    shift_start: str = "08:00"
    shift_end: str = "17:00"
    is_available: bool = True

class DriverResponse(DriverBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ChargingStationBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    charger_type: str = "DC_Fast"
    charging_rate_kw: float = 50.0
    cost_per_kwh: float = 0.28
    is_available: bool = True

class ChargingStationResponse(ChargingStationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
