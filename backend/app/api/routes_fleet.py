from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.models.fleet import Depot, Vehicle, Driver, ChargingStation
from app.schemas.fleet_schema import (
    DepotResponse, VehicleResponse, DriverResponse, ChargingStationResponse
)

router = APIRouter(prefix="/fleet", tags=["Fleet Management"])

@router.get("/depots", response_model=List[DepotResponse])
async def list_depots(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Depot))
    return result.scalars().all()

@router.get("/vehicles", response_model=List[VehicleResponse])
async def list_vehicles(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Vehicle))
    return result.scalars().all()

@router.get("/drivers", response_model=List[DriverResponse])
async def list_drivers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Driver))
    return result.scalars().all()

@router.get("/charging-stations", response_model=List[ChargingStationResponse])
async def list_charging_stations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ChargingStation))
    return result.scalars().all()
