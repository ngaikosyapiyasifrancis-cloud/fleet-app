# engine.py
# The brain of the Fleet Performance & Coaching System.
# Scores and coaches drivers based on weekly targets.

import urllib.parse
import base64
import json

# --- WEEKLY TARGETS ---
WEEKLY_TARGETS = {
    "hours":        50.0,
    "acceptance":   0.80,
    "cancellation": 0.05,
    "trips":        30,
}


def get_week_progress():
    """Works out how far through the current week we are."""
    from datetime import datetime
    now = datetime.now()
    day_number  = now.weekday()
    day_name    = now.strftime("%A")
    hour        = now.hour
    days_elapsed = day_number + (hour / 24)
    progress     = days_elapsed / 7
    days_left = 6 - day_number

    return {
        "day_number":   day_number,
        "day_name":     day_name,
        "progress":     round(progress, 4),
        "days_elapsed": round(days_elapsed, 2),
        "days_left":    days_left,
    }


def calculate_performance_score(confirmation_rate, cancellation_rate, trips_per_hr,
                                  earnings_per_hr, hours_online, trips_taken, progress):
    """Calculates a performance score (0 to 100) adjusted for week progress."""

    # Acceptance Rate (30%)
    ar_score = (confirmation_rate / WEEKLY_TARGETS["acceptance"]) * 100
    ar_score = min(ar_score, 100) * 0.30

    # Cancellation Rate (25%)
    if cancellation_rate <= WEEKLY_TARGETS["cancellation"]:
        cr_score = 100
    else:
        excess = (cancellation_rate - WEEKLY_TARGETS["cancellation"]) * 100
        cr_score = max(100 - (excess * 20), 0)
    cr_score = cr_score * 0.25

    # Hours Progress (25%)
    expected_hours = WEEKLY_TARGETS["hours"] * max(progress, 0.01)
    hours_score = min((hours_online / expected_hours) * 100, 100) * 0.25

    # Trips Progress (20%)
    expected_trips = WEEKLY_TARGETS["trips"] * max(progress, 0.01)
    trips_score = min((trips_taken / expected_trips) * 100, 100) * 0.20

    total_score = ar_score + cr_score + hours_score + trips_score
    return round(total_score, 1)


def get_remaining_targets(hours_online, trips_taken, confirmation_rate,
                           cancellation_rate, progress):
    """Calculates what each driver still needs to achieve by Sunday 23:59."""
    remaining = {}

    hours_needed = max(WEEKLY_TARGETS["hours"] - hours_online, 0)
    remaining["hours_needed"]    = round(hours_needed, 1)
    remaining["hours_on_track"]  = hours_online >= (WEEKLY_TARGETS["hours"] * progress)

    trips_needed = max(WEEKLY_TARGETS["trips"] - trips_taken, 0)
    remaining["trips_needed"]    = int(trips_needed)
    remaining["trips_on_track"]  = trips_taken >= (WEEKLY_TARGETS["trips"] * progress)

    remaining["ar_on_track"]     = confirmation_rate >= WEEKLY_TARGETS["acceptance"]
    remaining["ar_gap"]          = round(max(WEEKLY_TARGETS["acceptance"] - confirmation_rate, 0) * 100, 1)

    remaining["cr_on_track"]     = cancellation_rate <= WEEKLY_TARGETS["cancellation"]
    remaining["cr_gap"]          = round(max(cancellation_rate - WEEKLY_TARGETS["cancellation"], 0) * 100, 1)

    return remaining


def get_coaching_message(score, remaining, week_info):
    """Returns a status label and coaching message based on score and remaining targets."""
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    issues = []
    if not remaining["hours_on_track"]:
        issues.append(f"{remaining['hours_needed']} more hours online needed")
    if not remaining["trips_on_track"]:
        issues.append(f"{remaining['trips_needed']} more trips needed")
    if not remaining["ar_on_track"]:
        issues.append(f"AR is {remaining['ar_gap']}% below 80% minimum")
    if not remaining["cr_on_track"]:
        issues.append(f"CR is {remaining['cr_gap']}% above 5% maximum")

    issue_text = " | ".join(issues) if issues else "All targets on track"

    if score >= 85:
        status  = "Top Performer"
        message = f"Excellent work! You are ahead of targets. {issue_text}"
    elif score >= 70:
        status  = "Good"
        message = f"Good progress. {days_left} day(s) left to finish strong. {issue_text}"
    elif score >= 50:
        status  = "Needs Improvement"
        message = f"You are falling behind. Only {days_left} day(s) left. {issue_text}"
    else:
        status  = "Urgent Attention"
        message = f"Critical action needed! {days_left} day(s) left. {issue_text}"

    return (status, message)


# ---------------------------------------------------------------------------
# LINK GENERATOR - Encodes data directly in URL
# ---------------------------------------------------------------------------

def encode_fleet_data(df, week_label=""):
    """Encodes all fleet data to base64 for URL."""
    # Convert DataFrame to list of dicts (JSON serializable)
    drivers_data = []
    for _, row in df.iterrows():
        drivers_data.append({
            "Driver": str(row.get("Driver", "")),
            "Team": str(row.get("Team", "")),
            "Score": float(row.get("Score", 0)),
            "Status": str(row.get("Status", "")),
            "KPI Met": str(row.get("KPI Met", "NO")),
            "Hours Online": float(row.get("Hours Online", 0)),
            "Trips Taken": int(row.get("Trips Taken", 0)),
            "Confirmation Rate": float(row.get("Confirmation Rate", 0)),
            "Cancellation Rate": float(row.get("Cancellation Rate", 0)),
            "Earnings / hr": float(row.get("Earnings / hr", 0)),
            "Total Earnings": float(row.get("Total Earnings", 0)),
            "Coaching Message": str(row.get("Coaching Message", "")),
        })

    data = {
        "week": week_label,
        "drivers": drivers_data,
        "targets": WEEKLY_TARGETS
    }

    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode()).decode()
    return encoded


