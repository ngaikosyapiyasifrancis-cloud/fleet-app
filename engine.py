# engine.py
# This file contains the logic (the "engine") for our Fleet Performance app.
# It calculates scores and generates coaching messages for drivers.


def calculate_performance_score(on_time_rate, fuel_efficiency, safety_incidents):
    """
    Calculates a performance score (0 to 100) for a driver.

    Parameters:
    - on_time_rate      : % of trips completed on time       (e.g. 85 means 85%)
    - fuel_efficiency   : km per litre                       (e.g. 12.5)
    - safety_incidents  : number of incidents in the period  (e.g. 0, 1, 2...)

    Returns:
    - A score between 0 and 100
    """

    # --- COMPONENT 1: On-Time Score (worth 40% of total score) ---
    # on_time_rate is already a percentage (0–100), so we use it directly.
    on_time_score = on_time_rate * 0.40

    # --- COMPONENT 2: Fuel Efficiency Score (worth 35% of total score) ---
    # We assume a "perfect" fuel efficiency is 15 km/L.
    # We cap it at 100 so no one scores above perfect.
    fuel_score = min((fuel_efficiency / 15) * 100, 100) * 0.35

    # --- COMPONENT 3: Safety Score (worth 25% of total score) ---
    # Zero incidents = perfect safety score (100).
    # Each incident reduces the score by 20 points.
    # We use max(..., 0) so the score never goes below 0.
    safety_score = max(100 - (safety_incidents * 20), 0) * 0.25

    # --- TOTAL SCORE ---
    total_score = on_time_score + fuel_score + safety_score

    # Round to 1 decimal place for clean display
    return round(total_score, 1)


def get_coaching_message(score):
    """
    Returns a short coaching message based on the driver's score.

    Parameters:
    - score : the performance score (0 to 100)

    Returns:
    - A string message for the driver
    """

    if score >= 85:
        return "🌟 Excellent performance! Keep it up."
    elif score >= 70:
        return "✅ Good work. Small improvements will push you to the top."
    elif score >= 50:
        return "⚠️ Average performance. Focus on punctuality and safety."
    else:
        return "🚨 Needs urgent attention. Please schedule a coaching session."
