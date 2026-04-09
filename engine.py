# engine.py
# Cleaned & Optimized for Real-Time Coaching System

from datetime import datetime

# --- WEEKLY TARGETS ---
WEEKLY_TARGETS = {
    "hours":        50.0,
    "acceptance":   0.80,
    "cancellation": 0.05,
    "trips":        30,
}

# ----------------------------------------
# WEEK PROGRESS
# ----------------------------------------
def get_week_progress():
    now = datetime.now()
    day_number  = now.weekday()
    day_name    = now.strftime("%A")
    hour        = now.hour

    days_elapsed = day_number + (hour / 24)
    progress     = days_elapsed / 7
    days_left    = 6 - day_number

    return {
        "day_number": day_number,
        "day_name": day_name,
        "progress": round(progress, 4),
        "days_elapsed": round(days_elapsed, 2),
        "days_left": days_left,
    }

# ----------------------------------------
# PERFORMANCE SCORE
# ----------------------------------------
def calculate_performance_score(
    confirmation_rate,
    cancellation_rate,
    trips_per_hr,
    earnings_per_hr,
    hours_online,
    trips_taken,
    progress
):

    ar_score = min((confirmation_rate / WEEKLY_TARGETS["acceptance"]) * 100, 100) * 0.30

    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_score = 100
    else:
        excess = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_score = max(100 - (excess * 20), 0)
    cr_score *= 0.25

    expected_hours = WEEKLY_TARGETS["hours"] * max(progress, 0.01)
    hours_score = min((hours_online / expected_hours) * 100, 100) * 0.25

    expected_trips = WEEKLY_TARGETS["trips"] * max(progress, 0.01)
    trips_score = min((trips_taken / expected_trips) * 100, 100) * 0.20

    return round(ar_score + cr_score + hours_score + trips_score, 1)

# ----------------------------------------
# REMAINING TARGETS
# ----------------------------------------
def get_remaining_targets(hours_online, trips_taken, confirmation_rate, cancellation_rate, progress):

    return {
        "hours_needed": round(max(WEEKLY_TARGETS["hours"] - hours_online, 0), 1),
        "trips_needed": int(max(WEEKLY_TARGETS["trips"] - trips_taken, 0)),
        "hours_on_track": hours_online >= (WEEKLY_TARGETS["hours"] * progress),
        "trips_on_track": trips_taken >= (WEEKLY_TARGETS["trips"] * progress),
        "ar_on_track": confirmation_rate >= WEEKLY_TARGETS["acceptance"],
        "cr_on_track": cancellation_rate <= WEEKLY_TARGETS["cancellation"],
    }

# ----------------------------------------
# STATUS + COACHING
# ----------------------------------------
def get_coaching_message(score, remaining, week_info):

    days_left = week_info["days_left"]

    if score >= 85:
        return "🌟 Top Performer", f"Excellent work — keep pushing to stay on top."

    elif score >= 70:
        return "✅ Good", f"Good progress. {days_left} days left to finish strong."

    elif score >= 50:
        return "⚠️ Needs Improvement", f"You are falling behind. {days_left} days left to recover."

    else:
        return "🚨 Urgent Attention", f"Urgent action needed. Fix performance immediately."

# ----------------------------------------
# SIMPLE MESSAGE GENERATOR (NEW CORE)
# ----------------------------------------
def generate_whatsapp_message(driver_name, score, status, remaining, week_info, row, language="english"):

    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    hrs = round(row["Hours Online"], 1)
    trp = int(row["Trips Taken"])
    ar  = round(row["Confirmation Rate"] * 100, 1)
    cr  = round(row["Cancellation Rate"] * 100, 1)

    hrs_needed = remaining["hours_needed"]
    trp_needed = remaining["trips_needed"]

    # --- PERFORMANCE TONE ---
    if score >= 85:
        tone = "🔥 You're doing great — keep the momentum going."
    elif score >= 70:
        tone = "👍 You're on track, just stay consistent."
    elif score >= 50:
        tone = "⚠️ You need to push harder to hit your targets."
    else:
        tone = "🚨 Immediate improvement needed — you're far behind."

    # --- FINAL MESSAGE ---
    msg = f"""Hi {driver_name} 👋

📅 {day_name} check-in — {days_left} day(s) left this week.

📊 Your current stats:
• Hours: {hrs} hrs
• Trips: {trp}
• Acceptance: {ar}%
• Cancellation: {cr}%

🎯 Targets:
50+ hrs | 80%+ AR | ≤5% CR | 30+ trips

📉 Remaining:
• {hrs_needed} more hours
• {trp_needed} more trips

{tone}
"""

    return msg
