# engine.py
# The brain of the Fleet Performance & Coaching System.
# Scores and coaches drivers based on weekly targets and how far into the week we are.

from datetime import datetime, timezone

# --- WEEKLY TARGETS ---
WEEKLY_TARGETS = {
    "hours":        50.0,   # minimum hours online per week
    "acceptance":   0.80,   # minimum acceptance rate (80%)
    "cancellation": 0.05,   # maximum cancellation rate (5%)
    "trips":        30,     # minimum trips per week
}


def get_week_progress():
    """
    Works out how far through the current week we are (Monday=0 to Sunday=6).
    The week runs Monday 00:00 to Sunday 23:59.

    Returns:
    - day_number   : 0 = Monday, 6 = Sunday
    - day_name     : e.g. "Wednesday"
    - progress     : fraction of week elapsed e.g. 0.43 means 43% through the week
    - days_elapsed : how many full days have passed e.g. 3
    - days_left    : how many days remain e.g. 4
    """
    now = datetime.now()
    day_number  = now.weekday()          # Monday=0, Sunday=6
    day_name    = now.strftime("%A")     # e.g. "Wednesday"
    hour        = now.hour

    # Progress = days elapsed + fraction of current day
    days_elapsed = day_number + (hour / 24)
    progress     = days_elapsed / 7

    days_left = 6 - day_number  # full days remaining after today

    return {
        "day_number":   day_number,
        "day_name":     day_name,
        "progress":     round(progress, 4),
        "days_elapsed": round(days_elapsed, 2),
        "days_left":    days_left,
    }


def get_prorated_targets(progress):
    """
    Calculates how much of each target a driver should have achieved by now.

    For example: if it's Wednesday afternoon and progress=0.43
    - Expected hours so far: 50 * 0.43 = 21.5 hrs
    - Expected trips so far: 30 * 0.43 = 12.9 trips

    Note: Rates (AR, CR) are not pro-rated — they apply at all times.

    Returns a dict of expected values so far this week.
    """
    return {
        "hours":    round(WEEKLY_TARGETS["hours"]  * progress, 1),
        "trips":    round(WEEKLY_TARGETS["trips"]  * progress, 1),
        "acceptance":   WEEKLY_TARGETS["acceptance"],    # rate — always applies
        "cancellation": WEEKLY_TARGETS["cancellation"],  # rate — always applies
    }


def calculate_performance_score(confirmation_rate, cancellation_rate, trips_per_hr,
                                  earnings_per_hr, hours_online, trips_taken, progress):
    """
    Calculates a performance score (0 to 100) adjusted for week progress.

    Parameters:
    - confirmation_rate  : acceptance rate        (e.g. 0.96)
    - cancellation_rate  : cancellation rate      (e.g. 0.02)
    - trips_per_hr       : trips per hour         (e.g. 1.5)
    - earnings_per_hr    : rands earned per hour  (e.g. 13.50)
    - hours_online       : total hours online     (e.g. 22.5)
    - trips_taken        : total trips completed  (e.g. 18)
    - progress           : how far through week   (e.g. 0.43)

    Returns:
    - score between 0 and 100
    """

    # --- COMPONENT 1: Acceptance Rate (30%) ---
    # Must be above 80% at all times
    ar_score = (confirmation_rate / WEEKLY_TARGETS["acceptance"]) * 100
    ar_score = min(ar_score, 100) * 0.30

    # --- COMPONENT 2: Cancellation Rate (25%) ---
    # Must stay at or below 5%
    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_score = 100
    else:
        # Each % above 5% costs 20 points
        excess = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_score = max(100 - (excess * 20), 0)
    cr_score = cr_score * 0.25

    # --- COMPONENT 3: Hours Progress (25%) ---
    # Compare actual hours to expected hours at this point in the week
    expected_hours = WEEKLY_TARGETS["hours"] * max(progress, 0.01)
    hours_score = min((hours_online / expected_hours) * 100, 100) * 0.25

    # --- COMPONENT 4: Trips Progress (20%) ---
    # Compare actual trips to expected trips at this point in the week
    expected_trips = WEEKLY_TARGETS["trips"] * max(progress, 0.01)
    trips_score = min((trips_taken / expected_trips) * 100, 100) * 0.20

    total_score = ar_score + cr_score + hours_score + trips_score
    return round(total_score, 1)


def get_remaining_targets(hours_online, trips_taken, confirmation_rate,
                           cancellation_rate, progress):
    """
    Calculates what each driver still needs to achieve by Sunday 23:59.

    Returns a dict with remaining targets and on-track status for each metric.
    """
    remaining = {}

    # Hours still needed
    hours_needed = max(WEEKLY_TARGETS["hours"] - hours_online, 0)
    remaining["hours_needed"]    = round(hours_needed, 1)
    remaining["hours_on_track"]  = hours_online >= (WEEKLY_TARGETS["hours"] * progress)

    # Trips still needed
    trips_needed = max(WEEKLY_TARGETS["trips"] - trips_taken, 0)
    remaining["trips_needed"]    = int(trips_needed)
    remaining["trips_on_track"]  = trips_taken >= (WEEKLY_TARGETS["trips"] * progress)

    # Acceptance rate status
    remaining["ar_on_track"]     = confirmation_rate >= WEEKLY_TARGETS["acceptance"]
    remaining["ar_gap"]          = round(max(WEEKLY_TARGETS["acceptance"] - confirmation_rate, 0) * 100, 1)

    # Cancellation rate status
    remaining["cr_on_track"]     = cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    remaining["cr_gap"]          = round(max(cancellation_rate - WEEKLY_TARGETS["cancellation"], 0) * 100, 1)

    return remaining


def get_coaching_message(score, remaining, week_info):
    """
    Returns a status label and a personalised coaching message based on:
    - The driver's score
    - What they still need to achieve
    - What day of the week it is

    Returns:
    - (status, message)
    """
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    # Build a list of specific issues
    issues = []
    if not remaining["hours_on_track"]:
        issues.append(f"{remaining['hours_needed']} more hours online needed")
    if not remaining["trips_on_track"]:
        issues.append(f"{remaining['trips_needed']} more trips needed")
    if not remaining["ar_on_track"]:
        issues.append(f"Acceptance Rate is {remaining['ar_gap']}% below the 80% minimum")
    if not remaining["cr_on_track"]:
        issues.append(f"Cancellation Rate is {remaining['cr_gap']}% above the 5% maximum")

    issue_text = " | ".join(issues) if issues else "All targets on track ✅"

    if score >= 85:
        status  = "🌟 Top Performer"
        message = f"Excellent work this {day_name}! You are ahead of your weekly targets. {issue_text}"
    elif score >= 70:
        status  = "✅ Good"
        message = f"Good progress. {days_left} day(s) left to finish strong. {issue_text}"
    elif score >= 50:
        status  = "⚠️ Needs Improvement"
        message = f"You are falling behind. Only {days_left} day(s) left this week. {issue_text}"
    else:
        status  = "🚨 Urgent Attention"
        message = f"Critical — urgent action needed before Sunday. {days_left} day(s) left. {issue_text}"

    return (status, message)
