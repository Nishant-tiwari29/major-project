from typing import Dict, Any, List
from dataclasses import dataclass
from app.core.config import settings

@dataclass
class CostBreakdown:
    distance_cost: float # Vehicle wear and fuel/energy per km
    driver_wage_cost: float # Driver hourly rate * route duration
    toll_charges: float # Highway / bridge tolls
    charging_cost: float # EV electricity charging expense
    late_penalty_cost: float # Penalties accrued from window violations
    total_cost: float
    carbon_emissions_kg: float

@dataclass
class NormalizedObjectiveScore:
    mode: str
    scalar_score: float
    normalized_distance: float
    normalized_duration: float
    normalized_cost: float
    normalized_emissions: float
    normalized_penalties: float
    weights_used: Dict[str, float]

class MultiObjectiveEvaluator:
    """
    Evaluates multi-objective routing plans with transparent cost accounting,
    CO2 emissions estimation, and min-max normalization.
    """
    PRESETS = {
        "balanced": {
            "cost": 0.25, "time": 0.25, "distance": 0.25, "emissions": 0.15, "penalties": 0.10
        },
        "cheapest": {
            "cost": 0.65, "time": 0.10, "distance": 0.10, "emissions": 0.05, "penalties": 0.10
        },
        "fastest": {
            "cost": 0.10, "time": 0.65, "distance": 0.10, "emissions": 0.05, "penalties": 0.10
        },
        "shortest": {
            "cost": 0.10, "time": 0.10, "distance": 0.65, "emissions": 0.10, "penalties": 0.05
        },
        "greenest": {
            "cost": 0.10, "time": 0.10, "distance": 0.10, "emissions": 0.65, "penalties": 0.05
        }
    }

    # Reference bounds for min-max scaling across typical city logistics instances
    BOUNDS = {
        "distance_km": (5.0, 150.0),
        "duration_min": (15.0, 360.0),
        "cost": (10.0, 400.0),
        "emissions_kg": (0.0, 60.0),
        "penalties": (0.0, 100.0)
    }

    @staticmethod
    def calculate_cost_breakdown(
        distance_km: float,
        duration_min: float,
        cost_per_km: float,
        driver_hourly_rate: float,
        emissions_factor_g_per_km: float,
        toll_cost: float = 0.0,
        charging_cost: float = 0.0,
        late_penalty_minutes: float = 0.0
    ) -> CostBreakdown:
        dist_cost = distance_km * cost_per_km
        driver_cost = (duration_min / 60.0) * driver_hourly_rate
        penalty_cost = late_penalty_minutes * settings.DEFAULT_LATE_PENALTY_PER_MINUTE
        total = dist_cost + driver_cost + toll_cost + charging_cost + penalty_cost
        co2_kg = (distance_km * emissions_factor_g_per_km) / 1000.0

        return CostBreakdown(
            distance_cost=round(dist_cost, 2),
            driver_wage_cost=round(driver_cost, 2),
            toll_charges=round(toll_cost, 2),
            charging_cost=round(charging_cost, 2),
            late_penalty_cost=round(penalty_cost, 2),
            total_cost=round(total, 2),
            carbon_emissions_kg=round(co2_kg, 2)
        )

    @classmethod
    def evaluate(
        cls,
        distance_km: float,
        duration_min: float,
        cost: float,
        emissions_kg: float,
        penalty_cost: float,
        mode: str = "balanced"
    ) -> NormalizedObjectiveScore:
        weights = cls.PRESETS.get(mode.lower(), cls.PRESETS["balanced"])

        def normalize(val: float, key: str) -> float:
            low, high = cls.BOUNDS[key]
            clamped = max(low, min(high, val))
            return (clamped - low) / (high - low)

        norm_d = normalize(distance_km, "distance_km")
        norm_t = normalize(duration_min, "duration_min")
        norm_c = normalize(cost, "cost")
        norm_e = normalize(emissions_kg, "emissions_kg")
        norm_p = normalize(penalty_cost, "penalties")

        score = (
            weights["distance"] * norm_d +
            weights["time"] * norm_t +
            weights["cost"] * norm_c +
            weights["emissions"] * norm_e +
            weights["penalties"] * norm_p
        )

        return NormalizedObjectiveScore(
            mode=mode,
            scalar_score=round(score, 4),
            normalized_distance=round(norm_d, 4),
            normalized_duration=round(norm_t, 4),
            normalized_cost=round(norm_c, 4),
            normalized_emissions=round(norm_e, 4),
            normalized_penalties=round(norm_p, 4),
            weights_used=weights
        )
