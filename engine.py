# engine.py
# Scoring and coaching logic for SparklingBlu Fleet Performance System.
# Targets: 10h/day min | 5 trips/day min | 80%+ AR | max 5% CR | 50h/week total
# Operating window: Mon-Sun, 5:00am - 7:30pm

from datetime import datetime

# ── WEEKLY TARGETS ────────────────────────────────────────────────────────────
WEEKLY_TARGETS = {
    "hours":        50.0,   # minimum total hours per week
    "acceptance":   0.80,   # minimum acceptance rate
    "cancellation": 0.05,   # maximum cancellation rate
    "trips":        30,     # minimum trips per week (changed from 20 to 30)
    "daily_hours":  10.0,   # minimum hours per active day
    "daily_trips":  5,      # minimum trips per active day
}

# Operating window
SHIFT_START = 5      # 5:00 AM
SHIFT_END   = 19.5   # 7:30 PM  (19h30)
SHIFT_HOURS = SHIFT_END - SHIFT_START  # 14.5 hours available per day


def get_week_progress():
    """
    Returns how far through the current Mon-Sun week we are.
    Only counts time within the operating window (5am - 7:30pm).
    """
    now        = datetime.now()
    day_number = now.weekday()   # Mon=0, Sun=6
    day_name   = now.strftime("%A")
    hour       = now.hour + now.minute / 60

    # How far through today's shift are we?
    if hour < SHIFT_START:
        day_fraction = 0.0
    elif hour > SHIFT_END:
        day_fraction = 1.0
    else:
        day_fraction = (hour - SHIFT_START) / SHIFT_HOURS

    # Total operating days elapsed this week
    days_elapsed = day_number + day_fraction
    progress     = days_elapsed / 7

    days_left    = 6 - day_number

    return {
        "day_number":   day_number,
        "day_name":     day_name,
        "progress":     round(progress, 4),
        "days_elapsed": round(days_elapsed, 2),
        "days_left":    days_left,
        "current_hour": round(hour, 2),
        "in_shift":     SHIFT_START <= hour <= SHIFT_END,
    }


def get_remaining_targets(hours_online, trips_taken, confirmation_rate,
                           cancellation_rate, progress, report_days=1):
    """
    Calculates what each driver still needs to hit by Sunday.

    Parameters:
    - hours_online       : hours online so far
    - trips_taken        : trips completed so far
    - confirmation_rate  : acceptance rate (0-1)
    - cancellation_rate  : cancellation rate (0-1)
    - progress           : week progress fraction
    - report_days        : number of days this CSV covers (for daily averages)
    """
    remaining = {}

    # Weekly remaining
    remaining["hours_needed"]     = round(max(WEEKLY_TARGETS["hours"] - hours_online, 0), 1)
    remaining["trips_needed"]     = max(WEEKLY_TARGETS["trips"] - int(trips_taken), 0)
    remaining["hours_on_track"]   = hours_online >= (WEEKLY_TARGETS["hours"] * max(progress, 0.01))
    remaining["trips_on_track"]   = trips_taken  >= (WEEKLY_TARGETS["trips"] * max(progress, 0.01))

    # Daily averages
    remaining["daily_hours_avg"]  = round(hours_online / max(report_days, 1), 1)
    remaining["daily_trips_avg"]  = round(trips_taken  / max(report_days, 1), 1)
    remaining["daily_hours_ok"]   = remaining["daily_hours_avg"] >= WEEKLY_TARGETS["daily_hours"]
    remaining["daily_trips_ok"]   = remaining["daily_trips_avg"] >= WEEKLY_TARGETS["daily_trips"]

    # Rates
    remaining["ar_on_track"]      = confirmation_rate >= WEEKLY_TARGETS["acceptance"]
    remaining["ar_gap"]           = round(max(WEEKLY_TARGETS["acceptance"] - confirmation_rate, 0) * 100, 1)
    remaining["cr_on_track"]      = cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    remaining["cr_gap"]           = round(max(cancellation_rate - WEEKLY_TARGETS["cancellation"], 0) * 100, 1)

    return remaining


