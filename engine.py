# engine.py
# Scoring and coaching — SparklingBlu Fleet Performance System
# Targets: 10h/day | 5 trips/day | 80%+ AR | max 5% CR | 50h/week Mon-Sun 5am-7:30pm

from datetime import datetime

WEEKLY_TARGETS = {
    "weekly_hours":    50.0,   # full week target
    "weekly_trips":    30,     # full week target
    "daily_hours":     10.0,   # per active day
    "daily_trips":     5,      # per active day
    "acceptance":      0.80,   # must be >= 80%
    "cancellation":    0.05,   # must be <= 5%
}

SHIFT_START = 5       # 5:00 AM
SHIFT_END   = 19.5    # 7:30 PM
SHIFT_HOURS = SHIFT_END - SHIFT_START  # 14.5h per day


def get_week_progress():
    now        = datetime.now()
    day_number = now.weekday()      # Mon=0, Sun=6
    day_name   = now.strftime("%A")
    hour       = now.hour + now.minute / 60

    if hour < SHIFT_START:
        day_fraction = 0.0
    elif hour > SHIFT_END:
        day_fraction = 1.0
    else:
        day_fraction = (hour - SHIFT_START) / SHIFT_HOURS

    days_elapsed = day_number + day_fraction
    progress     = days_elapsed / 7.0
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


def calculate_performance_score(confirmation_rate, cancellation_rate,
                                  hours_online, trips_taken, report_days=1):
    """
    Scores a driver 0-100 based on how well they are tracking against
    daily targets over the number of days the CSV covers.

    Scoring weights:
      Hours vs expected   35%  — must hit 10h per active day
      Trips vs expected   35%  — must hit 5 trips per active day
      Acceptance Rate     20%  — must be 80%+
      Cancellation Rate   10%  — must be 5% or below

    A driver on Thursday (report_days=4) needs:
      ≥ 40h online  (4 × 10h)
      ≥ 20 trips    (4 × 5 trips)
      ≥ 80% AR
      ≤ 5% CR
    to score in the Top Performer band (≥85).
    """
    days = max(int(report_days), 1)

    expected_hours = WEEKLY_TARGETS["daily_hours"] * days   # e.g. 40h by Thu
    expected_trips = WEEKLY_TARGETS["daily_trips"] * days   # e.g. 20 trips by Thu

    # 1. Hours score (35%)
    hrs_ratio  = hours_online / expected_hours
    hrs_score  = min(hrs_ratio, 1.0) * 100 * 0.35

    # 2. Trips score (35%)
    trp_ratio  = trips_taken / expected_trips
    trp_score  = min(trp_ratio, 1.0) * 100 * 0.35

    # 3. Acceptance Rate (20%)
    ar_ratio   = confirmation_rate / WEEKLY_TARGETS["acceptance"]
    ar_score   = min(ar_ratio, 1.0) * 100 * 0.20

    # 4. Cancellation Rate (10%) — penalise heavily above 5%
    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_base = 100
    else:
        excess  = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_base = max(100 - excess * 20, 0)
    cr_score = cr_base * 0.10

    return round(hrs_score + trp_score + ar_score + cr_score, 1)


def get_remaining_targets(hours_online, trips_taken, confirmation_rate,
                           cancellation_rate, progress, report_days=1):
    days = max(int(report_days), 1)

    rem = {}

    # Weekly remaining
    rem["hours_needed"]    = round(max(WEEKLY_TARGETS["weekly_hours"] - hours_online, 0), 1)
    rem["trips_needed"]    = max(WEEKLY_TARGETS["weekly_trips"] - int(trips_taken), 0)
    rem["hours_on_track"]  = hours_online >= (WEEKLY_TARGETS["weekly_hours"] * max(progress, 0.01))
    rem["trips_on_track"]  = trips_taken  >= (WEEKLY_TARGETS["weekly_trips"] * max(progress, 0.01))

    # Daily pace (for display — renamed to weekly totals per user request)
    rem["hours_weekly"]    = round(hours_online, 1)
    rem["trips_weekly"]    = int(trips_taken)
    rem["daily_hours_ok"]  = (hours_online / days) >= WEEKLY_TARGETS["daily_hours"]
    rem["daily_trips_ok"]  = (trips_taken  / days) >= WEEKLY_TARGETS["daily_trips"]

    # Rates
    rem["ar_on_track"]     = confirmation_rate >= WEEKLY_TARGETS["acceptance"]
    rem["ar_gap"]          = round(max(WEEKLY_TARGETS["acceptance"] - confirmation_rate, 0) * 100, 1)
    rem["cr_on_track"]     = cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    rem["cr_gap"]          = round(max(cancellation_rate - WEEKLY_TARGETS["cancellation"], 0) * 100, 1)

    return rem


def kpi_fully_met(hours_online, trips_taken, confirmation_rate,
                   cancellation_rate, report_days=1):
    """
    KPI is met when weekly totals are hit — not daily averages.
    A driver with 52h over 6 days has clearly met the 50h target.
    Daily targets are pace guides for coaching only.
    """
    return (
        hours_online      >= WEEKLY_TARGETS["weekly_hours"]  and
        trips_taken       >= WEEKLY_TARGETS["weekly_trips"]  and
        confirmation_rate >= WEEKLY_TARGETS["acceptance"]    and
        cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    )


def get_coaching_message(score, remaining, week_info):
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    issues = []
    if not remaining["daily_hours_ok"]:
        issues.append(f"{remaining['hours_weekly']}h online — need 10h/day pace")
    if not remaining["daily_trips_ok"]:
        issues.append(f"{remaining['trips_weekly']} trips — need 5 trips/day pace")
    if not remaining["ar_on_track"]:
        issues.append(f"AR {remaining['ar_gap']}% below 80% minimum")
    if not remaining["cr_on_track"]:
        issues.append(f"CR {remaining['cr_gap']}% above 5% maximum")
    if remaining["hours_needed"] > 0:
        issues.append(f"{remaining['hours_needed']}h still needed this week")
    if remaining["trips_needed"] > 0:
        issues.append(f"{remaining['trips_needed']} more trips needed this week")

    issue_text = "  |  ".join(issues) if issues else "All targets on track"

    if score >= 85:
        return ("Top Performer",
                f"Excellent work this {day_name}! You are on track for all weekly targets. {issue_text}")
    elif score >= 70:
        return ("Good",
                f"Good progress — {days_left} day(s) left to finish strong. {issue_text}")
    elif score >= 50:
        return ("Needs Improvement",
                f"Falling behind pace. Only {days_left} day(s) left. {issue_text}")
    else:
        return ("Urgent Attention",
                f"Critical — urgent action needed before Sunday. {days_left} day(s) left. {issue_text}")