def generate_shareable_link(base_url, encoded_data, mode="fleet", name="", team=""):
    """Generates a shareable link with encoded data."""
    params = f"data={urllib.parse.quote(encoded_data)}&mode={mode}"
    if name:
        params += f"&name={urllib.parse.quote(name)}"
    if team:
        params += f"&team={urllib.parse.quote(team)}"
    return f"{base_url.rstrip('/')}?{params}"


def generate_driver_link(base_url, df, driver_name, week_label=""):
    """Generates a shareable link for an individual driver."""
    encoded = encode_fleet_data(df, week_label)
    return generate_shareable_link(base_url, encoded, mode="driver", name=driver_name)


def generate_team_link(base_url, df, team_name, week_label=""):
    """Generates a shareable link for a team."""
    encoded = encode_fleet_data(df, week_label)
    return generate_shareable_link(base_url, encoded, mode="team", team=team_name)


def generate_fleet_link(base_url, df, week_label=""):
    """Generates a shareable link for the full fleet overview."""
    encoded = encode_fleet_data(df, week_label)
    return generate_shareable_link(base_url, encoded, mode="fleet")


# ---------------------------------------------------------------------------
# WHATSAPP MESSAGE GENERATOR
# ---------------------------------------------------------------------------

def generate_whatsapp_message(driver_name, score, status, remaining, week_info, row):
    """Generates a WhatsApp message for a driver."""
    day_name  = week_info["day_name"]
    days_left = week_info["days_left"]

    ar  = round((row.get("Confirmation Rate", 0)) * 100, 1)
    cr  = round((row.get("Cancellation Rate", 0)) * 100, 1)
    hrs = round(row.get("Hours Online", 0), 1)
    trp = int(row.get("Trips Taken", 0))
    eph = round(row.get("Earnings / hr", 0), 2)

    hrs_ok  = "[OK]" if remaining["hours_on_track"] else "[X]"
    trp_ok  = "[OK]" if remaining["trips_on_track"] else "[X]"
    ar_ok   = "[OK]" if remaining["ar_on_track"] else "[X]"
    cr_ok   = "[OK]" if remaining["cr_on_track"] else "[X]"

    msg = f"""SPARKLINGBLU MOTO - WEEKLY PERFORMANCE
================================
Driver: {driver_name}
Day: {day_name} | Days Left: {days_left}
Score: {score}/100 | Status: {status}

================================
YOUR WEEKLY METRICS
================================
Hours Online: {hrs} hrs {hrs_ok} (min 50 hrs)
Trips Taken: {trp} trips {trp_ok} (min 30 trips)
Acceptance Rate: {ar}% {ar_ok} (must be 80%+)
Cancellation Rate: {cr}% {cr_ok} (max 5%)
Earnings / hr: R{eph}

================================
WHAT YOU NEED BY SUNDAY
================================
Hours needed: {remaining['hours_needed']} hrs
Trips needed: {remaining['trips_needed']} trips
{"[X] Keep accepting trips!" if not remaining['ar_on_track'] else "[OK] AR target met!"}
{"[X] Reduce cancellations!" if not remaining['cr_on_track'] else "[OK] CR target met!"}

Keep pushing - you've got this!
SparklingBlu Moto Fleet Team"""

    return msg


def generate_bulk_whatsapp_message(df_summary, week_info):
    """Generates a bulk WhatsApp message summarizing the fleet."""
    day_name    = week_info["day_name"]
    days_left   = week_info["days_left"]
    total       = len(df_summary)
    avg_score   = round(df_summary["Score"].mean(), 1)
    top         = len(df_summary[df_summary["Score"] >= 85])
    good        = len(df_summary[(df_summary["Score"] >= 70) & (df_summary["Score"] < 85)])
    needs_imp   = len(df_summary[(df_summary["Score"] >= 50) & (df_summary["Score"] < 70)])
    urgent      = len(df_summary[df_summary["Score"] < 50])
    top_driver  = df_summary.loc[df_summary["Score"].idxmax(), "Driver"]
    top_score   = df_summary["Score"].max()

    msg = f"""SPARKLINGBLU MOTO - FLEET UPDATE
================================
{days_left} day(s) left this week
Total Drivers: {total}
Fleet Avg Score: {avg_score}/100

================================
PERFORMANCE BREAKDOWN
================================
Top Performers: {top}
Good: {good}
Needs Improvement: {needs_imp}
Urgent Attention: {urgent}

================================
DRIVER OF THE WEEK
================================
{top_driver} - Score: {top_score}/100

================================
Targets: 50hrs | 80%+ AR | <=5% CR | 30+ trips
SparklingBlu Moto Fleet Team"""

    return msg


def generate_team_whatsapp_message(team_name, team_df, week_info):
    """Generates a WhatsApp message for a team's performance."""
    days_left  = week_info["days_left"]
    total      = len(team_df)
    avg_score  = round(team_df["Score"].mean(), 1)
    top        = len(team_df[team_df["Score"] >= 85])
    needs_att  = len(team_df[team_df["Score"] < 70])
    compliant  = len(team_df[team_df["KPI Met"] == "YES"])

    msg = f"""SPARKLINGBLU - {team_name} UPDATE
================================
{days_left} day(s) left
Team Members: {total}
Avg Score: {avg_score}/100
KPI Compliant: {compliant}/{total}

Top Performers: {top}
Needs Support: {needs_att}

Keep pushing team!
SparklingBlu Moto Fleet Team"""

    return msg