def calculate_performance_score(confirmation_rate, cancellation_rate,
                                  hours_online, trips_taken,
                                  progress, report_days=1):
    """
    Calculates a performance score (0-100) based on real targets.

    Scoring breakdown:
    - Acceptance Rate   : 30%  (must be 80%+)
    - Cancellation Rate : 25%  (must be 5% or below)
    - Daily Hours Avg   : 25%  (must average 10h/day)
    - Daily Trips Avg   : 20%  (must average 5 trips/day)
    """

    # 1. Acceptance Rate (30%)
    ar_score = min(confirmation_rate / WEEKLY_TARGETS["acceptance"], 1.0) * 100 * 0.30

    # 2. Cancellation Rate (25%)
    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_score = 100
    else:
        excess   = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_score = max(100 - (excess * 20), 0)
    cr_score *= 0.25

    # 3. Daily Hours Average (25%)
    daily_hrs = hours_online / max(report_days, 1)
    hrs_score = min(daily_hrs / WEEKLY_TARGETS["daily_hours"], 1.0) * 100 * 0.25

    # 4. Daily Trips Average (20%)
    daily_trp = trips_taken / max(report_days, 1)
    trp_score = min(daily_trp / WEEKLY_TARGETS["daily_trips"], 1.0) * 100 * 0.20

    total = ar_score + cr_score + hrs_score + trp_score
    return round(total, 1)


def kpi_fully_met(hours_online, trips_taken, confirmation_rate,
                   cancellation_rate, report_days=1):
    """Returns True only if ALL four KPI targets are fully met."""
    daily_hrs = hours_online / max(report_days, 1)
    daily_trp = trips_taken  / max(report_days, 1)
    return (
        confirmation_rate >= WEEKLY_TARGETS["acceptance"]   and
        cancellation_rate <= WEEKLY_TARGETS["cancellation"] and
        daily_hrs         >= WEEKLY_TARGETS["daily_hours"]  and
        daily_trp         >= WEEKLY_TARGETS["daily_trips"]
    )


def get_coaching_message(score, remaining, week_info):
    """
    Returns (status, message) based on score, remaining targets, and day.
    """
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    issues = []
    if not remaining["daily_hours_ok"]:
        issues.append(
            f"Averaging {remaining['daily_hours_avg']}h/day — need 10h/day minimum"
        )
    if not remaining["daily_trips_ok"]:
        issues.append(
            f"Averaging {remaining['daily_trips_avg']} trips/day — need 5 trips/day minimum"
        )
    if not remaining["ar_on_track"]:
        issues.append(f"AR is {remaining['ar_gap']}% below the 80% minimum")
    if not remaining["cr_on_track"]:
        issues.append(f"CR is {remaining['cr_gap']}% above the 5% maximum")
    if remaining["hours_needed"] > 0:
        issues.append(f"{remaining['hours_needed']}h still needed for the week")
    if remaining["trips_needed"] > 0:
        issues.append(f"{remaining['trips_needed']} more trips needed for the week")

    issue_text = "  |  ".join(issues) if issues else "All targets on track"

    if score >= 85:
        status  = "Top Performer"
        message = (f"Excellent work this {day_name}! "
                   f"You are ahead of all your weekly targets. {issue_text}")
    elif score >= 70:
        status  = "Good"
        message = (f"Good progress. {days_left} day(s) left to finish strong. "
                   f"{issue_text}")
    elif score >= 50:
        status  = "Needs Improvement"
        message = (f"You are falling behind pace. Only {days_left} day(s) left. "
                   f"{issue_text}")
    else:
        status  = "Urgent Attention"
        message = (f"Critical — urgent action needed before Sunday. "
                   f"{days_left} day(s) left. {issue_text}")

    return (status, message)
