import joblib
import pandas as pd
from typing import Dict, Any, Optional
from pathlib import Path
from app.ml.model_trainer import TrafficModelTrainer, MODEL_SAVE_PATH
from app.dsa.graph import RoadNetworkGraph

class TrafficPredictor:
    """
    Predicts road segment travel time and applies predicted travel times into graph edge weights.
    """
    def __init__(self):
        self.model = None
        self._load_or_train()

    def _load_or_train(self):
        if MODEL_SAVE_PATH.exists():
            try:
                self.model = joblib.load(MODEL_SAVE_PATH)
            except Exception:
                self.model = None

        if self.model is None:
            trainer = TrafficModelTrainer()
            trainer.train_and_evaluate(num_samples=2500)
            self.model = joblib.load(MODEL_SAVE_PATH)

    def predict_edge_travel_time(
        self,
        distance_km: float,
        speed_limit_kmh: float,
        hour_of_day: int = 9,
        day_of_week: int = 1,
        weather: str = "clear",
        congestion_index: float = 1.4
    ) -> float:
        input_df = pd.DataFrame([{
            "distance_km": distance_km,
            "speed_limit_kmh": speed_limit_kmh,
            "hour_of_day": hour_of_day,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0,
            "weather": weather,
            "congestion_index": congestion_index,
            "incident": 1 if congestion_index > 2.2 else 0
        }])

        pred = self.model.predict(input_df)[0]
        return max(0.5, round(float(pred), 2))

    def update_graph_with_predictions(
        self,
        graph: RoadNetworkGraph,
        hour_of_day: int = 9,
        day_of_week: int = 1,
        weather: str = "clear",
        congestion_index: float = 1.4
    ):
        """Dynamically injects ML predicted speeds/durations into the road network edges."""
        for edges in graph.adj.values():
            for edge in edges:
                if not edge.is_closed:
                    pred_minutes = self.predict_edge_travel_time(
                        distance_km=edge.distance_km,
                        speed_limit_kmh=edge.speed_limit_kmh,
                        hour_of_day=hour_of_day,
                        day_of_week=day_of_week,
                        weather=weather,
                        congestion_index=congestion_index
                    )
                    # Effective speed = (distance_km / pred_minutes) * 60
                    pred_speed = (edge.distance_km / max(0.1, pred_minutes)) * 60.0
                    edge.congestion_multiplier = max(0.5, edge.speed_limit_kmh / max(5.0, pred_speed))

predictor = TrafficPredictor()
