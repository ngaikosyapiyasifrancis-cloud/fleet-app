# engine.py
# The brain of the Fleet Performance System.
# Uses real Uber data columns to calculate a performance score and coaching message.


def calculate_performance_score(confirmation_rate, cancellation_rate, trips_per_hr, earnings_per_hr):
    """
    Calculates a performance score (0 to 100) for a driver using real Uber data.

    Parameters:
    - confirmation_rate  : % of trips accepted   (e.g. 0.96 means 96%)
    - cancellation_rate  : % of trips cancelled  (e.g. 0.02 means 2%)
    - trips_per_hr       : trips completed per hour (e.g. 1.5)
    - earnings_per_hr    : rands earned per hour  (e.g. 13.50)

    Returns:
    - A score between 0 and 100
    """

    # --- COMPONENT 1: Confirmation Score (worth 35% of total) ---
    # confirmation_rate is between 0 and 1, so we multiply by 100 to get a percentage.
    # Example: 0.96 → 96 → 96 * 0.35 = 33.6
    confirmation_score = (confirmation_rate * 100) * 0.35

    # --- COMPONENT 2: Cancellation Score (worth 25% of total) ---
    # Lower cancellation = better score.
    # We subtract from 100 and penalise heavily — each 1% cancellation costs 10 points.
    # Example: 0.02 (2%) → 100 - (2 * 10) = 80 → 80 * 0.25 = 20
    cancellation_penalty = (cancellation_rate * 100) * 10
    cancellation_score = max(100 - cancellation_penalty, 0) * 0.25

    # --- COMPONENT 3: Productivity Score (worth 20% of total) ---
    # We benchmark "great" as 2 trips per hour.
    # Example: 1.5 trips/hr → (1.5/2 * 100) = 75 → 75 * 0.20 = 15
    productivity_score = min((trips_per_hr / 2) * 100, 100) * 0.20

    # --- COMPONENT 4: Earnings Efficiency Score (worth 20% of total) ---
    # We benchmark "great" as R15/hr earnings.
    # Example: R13.50/hr → (13.50/15 * 100) = 90 → 90 * 0.20 = 18
    earnings_score = min((earnings_per_hr / 15) * 100, 100) * 0.20

    # --- TOTAL SCORE ---
    total_score = confirmation_score + cancellation_score + productivity_score + earnings_score

    return round(total_score, 1)


def get_coaching_message(score):
    """
    Returns a coaching message and status label based on the driver's score.

    Parameters:
    - score : the performance score (0 to 100)

    Returns:
    - A tuple: (status, message)
    """

    if score >= 85:
        return ("🌟 Top Performer", "Excellent work! You are one of our best drivers. Keep it up.")
    elif score >= 70:
        return ("✅ Good", "Good performance. Focus on maintaining your confirmation rate to reach the top.")
    elif score >= 50:
        return ("⚠️ Needs Improvement", "Average performance. Reduce cancellations and aim for more trips per hour.")
    else:
        return ("🚨 Urgent Attention", "Performance is below standard. Please contact your fleet manager for a coaching session.")
