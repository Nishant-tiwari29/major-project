from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any

from app.ml.model_trainer import TrafficModelTrainer
from app.ml.predictor import predictor

router = APIRouter(prefix="/ml", tags=["Machine Learning Traffic Prediction"])

class TrafficFeaturePayload(BaseModel):
    distance_km: float
    speed_limit_kmh: float = 50.0
    hour_of_day: int = 9
    day_of_week: int = 1
    weather: str = "clear"
    congestion_index: float = 1.4

@router.post("/train")
async def train_traffic_models(num_samples: int = 4000):
    trainer = TrafficModelTrainer()
    results = trainer.train_and_evaluate(num_samples=num_samples)
    return results

@router.post("/predict-edge")
async def predict_road_duration(payload: TrafficFeaturePayload):
    dur = predictor.predict_edge_travel_time(
        distance_km=payload.distance_km,
        speed_limit_kmh=payload.speed_limit_kmh,
        hour_of_day=payload.hour_of_day,
        day_of_week=payload.day_of_week,
        weather=payload.weather,
        congestion_index=payload.congestion_index
    )
    return {
        "distance_km": payload.distance_km,
        "predicted_duration_minutes": dur,
        "effective_speed_kmh": round((payload.distance_km / dur) * 60.0, 1)
    }
