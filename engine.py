# engine.py — SparklingBlu Fleet Performance Engine
# Weekly targets: 50h/week, 35 trips/week, 80% AR, 5% CR max

from datetime import datetime, timedelta

# Weekly targets based on 10h/day x 5 days = 50h/week, 5 trips/day x 7 days = 35 trips/week
WEEKLY_TARGETS = {
    "hours": 50,       # Target hours per week (10h/day * 5 days)
    "trips": 35,       # Target trips per week (5 trips/day * 7 days)
    "ar": 0.80,       # Acceptance Rate target (80%)
    "cr": 0.05,       # Cancellation Rate max (5%)
    "daily_hours": 10, # Daily hours target
    "daily_trips": 5,  # Daily trips target
}

def get_week_progress():
    """Calculate current week progress (Monday = start)"""
    now = datetime.now()
    # Find Monday of current week
    days_since_monday = now.weekday()
    monday = now - timedelta(days=days_since_monday)
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

    # End of week is Sunday 23:59:59
    sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

    # Week days mapping
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Calculate progress
    total_seconds = (sunday - monday).total_seconds()
    elapsed_seconds = (now - monday).total_seconds()
    progress = min(elapsed_seconds / total_seconds, 1.0)

    days_left = max(0, (sunday.date() - now.date()).days)
    current_day = now.weekday()

    return {
        "day_name": day_names[current_day],
        "day_index": current_day + 1,  # 1-7
        "progress": progress,
        "days_left": days_left,
        "week_start": monday.date().isoformat(),
        "week_end": sunday.date().isoformat(),
    }


def calculate_performance_score(ar, cr, hours, trips, week_progress, report_days=1):
    """
    Calculate performance score (0-100) based on weekly targets.

    Score breakdown:
    - Hours component (25 pts max): Based on weekly hours vs target
    - Trips component (25 pts max): Based on weekly trips vs target
    - AR component (25 pts max): Based on acceptance rate
    - CR component (25 pts max): Based on cancellation rate

    A driver with only 31 hours should NOT be a top performer.
    Top performers need: high hours, high trips, high AR, low CR.
    """
    score = 0.0

    # Hours score (25 pts) - Weekly hours target is 50
    weekly_hours_target = WEEKLY_TARGETS["hours"]
    hours_ratio = min(float(hours) / weekly_hours_target, 1.0)
    hours_score = hours_ratio * 25

    # Trips score (25 pts) - Weekly trips target is 35
    weekly_trips_target = WEEKLY_TARGETS["trips"]
    trips_ratio = min(float(trips) / weekly_trips_target, 1.0)
    trips_score = trips_ratio * 25

    # AR score (25 pts) - Target is 80%
    ar_target = WEEKLY_TARGETS["ar"]
    try:
        ar_val = float(ar)
    except:
        ar_val = 0.0
    ar_ratio = min(ar_val / ar_target, 1.0)
    ar_score = ar_ratio * 25

    # CR score (25 pts) - Max is 5%, lower is better
    cr_max = WEEKLY_TARGETS["cr"]
    try:
        cr_val = float(cr)
    except:
        cr_val = 0.10  # Default high CR
    # Invert: 0% CR = 25 pts, 5%+ CR = 0 pts
    if cr_val <= cr_max:
        cr_score = 25.0
    else:
        cr_score = max(0, 25 * (1 - (cr_val - cr_max) / 0.20))  # Gracefully handle high CR

    score = hours_score + trips_score + ar_score + cr_score

    return round(score, 1)


def get_status(score):
    """
    Determine driver status based on score.
    Top performers need BOTH high activity AND good rates.
    """
    if score >= 85:
        return "Top Performer"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Needs Improvement"
    else:
        return "Needs Urgent Attention"


