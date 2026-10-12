from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models.orders import DeliveryRequest, Customer, Package
from app.schemas.order_schema import DeliveryRequestResponse

router = APIRouter(prefix="/orders", tags=["Order Management"])

@router.get("/pending", response_model=List[DeliveryRequestResponse])
async def list_pending_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DeliveryRequest)
        .options(selectinload(DeliveryRequest.customer), selectinload(DeliveryRequest.packages))
        .where(DeliveryRequest.status == "pending")
    )
    return result.scalars().all()
