import numpy as np
import pandas as pd
from typing import Tuple

def generate_traffic_dataset(num_samples: int = 5000, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic, clearly-labelled traffic dataset simulating urban road conditions.
    Ground-truth physics:
    - Base time = (distance_km / speed_limit_kmh) * 60 minutes
    - Rush hour congestion multiplier (8-10 AM & 5-8 PM)
    - Inclement weather delays (rain +20%, storm +50%)
    - Stochastic traffic noise
    """
    np.random.seed(random_state)

    distances = np.random.uniform(1.0, 25.0, size=num_samples)
    speed_limits = np.random.choice([30, 40, 50, 60, 80], size=num_samples, p=[0.15, 0.25, 0.35, 0.15, 0.10])
    hours = np.random.randint(0, 24, size=num_samples)
    days = np.random.randint(0, 7, size=num_samples) # 0=Mon, 6=Sun
    is_weekend = (days >= 5).astype(int)

    weather_types = ["clear", "rain", "fog", "storm"]
    weather = np.random.choice(weather_types, size=num_samples, p=[0.70, 0.18, 0.08, 0.04])

    weather_multipliers = {
        "clear": 1.0,
        "fog": 1.15,
        "rain": 1.25,
        "storm": 1.55
    }

    # Rush hour curves
    congestion_indices = []
    travel_times = []

    for i in range(num_samples):
        h = hours[i]
        w = is_weekend[i]
        dist = distances[i]
        speed = speed_limits[i]
        w_factor = weather_multipliers[weather[i]]

        # Rush hour peak calculation
        if w == 0: # Weekday
            if 8 <= h <= 10:
                base_congestion = np.random.uniform(1.8, 2.8)
            elif 17 <= h <= 20:
                base_congestion = np.random.uniform(1.9, 3.1)
            elif 12 <= h <= 15:
                base_congestion = np.random.uniform(1.2, 1.6)
            else:
                base_congestion = np.random.uniform(1.0, 1.25)
        else: # Weekend
            if 12 <= h <= 21:
                base_congestion = np.random.uniform(1.3, 1.8)
            else:
                base_congestion = np.random.uniform(1.0, 1.2)

        # Incident probability: 4% chance of bottleneck
        incident = 1 if np.random.random() < 0.04 else 0
        if incident:
            base_congestion *= np.random.uniform(1.3, 1.7)

        effective_congestion = base_congestion * w_factor
        congestion_indices.append(round(effective_congestion, 2))

        # Travel time with gaussian disturbance
        effective_speed = max(8.0, speed / effective_congestion)
        base_time = (dist / effective_speed) * 60.0
        noisy_time = base_time + np.random.normal(0, 0.8)
        travel_times.append(max(1.0, round(noisy_time, 2)))

    df = pd.DataFrame({
        "distance_km": np.round(distances, 2),
        "speed_limit_kmh": speed_limits,
        "hour_of_day": hours,
        "day_of_week": days,
        "is_weekend": is_weekend,
        "weather": weather,
        "congestion_index": congestion_indices,
        "incident": (np.array(congestion_indices) > 2.2).astype(int),
        "travel_time_minutes": travel_times
    })

    return df