def get_remaining_targets(hours, trips, ar, cr, week_progress, report_days=1):
    """
    Calculate remaining targets to meet weekly goals.
    """
    remaining = {}

    # Weekly hours remaining (target: 50)
    try:
        hrs = float(hours)
    except:
        hrs = 0.0
    hours_needed = max(0, WEEKLY_TARGETS["hours"] - hrs)

    # Weekly trips remaining (target: 35)
    try:
        trp = float(trips)
    except:
        trp = 0
    trips_needed = max(0, int(WEEKLY_TARGETS["trips"] - trp))

    # AR on track?
    try:
        ar_val = float(ar)
    except:
        ar_val = 0.0
    ar_on_track = ar_val >= WEEKLY_TARGETS["ar"]

    # CR on track?
    try:
        cr_val = float(cr)
    except:
        cr_val = 0.10
    cr_on_track = cr_val <= WEEKLY_TARGETS["cr"]

    # Hours on track? (considering day of week)
    hours_on_track = hrs >= (WEEKLY_TARGETS["daily_hours"] * week_info()["day_index"])

    # Trips on track? (considering day of week)
    trips_on_track = trp >= (WEEKLY_TARGETS["daily_trips"] * week_info()["day_index"])

    # Daily averages
    day_index = week_info()["day_index"]
    daily_hours_avg = hrs / day_index if day_index > 0 else 0
    daily_trips_avg = trp / day_index if day_index > 0 else 0

    remaining["hours_needed"] = round(hours_needed, 1)
    remaining["trips_needed"] = trips_needed
    remaining["ar_on_track"] = ar_on_track
    remaining["cr_on_track"] = cr_on_track
    remaining["hours_on_track"] = hours_on_track
    remaining["trips_on_track"] = trips_on_track
    remaining["daily_hours_avg"] = round(daily_hours_avg, 1)
    remaining["daily_trips_avg"] = round(daily_trips_avg, 1)

    return remaining


def week_info():
    """Helper to get week info without passing around"""
    return get_week_progress()


def get_coaching_message(score, remaining, week_info_data):
    """Generate coaching message based on performance"""
    status = get_status(score)
    coaching = ""

    if status == "Top Performer":
        coaching = "Excellent work! You're meeting or exceeding all weekly targets. Keep up the great effort!"
    elif status == "Good":
        coaching = "Good progress! You're on track in some areas. Focus on any remaining KPIs to reach top performer status."
    elif status == "Needs Improvement":
        gaps = []
        if not remaining["hours_on_track"]:
            gaps.append(f"hours ({remaining['hours_needed']} hrs short)")
        if not remaining["trips_on_track"]:
            gaps.append(f"trips ({remaining['trips_needed']} trips short)")
        if not remaining["ar_on_track"]:
            gaps.append("acceptance rate")
        if not remaining["cr_on_track"]:
            gaps.append("cancellation rate")

        if gaps:
            coaching = f"Focus areas: {' | '.join(gaps)}. You have {week_info_data['days_left']} day(s) left to improve."
        else:
            coaching = f"You're close to top performer! Keep up your current pace. {week_info_data['days_left']} day(s) left."
    else:  # Needs Urgent Attention
        coaching = f"URGENT: Multiple KPIs need immediate attention. Please reach out to your team leader for support. {week_info_data['days_left']} day(s) left this week."

    return status, coaching


def kpi_fully_met(hours, trips, ar, cr, report_days=1):
    """
    Check if ALL weekly KPIs are fully met.
    To be KPI compliant, driver needs:
    - Weekly hours >= 50 (or appropriate for day of week)
    - Weekly trips >= 35 (or appropriate for day of week)
    - AR >= 80%
    - CR <= 5%
    """
    try:
        hrs = float(hours)
    except:
        hrs = 0.0

    try:
        trp = float(trips)
    except:
        trp = 0

    try:
        ar_val = float(ar)
    except:
        ar_val = 0.0

    try:
        cr_val = float(cr)
    except:
        cr_val = 0.10

    # All KPIs must be met
    hours_ok = hrs >= WEEKLY_TARGETS["hours"]
    trips_ok = trp >= WEEKLY_TARGETS["trips"]
    ar_ok = ar_val >= WEEKLY_TARGETS["ar"]
    cr_ok = cr_val <= WEEKLY_TARGETS["cr"]

    return hours_ok and trips_ok and ar_ok and cr_ok
