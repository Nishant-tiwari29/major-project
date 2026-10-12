import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from pathlib import Path
import joblib

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.tree import DecisionTreeRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from app.ml.traffic_dataset import generate_traffic_dataset

MODEL_SAVE_PATH = Path(__file__).resolve().parent / "saved_traffic_model.joblib"

class TrafficModelTrainer:
    """
    Trains and benchmarks machine learning regression models for edge travel-time prediction:
    1. Linear Regression (Ordinary Least Squares baseline)
    2. Ridge Regression (L2 Regularized linear model)
    3. Decision Tree Regressor (Non-linear recursive partitioning)
    4. K-Nearest Neighbors Regressor (Non-parametric instance-based)
    """
    def __init__(self):
        self.models = {
            "Linear Regression (Baseline)": LinearRegression(),
            "Ridge Regression (L2)": Ridge(alpha=1.0),
            "Decision Tree Regressor": DecisionTreeRegressor(max_depth=10, min_samples_split=5, random_state=42),
            "K-Nearest Neighbors Regressor": KNeighborsRegressor(n_neighbors=7)
        }
        self.preprocessor = None
        self.best_pipeline = None

    def train_and_evaluate(self, num_samples: int = 4000) -> Dict[str, Any]:
        df = generate_traffic_dataset(num_samples=num_samples)

        X = df.drop(columns=["travel_time_minutes"])
        y = df["travel_time_minutes"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )

        categorical_cols = ["weather"]
        numerical_cols = [c for c in X.columns if c not in categorical_cols]

        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), numerical_cols),
                ("cat", OneHotEncoder(drop="first", sparse_output=False), categorical_cols)
            ]
        )

        results = {}
        best_rmse = float('inf')
        best_name = None

        for name, model in self.models.items():
            pipeline = Pipeline(steps=[
                ("preprocessor", preprocessor),
                ("regressor", model)
            ])

            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)

            mae = mean_absolute_error(y_test, preds)
            rmse = np.sqrt(mean_squared_error(y_test, preds))
            r2 = r2_score(y_test, preds)

            results[name] = {
                "mae": round(float(mae), 3),
                "rmse": round(float(rmse), 3),
                "r2_score": round(float(r2), 4)
            }

            if rmse < best_rmse:
                best_rmse = rmse
                best_name = name
                self.best_pipeline = pipeline

        # Save best model to disk
        joblib.dump(self.best_pipeline, MODEL_SAVE_PATH)

        return {
            "model_comparison": results,
            "best_model": best_name,
            "best_rmse": round(float(best_rmse), 3),
            "dataset_samples": num_samples
        }

if __name__ == "__main__":
    trainer = TrafficModelTrainer()
    res = trainer.train_and_evaluate()
    print("Training Results:", res)
